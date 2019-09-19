import logging
import decimal
import copy
import requests
import re

from django.apps import apps
from django.http import HttpResponse
from django.db import transaction

from api_basebone.core import exceptions


from api_basebone.core import admin, const, gmeta

from django.contrib.auth import get_user_model
from rest_framework import permissions, viewsets

# from rest_framework.decorators import action

from api_basebone.drf.response import success_response
from api_basebone.drf.pagination import PageNumberPagination

from api_basebone.restful.const import CLIENT_END_SLUG


# from api_basebone.services.api_services import API_RUNNER_MAP

from rest_framework.exceptions import PermissionDenied

from api_basebone.restful.serializers import create_serializer_class
from api_basebone.restful.serializers import multiple_create_serializer_class
from api_basebone.restful import batch_actions
from api_basebone.restful.forms import get_form_class
from api_basebone.restful.relations import forward_relation_hand, reverse_relation_hand
from api_basebone.restful.funcs import find_func

from api_basebone.utils import meta
from api_basebone.utils.gmeta import get_gmeta_config_by_key
from api_basebone.utils.operators import build_filter_conditions2
from api_basebone.signals import post_bsm_create

from .user_pip import add_login_user_data

from api_basebone.models import Api
from api_basebone.models import Parameter
from api_basebone.models import Filter
from api_basebone.models import Field

from api_basebone.services import api_services

from . import api_param


log = logging.getLogger(__name__)


class FormMixin(object):
    """表单处理集合"""

    def get_create_form(self):
        """获取创建数据的验证表单"""
        return get_form_class(self.model, 'create', end=self.end_slug)

    def get_update_form(self):
        """获取更新数据的验证表单"""
        return get_form_class(self.model, 'update', end=self.end_slug)

    def get_partial_update_form(self):
        return get_form_class(self.model, 'update', end=self.end_slug)

    def get_custom_patch_form(self):
        return get_form_class(self.model, 'update', end=self.end_slug)

    def get_validate_form(self, action):
        """获取验证表单"""
        return getattr(self, 'get_{}_form'.format(action))()

    def get_bsm_model_admin(self):
        """获取 BSM Admin 模块"""
        return meta.get_bsm_model_admin(self.model)


class QuerySetMixin:
    """结果集处理集合"""

    def get_queryset_by_filter_user(self, queryset):
        """通过用户过滤对应的数据集

        - 如果用户是超级用户，则不做任何过滤
        - 如果用户是普通用户，则客户端筛选的模型有引用到了用户模型，则过滤对应的数据集
        """
        user = self.request.user
        if user and user.is_staff and user.is_superuser:
            return queryset

        # 检测模型中是否有字段引用了用户模型
        has_user_field = meta.get_related_model_field(self.model, get_user_model())
        if has_user_field:
            # 如果有，则读取模型中 GMeta 中的配置
            # FIXME: 注意，这里和管理端的处理逻辑暂时是不同的
            user_field_name = get_gmeta_config_by_key(
                self.model, gmeta.GMETA_CLIENT_USER_FIELD
            )
            filter_by_login_user = get_gmeta_config_by_key(
                self.model, gmeta.GMETA_CLIENT_FILTER_BY_LOGIN_USER
            )
            if user_field_name and filter_by_login_user:
                return queryset.filter(**{user_field_name: user})
        return queryset

    def get_queryset_by_order_by(self, queryset):
        """结果集支持排序"""
        fields = self.request.data.get(const.ORDER_BY_FIELDS)
        if isinstance(fields, list) and fields:
            return queryset.order_by(*fields)
        return queryset

    def get_queryset_by_filter_conditions(self, queryset):
        """
        用于检测客户端传入的过滤条件

        客户端传入的过滤条件的数据结构如下：

        [
            {
                field: xxxx,
                operator: xxxx,
                value: xxxx
            }
        ]
        """
        # 原先的写法是`if not queryset`，这样会引起queryset调用__bool__，并会触发fetch_all，导致请求变慢
        # if not queryset.exists():
        #     return queryset

        filter_conditions = self.request.data.get(const.FILTER_CONDITIONS)
        if filter_conditions:
            cons = build_filter_conditions2(filter_conditions)
            if cons:
                queryset = queryset.filter(cons)
        return queryset

    def get_queryset_by_exclude_conditions(self, queryset):
        """用于检测客户端传入的排除条件

        客户端传入的过滤条件的数据结构如下：

        [
            {
                field: xxxx,
                operator: xxxx,
                value: xxxx
            }
        ]
        """
        if not queryset.first():
            return queryset

        conditions = self.request.data.get(const.EXCLUDE_CONDITIONS)
        if conditions:
            cons = build_filter_conditions2(conditions)
            if cons:
                return queryset.exclude(cons)
        return queryset

    def get_queryset_by_with_tree(self, queryset):
        """如果是树形结构，则需要做对应的过滤"""
        if self.tree_data:
            params = {self.tree_data[0]: self.tree_data[2]}
            return queryset.filter(**params)
        return queryset

    def _get_queryset(self, queryset):
        methods = ['filter_user', 'filter_conditions', 'order_by', 'with_tree']
        for item in methods:
            queryset = getattr(self, f'get_queryset_by_{item}')(queryset)
        return queryset.distinct()


