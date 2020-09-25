import copy
import json
import logging

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework import permissions
from rest_framework.decorators import action

from api_basebone.core import admin, exceptions, const, gmeta

from api_basebone.drf.response import success_response
from api_basebone.drf.pagination import PageNumberPagination

from api_basebone.restful import batch_actions
from api_basebone.restful.const import CLIENT_END_SLUG
from api_basebone.restful.mixins import FormMixin
from api_basebone.restful.serializers import (
    create_serializer_class,
    multiple_create_serializer_class,
)

from api_basebone.utils import meta
from api_basebone.utils import queryset as queryset_utils
from api_basebone.utils.gmeta import get_gmeta_config_by_key
from api_basebone.utils.operators import build_filter_conditions2

from api_basebone.restful.viewsets import BSMModelViewSet
from api_basebone.services import rest_services

log = logging.getLogger(__name__)

exposed_apis = {}


def register_api(app, exposed_data):
    for model, data in exposed_data.items():
        exposed_apis[f'{app}__{model}'] = data


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

    def check_permissions(self, request):
        """校验权限"""
        if not hasattr(self, 'model'):
            return False

        action_skip = get_gmeta_config_by_key(
            self.model, gmeta.GMETA_CLIENT_API_PERMISSION_SKIP
        )
        if isinstance(action_skip, (tuple, list)) and self.action in action_skip:
            return True
        super().check_permissions(request)

    def perform_authentication(self, request):
        """
        截断，校验对应的 app 和 model 是否合法以及赋予当前对象对应的属性值

        - 检验 app 和 model 是否合法
        - 加载 admin 模块
        - 记录模型对象
        - 处理展开字段
        - 处理树形数据
        - 给数据自动插入用户数据
        """
        result = super().perform_authentication(request)
        self.app_label, self.model_slug = self.kwargs.get('app'), self.kwargs.get('model')

        # 检测模型是否合法
        try:
            self.model = apps.get_model(self.app_label, self.model_slug)
        except LookupError:
            raise exceptions.BusinessException(
                error_code=exceptions.MODEL_SLUG_IS_INVALID
            )

        # 检测方法是否允许访问
        model_str = f'{self.app_label}__{self.model_slug}'
        expose = exposed_apis.get(model_str, None)
        real_action = self.action
        if self.action == 'set':
            real_action = 'list'
        if (
            not expose
            or not expose.get('actions', None)
            or real_action not in expose['actions']
        ):
            raise exceptions.BusinessException(
                error_code=exceptions.THIS_ACTION_IS_NOT_AUTHENTICATE
            )

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

    def get_display_fields(self):
        return self.request.data.get(const.DISPLAY_FIELDS)

    def get_queryset(self):
        """动态的计算结果集

        - 如果是展开字段，这里做好是否关联查询
        """
        managers = get_gmeta_config_by_key(self.model, gmeta.GMETA_MANAGERS)
        if managers and 'client_api' in managers:
            objects = getattr(self.model, managers['client_api'], self.model.objects)
        else:
            objects = self.model.objects

        queryset = objects.all()

        expand_fields = self.expand_fields
        if expand_fields:
            expand_fields = self.translate_expand_fields(expand_fields)
            field_list = [item.replace('.', '__') for item in expand_fields]
            queryset = queryset.prefetch_related(*field_list)

        filter_fields = set()

        def add_filter_fields(cons):
            for con in cons:
                if 'field' in con:
                    filter_fields.add(con['field'])
                if 'children' in con:
                    add_filter_fields(con['children'])

        add_filter_fields(self.request.data.get(const.FILTER_CONDITIONS, []))
        queryset = queryset_utils.annotate(
            queryset, filter_fields, context={'user': self.request.user}
        )

        return self._get_queryset(queryset)

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
            display_fields=self.get_display_fields(),
        )
        return serializer_class


class CommonManageViewSet(FormMixin, QuerySetMixin, GenericViewMixin, BSMModelViewSet):
    """通用的管理接口视图
    list,set,retrieve,destroy的实现提到父类BSMModelViewSet
    """

    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPagination

    end_slug = CLIENT_END_SLUG

    def create(self, request, *args, **kwargs):
        """
        这里校验表单和序列化类分开创建

        原因：序列化类有可能嵌套
        """
        return rest_services.client_create(self, request, request.data)

    def update(self, request, *args, **kwargs):
        """全量更新数据"""
        # partial = kwargs.pop('partial', False)
        return rest_services.client_update(self, request, False, request.data)

    def partial_update(self, request, *args, **kwargs):
        """部分字段更新"""
        # kwargs['partial'] = True
        return rest_services.client_update(self, request, True, request.data)

    @action(methods=['put'], detail=True, url_path='patch')
    def custom_patch(self, request, *args, **kwargs):
        # kwargs['partial'] = True
        return rest_services.client_update(self, request, True, request.data)

    @action(methods=['POST'], detail=False, url_path='batch')
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

    @action(methods=['POST', 'GET'], detail=False, url_path='func')
    def func(self, request, app, model, **kwargs):
        """云函数, 由客户端直接调用的服务函数
        """
        data = request.data
        func_name = data.get('func_name', None) or request.GET.get('func_name', None)
        params = data.get('params', {}) or json.loads(request.GET.get('params', '{}'))
        return rest_services.client_func(
            self, request.user, app, model, func_name, params
        )

