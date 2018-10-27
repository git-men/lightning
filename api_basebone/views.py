import importlib

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework import permissions, viewsets
from rest_framework.decorators import action

from . import batch_actions

from .app.account.forms import UserCreateUpdateForm

from .core import admin, exceptions, const
from .core.const import (
    DISPLAY_FIELDS,
    EXPAND_FIELDS,
    FILTER_CONDITIONS,
    ORDER_BY_FIELDS,
)

from .drf.response import success_response
from .drf.pagination import PageNumberPagination

from .forms import create_form_class
from .serializers import (
    create_serializer_class,
    multiple_create_serializer_class
)

from .utils import meta, get_app
from .utils.operators import build_filter_conditions


class FormMixin(object):
    """表单处理集合"""

    def get_create_form(self):
        """获取创建数据的验证表单"""
        return create_form_class(self.model)

    def get_update_form(self):
        """获取更新数据的验证表单"""
        return create_form_class(self.model)

    def get_partial_update_form(self):
        return create_form_class(self.model)

    def get_validate_form(self, action):
        """获取验证表单"""
        return getattr(self, 'get_{}_form'.format(action))()


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

        has_user_field = meta.get_related_model_field(self.model, get_user_model())
        if has_user_field:
            module = importlib.import_module(f'{self.app_label}.admin')
            admin_class = getattr(module, f'{self.model.__name__}Admin', None)
            if admin_class:
                # 检测 admin 配置中是否指定了 auth_filter_field 属性
                try:
                    field_name = getattr(admin_class.GMeta, admin.GMETA_AUTH_FILTER_FIELD, None)
                    if field_name:
                        return queryset.filter(**{field_name: user})
                    else:
                        return queryset
                except Exception:
                    return queryset
            else:
                return queryset
        return queryset

    def get_queryset_by_order_by(self, queryset):
        """结果集支持排序"""
        fields = self.request.data.get(ORDER_BY_FIELDS)
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
        if not queryset:
            return queryset

        filter_conditions = self.request.data.get(FILTER_CONDITIONS)
        if filter_conditions:
            cons = build_filter_conditions(filter_conditions)
            if cons:
                return queryset.filter(cons)
            return queryset
        return queryset

    def get_queryset_by_with_tree(self, queryset):
        """如果是树形结构，则需要做对应的过滤"""
        if self.pass_meta_data_with_tree:
            params = {
                item[0]: item[2] for item in self.pass_meta_data_with_tree
            }
            return queryset.filter(**params)
        return queryset

    def _get_queryset(self, queryset):
        methods = ['filter_user', 'filter_conditions', 'order_by', 'with_tree']
        for item in methods:
            queryset = getattr(self, f'get_queryset_by_{item}')(queryset)
        return queryset


class GenericViewMixin:
    """重写 GenericAPIView 中的某些方法"""

    def perform_authentication(self, request):
        """
        截断，校验对应的 app 和 model 是否合法以及赋予当前对象对应的属性值
        """
        result = super().perform_authentication(request)
        self.app_label, self.model_slug = self.kwargs.get('app'), self.kwargs.get('model')

        if get_app(self.app_label) not in settings.INSTALLED_APPS:
            raise exceptions.BusinessException(
                error_code=exceptions.APP_LABEL_IS_INVALID
            )

        if self.model_slug not in apps.all_models[self.app_label]:
            raise exceptions.BusinessException(
                error_code=exceptions.MODEL_SLUG_IS_INVALID
            )

        try:
            self.model = apps.get_model(f'{self.app_label}.{self.model_slug}')
        except Exception:
            raise exceptions.BusinessException(
                error_code=exceptions.CANT_NOT_GET_MODEL
            )

        self.get_expand_fields()
        self._get_data_with_tree(request)
        return result

    def get_expand_fields(self):
        """获取扩展字段并作为属性值赋予

        注意使用扩展字段 get 方法和 post 方法的区别

        get 方法使用 query string，这里需要解析
        post 方法直接放到 body 中
        """
        if self.action in ['list', 'retrieve']:
            fields = self.request.query_params.get(EXPAND_FIELDS)
            self.expand_fields = fields.split(',') if fields else None
        else:
            self.expand_fields = self.request.data.get(EXPAND_FIELDS)

    def _get_data_with_tree(self, request):
        """检测是否可以设置树形结构"""

        self.pass_meta_data_with_tree = None

        data_with_tree = False
        # 检测客户端传进来的树形数据结构的参数
        if request.method.upper() == 'GET':
            data_with_tree = request.query_params.get(const.DATA_WITH_TREE, False)
        elif request.method.upper() == 'POST':
            data_with_tree = request.data.get(const.DATA_WITH_TREE, False)

        # 如果客户端传进来的参数为真，则通过 admin 配置校验，即 admin 中有没有配置
        if data_with_tree:
            module = importlib.import_module(f'{self.app_label}.admin')
            admin_class = getattr(module, f'{self.model.__name__}Admin', None)
            if admin_class:
                try:
                    parent_attr_map = getattr(admin_class.GMeta, admin.GMETA_PARENT_ATTR_MAP, None)
                    if parent_attr_map:
                        self.pass_meta_data_with_tree = parent_attr_map
                except Exception:
                    pass

    def get_queryset(self):
        """动态的计算结果集

        这里做好是否关联查询
        """

        expand_fields = self.expand_fields
        if not expand_fields:
            return self._get_queryset(
                self.model.objects.all()
            )

        field_list = [item.replace('.', '__') for item in expand_fields]
        return self._get_queryset(
            self.model.objects.all().prefetch_related(*field_list)
        )

    def get_serializer_class(self, expand_fields=None):
        """动态的获取序列化类

        - 如果没有嵌套字段，则动态创建最简单的序列化类
        - 如果有嵌套字段，则动态创建引用字段的嵌套序列化类
        """

        # 这里只有做是为了使用 django-rest-swagger
        expand_fields = getattr(self, 'expand_fields', None)
        model = getattr(self, 'model', get_user_model())
        pass_meta_data_with_tree = getattr(self, 'pass_meta_data_with_tree', None)

        if not expand_fields:
            return create_serializer_class(model, tree_structure=pass_meta_data_with_tree)

        return multiple_create_serializer_class(
            model, expand_fields, tree_structure=pass_meta_data_with_tree
        )