class GenericViewMixin:
    """重写 GenericAPIView 中的某些方法"""

    # def check_permissions(self, request):
    #     """校验权限"""
    #     action_skip = get_gmeta_config_by_key(
    #         self.model, gmeta.GMETA_CLIENT_API_PERMISSION_SKIP
    #     )
    #     if isinstance(action_skip, (tuple, list)) and self.action in action_skip:
    #         return True
    #     super().check_permissions(request)

    def perform_authentication(self, request):
        """
        - 处理展开字段
        - 处理树形数据
        - 给数据自动插入用户数据
        """
        result = super().perform_authentication(request)

        meta.load_custom_admin_module()
        self.get_expand_fields()
        self._get_data_with_tree(request)

        return result

    def get_expand_fields(self):
        """获取扩展字段并作为属性值赋予

        注意使用扩展字段 get 方法和 post 方法的区别

        get 方法使用 query string，这里需要解析
        post 方法直接放到 body 中
        """

        self.expand_fields = None
        if self.action in ['list']:
            fields = self.request.query_params.get(const.EXPAND_FIELDS)
            self.expand_fields = fields.split(',') if fields else None
        elif self.action in ['retrieve', 'set', 'func']:
            self.expand_fields = self.request.data.get(const.EXPAND_FIELDS)
            # 详情的展开字段和列表的展开字段分开处理
            if not self.expand_fields and self.action == 'retrieve':
                # 对于详情的展开，直接读取 admin 中的配置
                admin_class = self.get_bsm_model_admin()
                if admin_class:
                    try:
                        detail_expand_fields = getattr(
                            admin_class, admin.BSM_DETAIL_EXPAND_FIELDS, None
                        )
                        if detail_expand_fields:
                            self.expand_fields = copy.deepcopy(detail_expand_fields)
                    except Exception:
                        pass
        elif self.action in ['create', 'update', 'custom_patch', 'partial_update']:
            self.expand_fields = self.request.data.get('__expand_fields')

    def _get_data_with_tree(self, request):
        """检测是否可以设置树形结构"""
        self.tree_data = None

        data_with_tree = False
        # 检测客户端传进来的树形数据结构的参数
        if request.method.upper() == 'GET':
            data_with_tree = request.query_params.get(const.DATA_WITH_TREE, False)
        elif request.method.upper() == 'POST':
            data_with_tree = request.data.get(const.DATA_WITH_TREE, False)

        # 如果客户端传进来的参数为真，则通过 admin 配置校验，即 admin 中有没有配置
        if data_with_tree:
            admin_class = self.get_bsm_model_admin()
            if admin_class:
                try:
                    parent_field = getattr(admin_class, admin.BSM_PARENT_FIELD, None)
                    if parent_field:
                        # 获取父亲字段数据，包含字段名，related_name 和 默认值
                        # 这些数据在其他地方会用到
                        parent_field_data = meta.tree_parent_field(
                            self.model, parent_field
                        )
                        if parent_field_data:
                            self.tree_data = parent_field_data
                except Exception:
                    pass

    def translate_expand_fields(self, expand_fields):
        """转换展开字段"""
        for out_index, item in enumerate(expand_fields):
            field_list = item.split('.')
            model = self.model
            for index, value in enumerate(field_list):
                field = model._meta.get_field(value)
                if meta.check_field_is_reverse(field):
                    result = meta.get_relation_field_related_name(
                        field.related_model, field.remote_field.name
                    )
                    if result:
                        field_list[index] = result[0]
                if field.is_relation:
                    model = field.related_model
            expand_fields[out_index] = '.'.join(field_list)
        return expand_fields

    def get_queryset(self):
        """动态的计算结果集

        - 如果是展开字段，这里做好是否关联查询
        """
        managers = get_gmeta_config_by_key(self.model, gmeta.GMETA_MANAGERS)
        if managers and 'client_api' in managers:
            objects = getattr(self.model, managers['client_api'], self.model.objects)
        else:
            objects = self.model.objects
        expand_fields = self.expand_fields
        if not expand_fields:
            return self._get_queryset(objects.all())

        expand_fields = self.translate_expand_fields(expand_fields)
        field_list = [item.replace('.', '__') for item in expand_fields]
        return self._get_queryset(objects.all().prefetch_related(*field_list))

    def get_serializer_class(self, expand_fields=None):
        """动态的获取序列化类

        - 如果没有嵌套字段，则动态创建最简单的序列化类
        - 如果有嵌套字段，则动态创建引用字段的嵌套序列化类
        """
        # FIXME: 这里只有做是为了使用 django-rest-swagger，否则会报错，因为 swagger 还是很笨
        expand_fields = getattr(self, 'expand_fields', None)
        # FIXME: 这里设置了一个默认值，是为了避免 swagger 报错
        model = getattr(self, 'model', get_user_model())
        tree_data = getattr(self, 'tree_data', None)
        exclude_fields = self.request.data.get('exclude_fields')

        # 如果没有展开字段，则直接创建模型对应的序列化类
        if not expand_fields:
            return create_serializer_class(
                model,
                exclude_fields=exclude_fields,
                tree_structure=tree_data,
                action=self.action,
            )

        # 如果有展开字段，则创建嵌套的序列化类
        serializer_class = multiple_create_serializer_class(
            model,
            expand_fields,
            exclude_fields=exclude_fields,
            tree_structure=tree_data,
            action=self.action,
        )
        return serializer_class


