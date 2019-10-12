import logging
import decimal
import copy
import re

from django.apps import apps
from rest_framework.viewsets import ModelViewSet

from api_basebone.core import exceptions


from api_basebone.core import admin, const, gmeta

from django.contrib.auth import get_user_model
from rest_framework import permissions

from api_basebone.drf.response import success_response
from api_basebone.drf.pagination import PageNumberPagination

from api_basebone.restful.const import CLIENT_END_SLUG

from api_basebone.restful.serializers import create_serializer_class
from api_basebone.restful.serializers import multiple_create_serializer_class

from api_basebone.utils import meta
from api_basebone.utils.gmeta import get_gmeta_config_by_key
from api_basebone.restful.mixins import FormMixin

# from api_basebone.restful.viewsets import BSMModelViewSet
from api_basebone.restful.client.views import QuerySetMixin

from api_basebone.models import Api
from api_basebone.models import Parameter
from api_basebone.models import Filter
from api_basebone.models import DisplayField
from api_basebone.models import SetField

from api_basebone.services import api_services
from api_basebone.services import rest_services

from . import api_param


log = logging.getLogger(__name__)


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


class ApiViewSet(FormMixin, QuerySetMixin, GenericViewMixin, ModelViewSet):
    """"""

    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPagination

    end_slug = CLIENT_END_SLUG

    def perform_create(self, serializer):
        return serializer.save()

    def perform_update(self, serializer):
        return serializer.save()

    def api(self, request, *args, **kwargs):
        slug = kwargs.get('pk')
        api = Api.objects.filter(slug=slug).first()
        if not api:
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data=f'没有\'{slug}\'这一api',
            )

        if not api.method_equal(request.method):
            raise exceptions.BusinessException(
                error_code=exceptions.THIS_ACTION_IS_NOT_AUTHENTICATE,
                error_data=f'{request.method}此种请求不允许访问\"{slug}\"',
            )
        self.model = apps.all_models[api.app][api.model]
        self.action = self.API_ACTION_MAP.get(api.operation, '')
        api_runnser = self.API_RUNNER_MAP.get(api.operation)
        return api_runnser(self, request, api, *args, **kwargs)

    def get_param_value(self, request, parameter):
        value = request.GET.get(parameter.name) or request.POST.get(parameter.name) or parameter.default
        if ((value is None) or (value == '')) and (parameter.required):
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data=f'{parameter.name}参数为必填',
            )
        if parameter.type == Parameter.TYPE_BOOLEAN:
            if isinstance(value, str):
                if value.lower() == 'true':
                    value = True
                elif value.lower() == 'false':
                    value = False
                else:
                    value = bool(eval(value))
            else:
                value = bool(eval(value))
        elif parameter.type in (Parameter.TYPE_INT, Parameter.TYPE_PAGE_IDX, Parameter.TYPE_PAGE_SIZE):
            value = int(value)
        elif parameter.type == Parameter.TYPE_DECIMAL:
            value = decimal.Decimal(value)
        return value

    def get_pk_value(self, request, api_id):
        parameters = api_services.get_config_parameters(api_id)
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
        """提取分页参数"""
        parameters = api_services.get_config_parameters(api_id)
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
        parameters = api_services.get_config_parameters(api_id)
        params = {}
        for p in parameters:
            if not p.is_special_defined():
                params[p.name] = self.get_param_value(request, p)
        return params

    def run_func_api(self, request, api, *args, **kwargs):
        """云函数api"""
        parameters = api_services.get_config_parameters(api.id)
        params = {}
        for p in parameters:
            params[p.name] = self.get_param_value(request, p)
        
        return rest_services.client_func(self, request.user, api.app, api.model, api.func_name, params)

    def filter_response_display(self, api_id, response):
        """过滤resonse的返回属性"""
        if 'result' in response.data:
            display_fields = api_services.get_config_display_fields(api_id)
            display_fields = [f.name for f in display_fields]
            result = rest_services.filter_display_fields(response.data['result'], display_fields)
            response = success_response(result)

        return response

    def make_set_data(self, request, api_id):
        """往request注入修改的参数和数据"""
        data = request.data
        if hasattr(data, '_mutable'):
            data._mutable = True
        params = self.get_request_params(request, api_id)
        set_fields = api_services.get_config_set_fields(api_id)
        new_data = {}
        for f in set_fields:
            new_data[f.name] = self.replace_params(request, f.value, params)
        data.clear()
        data.update(new_data)
        # if hasattr(data, '_mutable'):
        #     data._mutable = False

    def run_create_api(self, request, api, *args, **kwargs):
        """新建操作api"""
        self.make_set_data(request, api.id)
        response = rest_services.client_create(self, request)
        return self.filter_response_display(api.id, response)

    def run_update_api(self, request, api, *args, **kwargs):
        """更新操作api"""
        id = self.get_pk_value(request, api.id)
        kwargs[self.lookup_field] = id
        self.kwargs = kwargs
        self.make_set_data(request, api.id)
        
        response = rest_services.client_update(self, request, False)
        return self.filter_response_display(api.id, response)

    def run_replace_api(self, request, api, *args, **kwargs):
        """局部更新操作api"""
        id = self.get_pk_value(request, api.id)
        kwargs[self.lookup_field] = id
        self.kwargs = kwargs
        self.make_set_data(request, api.id)
        
        response = rest_services.client_update(self, request, True)
        return self.filter_response_display(api.id, response)

    def run_delete_api(self, request, api, *args, **kwargs):
        """删除操作api"""
        id = self.get_pk_value(request, api.id)
        kwargs[self.lookup_field] = id
        self.kwargs = kwargs
        
        return rest_services.destroy(self, request)

    def run_retrieve_api(self, request, api, *args, **kwargs):
        """查询详情操作api"""
        id = self.get_pk_value(request, api.id)
        kwargs[self.lookup_field] = id
        self.kwargs = kwargs

        fields = api_services.get_config_display_fields(api.id)
        self.expand_fields = self.get_config_expand_fields(fields)
        display_fields = [f.name for f in fields]
        
        return rest_services.retrieve(self, display_fields)

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
        """参数注入到列值或查询条件"""

        # 用户自定义参数的注入
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
        
        # 服务器定义参数的注入
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

        # 敏感字符双写
        key_works = {'$$': '$', '{{': '}', '}}': '}', '##': '#'}
        for k, v in key_works.items():
            if k in s:
                s = s.replace(k, v)

        return s

    def get_config_expand_fields(self, fields):
        """依据显示的列，展开属性"""
        expand_fields = set()
        for field in fields:
            nest_fields = field.name.split('.')
            if len(nest_fields) > 1:
                expand = '.'.join(nest_fields[:-1])
                expand_fields.add(expand)
        return list(expand_fields)

    def run_list_api(self, request, api, *args, **kwargs):
        """查询api"""
        data = request.data
        if hasattr(data, '_mutable'):
            data._mutable = True
        data[const.ORDER_BY_FIELDS] = api.get_order_by_fields()
        
        params = self.get_request_params(request, api.id)
        
        filters = api_services.get_filters_json(api)
        self.put_params_into_filters(request, filters, params)
        data[const.FILTER_CONDITIONS] = filters

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
        # if hasattr(data, '_mutable'):
        #     data._mutable = False

        fields = api_services.get_config_display_fields(api.id)
        self.expand_fields = self.get_config_expand_fields(fields)
        display_fields = [f.name for f in fields]
        return rest_services.display(self, display_fields)

    def run_delete_by_condition_api(self, request, api, *args, **kwargs):
        """按条件删除的api"""
        data = request.data
        if hasattr(data, '_mutable'):
            data._mutable = True
        
        params = self.get_request_params(request, api.id)
        
        filters = api_services.get_filters_json(api)
        self.put_params_into_filters(request, filters, params)
        data[const.FILTER_CONDITIONS] = filters

        # if hasattr(data, '_mutable'):
        #     data._mutable = False

        return rest_services.delete_by_conditon(self)

    def run_update_by_condition_api(self, request, api, *args, **kwargs):
        """按条件更新的api"""
        params = self.get_request_params(request, api.id)

        data = request.data
        if hasattr(data, '_mutable'):
            data._mutable = True
        
        filters = api_services.get_filters_json(api)
        self.put_params_into_filters(request, filters, params)
        data[const.FILTER_CONDITIONS] = filters

        # if hasattr(data, '_mutable'):
        #     data._mutable = False

        set_fields = api_services.get_config_set_fields(api.id)
        set_fields_map = {}
        for f in set_fields:
            set_fields_map[f.name] = self.replace_params(request, f.value, params)

        return rest_services.update_by_conditon(self, set_fields_map)

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