class CommonManageViewSet(FormMixin,
                          QuerySetMixin,
                          GenericViewMixin,
                          viewsets.ModelViewSet):
    """通用的管理接口视图"""
    permission_classes = (permissions.IsAuthenticated, )
    pagination_class = PageNumberPagination

    def perform_create(self, serializer):
        return serializer.save()

    def perform_update(self, serializer):
        return serializer.save()

    def retrieve(self, request, *args, **kwargs):
        """获取数据详情"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(serializer.data)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            return success_response(response.data)

        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)

    def _pre_many_to_many(self, field, key, value, update_data):
        """处理多对多关系"""
        # 如果多对多关系的字段的值不是列表，不做处理
        if not (isinstance(value, list) and value):
            return

        pure_data, object_data = [], []
        for item in value:
            object_data.append(item) if isinstance(item, dict) else pure_data.append(item)

        # 如果不包含对象数据，则不做任何处理
        if not object_data:
            return

        serializer = create_serializer_class(field.related_model)(data=object_data, many=True)
        serializer.is_valid(raise_exception=True)

        create_data = [field.related_model.objects.create(**item).id for item in object_data]
        update_data[key] = pure_data + create_data
        return update_data

    def _pre_one_to_many(self, field, key, value, update_data):
        """处理一对多关系"""
        if not isinstance(value, dict):
            return

        serializer = create_serializer_class(field.related_model)(data=value)
        serializer.is_valid(raise_exception=True)
        update_data[key] = field.related_model.objects.create(**value).id
        return update_data

    def _create_update_pre_hand(self, request, *args, **kwargs):
        """创建和更新的预处理

        例如文章和图片存在多对多，在新建文章时，对于图片，前端有可能会 push 以下数据
            - 包含对象的列表，[{字段：值，字段：值...}]
            - 包含 id 的列表
            - 包含 id 和对象的列表

        对于这种场景，需要检查客户端传进来的数据，同时需要做对应的预处理

        这里面包含两种关系
        - 一对多
        - 多不多

        TODO：暂时只支持多对多关系
        """
        if not (request.data and isinstance(request.data, dict)):
            return

        update_data = {}
        for key, value in request.data.items():
            field = meta.get_relation_field(self.model, key)
            if not field:
                continue
            print(field)

            if field.many_to_many:
                self._pre_many_to_many(field, key, value, update_data)
            else:
                self._pre_one_to_many(field, key, value, update_data)
        request.data.update(update_data)

    def create(self, request, *args, **kwargs):
        """
        这里校验表单和序列化类分开创建

        原因：序列化类有可能嵌套
        """

        self._create_update_pre_hand(request, *args, **kwargs)

        if self.model == get_user_model():
            serializer = UserCreateUpdateForm(data=request.data)
        else:
            serializer = self.get_validate_form(self.action)(data=request.data)
        serializer.is_valid(raise_exception=True)

        instance = self.perform_create(serializer)

        # 如果有联合查询，单个对象创建后并没有联合查询
        instance = self.get_queryset().filter(id=instance.id).first()
        serializer = self.get_serializer(instance)
        return success_response(serializer.data)

    def update(self, request, *args, **kwargs):
        """全量更新数据"""

        self._create_update_pre_hand(request, *args, **kwargs)

        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        if self.model == get_user_model():
            serializer = UserCreateUpdateForm(instance, data=request.data, partial=partial)
        else:
            serializer = self.get_validate_form(self.action)(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        instance = self.perform_update(serializer)
        serializer = self.get_serializer(instance)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}
        return success_response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """部分字段更新"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """删除数据"""
        instance = self.get_object()
        self.perform_destroy(instance)
        return success_response()

    @action(methods=['POST'], detail=False, url_path='list')
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

    @action(methods=['POST'], detail=False, url_path='batch')
    def batch(self, request, app, model, **kwargs):
        """
        ## 批量操作

        ```python
        这里可以执行各种操作，数据格式如下：

        {
            action: xxxx,
            source: 具体的数据结构有对应的 action 决定
        }

        业务流程
            - 根据 action 获取对应的表单，然后做对应的验证
            - 执行对应的 action

        批量删除的数据格式如下：

        {
            action: 'delete',
            source: {
                key: 'id', # 因为主键不一定是 id，也有肯能是其他
                data: 主键的列表
            }
        }
        ```
        """
        action = request.data.get('action', 'delete')
        if not action:
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data='缺少对应的 action'
            )

        action = action.lower()
        form_class = getattr(batch_actions, f'{action}Form', None)
        if not form_class:
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data='传入的 action 不支持'
            )

        serializer = form_class(data=request.data.get('source'), context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)

        serializer.handle()
        return success_response()