class ApiViewSet(FormMixin, QuerySetMixin, GenericViewMixin, viewsets.ModelViewSet):
    """"""

    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPagination

    end_slug = CLIENT_END_SLUG

    def perform_create(self, serializer):
        return serializer.save()

    def perform_update(self, serializer):
        return serializer.save()

    def retrieve(self, request, *args, **kwargs):
        """获取数据详情"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(serializer.data)

    def filter_display_fields(self, request, data):
        display_fields = request.data.get(const.DISPLAY_FIELDS)
        if not display_fields:
            return data
        display_fields_set = set()
        for field_str in display_fields:
            items = field_str.split('.')
            for i in range(len(items)):
                display_fields_set.add('.'.join(items[:i+1]))

        results = []
        for record in data:
            display_record = self.filter_sub_display_fields(display_fields_set, record)
            results.append(display_record)

        return results

    def filter_sub_display_fields(self, display_fields_set, record, prefix=''):
        display_record = {}
        for k, v in record.items():
            if prefix:
                full_key = prefix + '.' + k
            else:
                full_key = k
            if isinstance(v, list):
                if full_key not in display_fields_set:
                    continue
                display_record[k] = []
                for d in v:
                    sub_record = self.filter_sub_display_fields(display_fields_set, d, full_key)
                    display_record[k].append(sub_record)
            elif isinstance(v, dict):
                if full_key not in display_fields_set:
                    continue
                display_record[k] = self.filter_sub_display_fields(display_fields_set, v, full_key)
            elif full_key in display_fields_set:
                display_record[k] = v
        return display_record

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            result = self.filter_display_fields(request, serializer.data)
            response = self.get_paginated_response(result)
            return success_response(response.data)

        serializer = self.get_serializer(queryset, many=True)
        result = self.filter_display_fields(request, serializer.data)
        return success_response(result)

    def delete_by_conditon(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        deleted, rows_count = queryset.delete()
        result = {'deleted': deleted, 'rows_count': rows_count}

        return success_response(result)

    def update_by_conditon(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        set_fields = self.request.data.get(const.SET_FIELDS)
        count = queryset.update(**set_fields)
        result = {'count': count}
        return success_response(result)

    def create(self, request, *args, **kwargs):
        """
        这里校验表单和序列化类分开创建

        原因：序列化类有可能嵌套
        """

        with transaction.atomic():
            add_login_user_data(self, request.data)
            forward_relation_hand(self.model, request.data)
            serializer = self.get_validate_form('create')(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance = self.perform_create(serializer)
            reverse_relation_hand(self.model, request.data, instance, detail=False)
            instance = self.get_queryset().get(id=instance.id)

            # with transaction.atomic():
            log.debug(
                'sending Post Save signal with: model: %s, instance: %s',
                self.model,
                instance,
            )
            post_bsm_create.send(sender=self.model, instance=instance, create=True)
            # 如果有联合查询，单个对象创建后并没有联合查询, 所以要多查一次？
            serializer = self.get_serializer(self.get_queryset().get(id=instance.id))
            return success_response(serializer.data)

    def update(self, request, *args, **kwargs):
        """全量更新数据"""
        with transaction.atomic():
            add_login_user_data(self, request.data)
            forward_relation_hand(self.model, request.data)

            partial = kwargs.pop('partial', False)
            instance = self.get_object()

            serializer = self.get_validate_form(self.action)(
                instance, data=request.data, partial=partial
            )
            serializer.is_valid(raise_exception=True)
            instance = self.perform_update(serializer)

            reverse_relation_hand(self.model, request.data, instance)
            instance = self.get_queryset().get(id=instance.id)

            # with transaction.atomic():
            log.debug(
                'sending Post Update signal with: model: %s, instance: %s',
                self.model,
                instance,
            )
            post_bsm_create.send(sender=self.model, instance=instance, create=False)

            serializer = self.get_serializer(self.get_queryset().get(id=instance.id))
            return success_response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """部分字段更新"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    # @action(methods=['put'], detail=True, url_path='patch')
    def custom_patch(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """删除数据"""
        instance = self.get_object()
        self.perform_destroy(instance)
        return success_response()

    # @action(methods=['POST'], detail=False, url_path='list')
    def set(self, request, app, model, **kwargs):
        """获取列表数据"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            return success_response(response.data)

        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)

    # @action(methods=['POST'], detail=False, url_path='batch')
    def batch(self, request, app, model, **kwargs):
        """
        ## 批量操作

        ```python
        {action: 动作, data: 主键的列表}
        ```
        """
        serializer = batch_actions.BatchActionForm(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        serializer.handle()
        return success_response()

    # @action(methods=['POST', 'GET'], detail=False, url_path='func')
    def func(self, request, app, model, func_name, params, **kwargs):
        """云函数, 由客户端直接调用的服务函数
        """
        func, options = find_func(app, model, func_name)
        if not func:
            raise exceptions.BusinessException(
                error_code=exceptions.FUNCTION_NOT_FOUNT,
                error_data=f'no such func: {func_name} found',
            )

        if options.get('login_required', False):
            if not request.user.is_authenticated:
                raise PermissionDenied()

        view_context = {'view': self}
        params['view_context'] = view_context

        result = func(request.user, **params)
        # TODO：考虑函数的返回结果类型。1. 实体，2.实体列表，3.字典，4.无返回，针对不同的结果给客户端反馈
        if isinstance(result, requests.Response):
            return HttpResponse(result, result.headers.get('Content-Type', None))
        if isinstance(result, (list, dict)):
            return success_response(result)
        if isinstance(result, self.model):
            serializer = self.get_serializer(result)
            return success_response(serializer.data)
        return success_response()

    def api(self, request, *args, **kwargs):
        slug = kwargs.get('pk')
        api = Api.objects.filter(slug=slug).first()
        if not api:
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data=f'没有\'{slug}\'这一api',
            )

        if request.method.lower() != api.method.lower():
            raise exceptions.BusinessException(
                error_code=exceptions.THIS_ACTION_IS_NOT_AUTHENTICATE,
                error_data=f'{request.method}此种请求不允许访问\"{slug}\"',
            )
        self.model = apps.all_models[api.app][api.model]
        self.action = self.API_ACTION_MAP.get(api.operation, '')
        api_runnser = self.API_RUNNER_MAP.get(api.operation)
        return api_runnser(self, request, api, *args, **kwargs)

    def get_config_parameters(self, api_id):
        return Parameter.objects.filter(api__id=api_id).all()

    def get_config_fields(self, api_id):
        return Field.objects.filter(api__id=api_id).all()

    def get_param_value(self, request, parameter):
        value = request.GET.get(parameter.name) or request.POST.get(parameter.name) or parameter.default
        if ((value is None) or (value == '')) and (parameter.required):
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data=f'{parameter.name}参数为必填',
            )
        if parameter.type == Parameter.TYPE_BOOLEAN:
            value = bool(value)
        elif parameter.type in (Parameter.TYPE_INT, Parameter.TYPE_PAGE_IDX, Parameter.TYPE_PAGE_SIZE):
            value = int(value)
        elif parameter.type == Parameter.TYPE_DECIMAL:
            value = decimal.Decimal(value)
        return value

    def get_pk_value(self, request, api_id):
        parameters = self.get_config_parameters(api_id)
        for p in parameters:
            if p.type == Parameter.TYPE_PK:
                id = self.get_param_value(request, p)
                if id:
                    return id
                else:
                    raise exceptions.BusinessException(
                        error_code=exceptions.PARAMETER_FORMAT_ERROR,
                        error_data=f'没有\'{p.name}\'这一pk参数',
                    )
        else:
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data='api没有配置pk参数',
            )

    def get_page_param(self, request, api_id):
        parameters = self.get_config_parameters(api_id)
        size = None
        page = None
        for p in parameters:
            if p.type == Parameter.TYPE_PAGE_SIZE:
                size = self.get_param_value(request, p)
                if not size:
                    raise exceptions.BusinessException(
                        error_code=exceptions.PARAMETER_FORMAT_ERROR,
                        error_data=f'没有\'{p.name}\'这一页长参数',
                    )
            elif p.type == Parameter.TYPE_PAGE_IDX:
                page = self.get_param_value(request, p)
                if not page:
                    raise exceptions.BusinessException(
                        error_code=exceptions.PARAMETER_FORMAT_ERROR,
                        error_data=f'没有\'{p.name}\'这一页码参数',
                    )

        return size, page

    def get_request_params(self, request, api_id):
        parameters = self.get_config_parameters(api_id)
        params = {}
        for p in parameters:
            if not p.is_special_defined():
                params[p.name] = self.get_param_value(request, p)
        return params

    def run_func_api(self, request, api, *args, **kwargs):
        parameters = self.get_config_parameters(api.id)
        params = {}
        for p in parameters:
            params[p.name] = self.get_param_value(request, p)
        return self.func(request, api.app, api.model, api.func_name, params, **kwargs)

    def run_create_api(self, request, api, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def run_update_api(self, request, api, *args, **kwargs):
        id = self.get_pk_value(request, api.id)
        kwargs[self.lookup_field] = id
        self.kwargs = kwargs
        
        return self.update(request, *args, **kwargs)

    def run_replace_api(self, request, api, *args, **kwargs):
        id = self.get_pk_value(request, api.id)
        kwargs[self.lookup_field] = id
        self.kwargs = kwargs
        
        return self.custom_patch(request, *args, **kwargs)

    def run_delete_api(self, request, api, *args, **kwargs):
        id = self.get_pk_value(request, api.id)
        kwargs[self.lookup_field] = id
        self.kwargs = kwargs
        
        return self.destroy(request, *args, **kwargs)

    def run_retrieve_api(self, request, api, *args, **kwargs):
        id = self.get_pk_value(request, api.id)
        kwargs[self.lookup_field] = id
        self.kwargs = kwargs
        
        return self.retrieve(request, *args, **kwargs)

    def put_params_into_filters(self, request, filters, params):
        for filter in filters:
            self.put_param_into_one_filter(request, filter, params)

    def put_param_into_one_filter(self, request, filter, params):
        # if ('children' in filter) and (filter['children']):
        if filter['type'] == Filter.TYPE_CONTAINER:
            children = filter['children']
            for child in children:
                self.put_param_into_one_filter(request, child, params)
        else:
            filter['value'] = self.replace_params(request, filter['value'], params)

    def replace_params(self, request, s, params):
        if '${' in s:
            pat = r'\${([\w\.-]+)}'
            ls = re.findall(pat, s)
            for k in ls:
                if k not in params:
                    raise exceptions.BusinessException(
                        error_code=exceptions.PARAMETER_FORMAT_ERROR,
                        error_data=f'filters设置的参数\'{k}\'为未定义参数',
                    )
                v = params[k]
                s = s.replace(f'${{{k}}}', f'{v}')
        
        if '#{' in s:
            pat = r'#{([\w\.-]+)}'
            ls = re.findall(pat, s)
            for k in ls:
                if k not in api_param.API_SERVER_PARAM:
                    raise exceptions.BusinessException(
                        error_code=exceptions.PARAMETER_FORMAT_ERROR,
                        error_data=f'服务端参数\'{k}\'为未定义参数',
                    )
                f = api_param.API_SERVER_PARAM[k]
                v = f(request)
                s = s.replace(f'#{{{k}}}', f'{v}')

        key_works = {'$$': '$', '{{': '}', '}}': '}', '##': '#'}
        for k, v in key_works.items():
            if k in s:
                s = s.replace(k, v)

        return s

    def get_config_expand_fields(self, fields):
        expand_fields = set()
        for field in fields:
            nest_fields = field.name.split('.')
            if len(nest_fields) > 1:
                expand = '.'.join(nest_fields[:-1])
                expand_fields.add(expand)
        return list(expand_fields)

    def run_list_api(self, request, api, *args, **kwargs):
        data = request.data
        if hasattr(data, '_mutable'):
            data._mutable = True
        data[const.ORDER_BY_FIELDS] = api.get_order_by_fields()
        
        params = self.get_request_params(request, api.id)
        
        filters = api_services.get_filters_json(api)
        self.put_params_into_filters(request, filters, params)
        data[const.FILTER_CONDITIONS] = filters

        fields = self.get_config_fields(api.id)
        self.expand_fields = self.get_config_expand_fields(fields)
        # data['exclude_fields'] = {f'{api.app}__{api.model}': ['id']}
        data[const.DISPLAY_FIELDS] = [f.name for f in fields]

        size, page = self.get_page_param(request, api.id)

        self.kwargs = {}
        if size:
            self.kwargs['size'] = size
        if page:
            self.kwargs['page'] = page

        request.query_params._mutable = True
        request.query_params.clear()
        request.query_params.update(self.kwargs)
        request.query_params._mutable = False
        if hasattr(data, '_mutable'):
            data._mutable = False

        return self.list(request, *args, **self.kwargs)

    def run_delete_by_condition_api(self, request, api, *args, **kwargs):
        data = request.data
        if hasattr(data, '_mutable'):
            data._mutable = True
        
        params = self.get_request_params(request, api.id)
        
        filters = api_services.get_filters_json(api)
        self.put_params_into_filters(request, filters, params)
        data[const.FILTER_CONDITIONS] = filters

        if hasattr(data, '_mutable'):
            data._mutable = False

        return self.delete_by_conditon(request, *args, **self.kwargs)

    def run_update_by_condition_api(self, request, api, *args, **kwargs):
        data = request.data
        if hasattr(data, '_mutable'):
            data._mutable = True
        
        params = self.get_request_params(request, api.id)

        fields = self.get_config_fields(api.id)
        if fields:
            data[const.SET_FIELDS] = {}
            for f in fields:
                data[const.SET_FIELDS][f.name] = self.replace_params(request, f.value, params)
        
        filters = api_services.get_filters_json(api)
        self.put_params_into_filters(request, filters, params)
        data[const.FILTER_CONDITIONS] = filters

        if hasattr(data, '_mutable'):
            data._mutable = False

        return self.update_by_conditon(request, *args, **self.kwargs)

    # 放在最后
    API_RUNNER_MAP = {
        Api.OPERATION_LIST: run_list_api,
        Api.OPERATION_RETRIEVE: run_retrieve_api,
        Api.OPERATION_CREATE: run_create_api,
        Api.OPERATION_UPDATE: run_update_api,
        Api.OPERATION_REPLACE: run_replace_api,
        Api.OPERATION_DELETE: run_delete_api,
        Api.OPERATION_UPDATE_BY_CONDITION: run_update_by_condition_api,
        Api.OPERATION_DELETE_BY_CONDITION: run_delete_by_condition_api,
        Api.OPERATION_FUNC: run_func_api,
    }
    
    API_ACTION_MAP = {
        Api.OPERATION_LIST: 'list',
        Api.OPERATION_RETRIEVE: 'retrieve',
        Api.OPERATION_CREATE: 'create',
        Api.OPERATION_UPDATE: 'update',
        Api.OPERATION_REPLACE: 'custom_patch',
        Api.OPERATION_DELETE: 'destroy',
        Api.OPERATION_UPDATE_BY_CONDITION: 'update_by_conditon',
        Api.OPERATION_DELETE_BY_CONDITION: 'delete_by_conditon',
        Api.OPERATION_FUNC: 'func',
    }
