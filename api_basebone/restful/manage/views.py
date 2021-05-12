import copy
import json
import logging

from django.apps import apps

from django.contrib.auth import get_user_model
from django.conf import settings as django_settings
from rest_framework.decorators import action

from api_basebone.settings import settings
from api_basebone.core import admin, const, exceptions, gmeta
from api_basebone.drf.pagination import PageNumberPagination
from api_basebone.drf.permissions import IsAdminUser
from api_basebone.drf.response import success_response
from api_basebone.restful.export.excel import export_excel, import_excel

# from api_basebone.export.fields import get_attr_in_gmeta_class
from api_basebone.restful import batch_actions, renderers, renderers_v2
from api_basebone.restful.const import MANAGE_END_SLUG
from api_basebone.restful.mixins import (
    CheckValidateMixin,
    GroupStatisticsMixin,
    StatisticsMixin,
)
from api_basebone.restful.serializers import (
    create_serializer_class,
    get_export_serializer_class,
    multiple_create_serializer_class,
    sort_expand_fields,
)

from api_basebone.utils import meta, module as basebone_module
from api_basebone.utils.data import get_prefetch_fields_from_export_fields
from api_basebone.utils.operators import build_filter_conditions2
from api_basebone.restful.mixins import FormMixin
from api_basebone.restful.viewsets import BSMModelViewSet

from api_basebone.services import rest_services
from api_basebone.utils import queryset as queryset_utils
from api_basebone.services import queryset as queryset_service

from .user_pip import add_login_user_data


log = logging.getLogger(__name__)


class QuerySetMixin:
    """结果集处理集合"""

    def get_basebone_admin(self):
        """获取 basebone 的管理类"""
        pass

    def basebone_get_model_role_config(self):
        """获取角色配置"""
        if self.model_role_config is not None:
            return self.model_role_config

        role_config = getattr(
            basebone_module.get_bsm_global_module(
                basebone_module.BSM_GLOBAL_MODULE_ROLES
            ),
            basebone_module.BSM_GLOBAL_ROLES,
            None,
        )

        key_prefix = f'{self.app_label}__{self.model_slug}'
        if isinstance(role_config, dict):
            self.model_role_config = role_config.get(key_prefix)
        return self.model_role_config

    def get_queryset_by_filter_user(self, queryset):
        """通过用户过滤对应的数据集

        - 如果用户是超级用户，则不做任何过滤
        - 如果用户是普通用户，则客户端筛选的模型有引用到了用户模型，则过滤对应的数据集

        FIXME: 这里先根据模型角色配置做出对应的响应

        TODO: 当前一个用户只能属于一个用户组，如果用户没有属于任何组，则暂时不做任何处理
        """
        user = self.request.user
        if user and user.is_staff and user.is_superuser:
            return queryset

        role_config = self.basebone_get_model_role_config()
        if role_config:
            # 如果
            config_key = basebone_module.BSM_GLOBAL_ROLE_USE_ADMIN_FILTER_BY_LOGIN_USER
            if role_config.get(config_key):
                return queryset

        # 检测模型中是否有字段引用了用户模型
        has_user_field = meta.get_related_model_field(self.model, get_user_model())
        if has_user_field:
            admin_class = self.get_bsm_model_admin()
            if admin_class:
                # 检测 admin 配置中是否指定了 auth_filter_field 属性
                try:
                    field_name = getattr(admin_class, admin.BSM_AUTH_FILTER_FIELD, None)
                    filter_by_login_user = getattr(
                        admin_class, admin.BSM_FILTER_BY_LOGIN_USER, False
                    )

                    if field_name and filter_by_login_user:
                        return queryset.filter(**{field_name: user})
                except Exception:
                    pass
        return queryset

    def get_queryset_by_order_by(self, queryset):
        """结果集支持排序"""
        fields = self.request.data.get(const.ORDER_BY_FIELDS)
        if isinstance(fields, list) and fields:
            return queryset.order_by(*fields)
        return queryset

    def get_user_role_filters(self):
        """获取此用户权限对应的过滤条件"""

        user = self.request.user
        if user and user.is_staff and user.is_superuser:
            return []

        role_config = self.basebone_get_model_role_config()
        if role_config and isinstance(role_config, dict):
            return role_config.get('filters')

    def get_queryset_by_filter_conditions(self, queryset):
        """
        用于检测客户端传入的过滤条件

        这里面的各种过滤条件的权重

        - 角色配置的过滤条件 高
        - admin 配置的默认的过滤条件 中
        - 客户端传进来的过滤条件 低

        客户端传入的过滤条件的数据结构如下：

        [
            {
                field: xxxx,
                operator: xxxx,
                value: xxxx
            }
        ]
        """
        # 原先的写法是`if not queryset or self.action in ['create']`，这样会引起queryset调用__bool__，并会触发fetch_all，导致请求变慢
        if self.action in ['create']:
            return queryset

        role_filters = self.get_user_role_filters()
        filter_conditions = self.request.data.get(const.FILTER_CONDITIONS, [])
        # FIXME: 如果是更新业务，则客户端无需传入过滤条件，为什么不像 create 直接返回呢
        # 因为更新操作是需要一定的权限，比如 A 创建的数据， B 是否有权限进行更新呢，都需要
        # 考量
        if self.action in ['update', 'partial_update', 'custom_patch']:
            filter_conditions = []

        admin_class = self.get_bsm_model_admin()
        if admin_class:
            default_filter = getattr(admin_class, admin.BSM_DEFAULT_FILTER, None)
            default_filter = default_filter
            if default_filter:
                filter_conditions += default_filter

        if role_filters:
            filter_conditions += role_filters

        # 这里做个动作 1 校验过滤条件中的字段，是否需要对结果集去重 2 组装过滤条件
        if filter_conditions:
            # TODO: 这里没有做任何的检测，需要加上检测
            fields = set()

            def tree_check(cond):
                for c in cond:
                    if 'children' in c:
                        tree_check(c['children'])
                    else:
                        fields.add(c['field'])

            tree_check(filter_conditions)
            self.basebone_check_distinct_queryset(list(fields))
            cons = build_filter_conditions2(
                filter_conditions, context={'user': self.request.user}
            )

            if cons:
                queryset = queryset.filter(cons)
            return queryset
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

        self.basebone_origin_queryset = queryset

        # 权限中配置是否去重
        role_config = self.basebone_get_model_role_config()
        log.debug(f'role_config: {role_config}')
        role_distict = False
        if role_config and isinstance(role_config, dict):
            role_distict = role_config.get(
                basebone_module.BSM_GLOBAL_ROLE_QS_DISTINCT, False
            )
        if self.basebone_distinct_queryset or role_distict:
            log.debug(
                f'basebone distinct queryset or role_distinct: {self.basebone_distinct_queryset}, {role_distict}'
            )
            return queryset.distinct()
        return queryset


class GenericViewMixin:
    """重写 GenericAPIView 中的某些方法"""

    def check_app_model(self, request):
        # 是否对结果集进行去重
        self.basebone_distinct_queryset = False

        # 模型角色配置
        self.model_role_config = None

        self.app_label, self.model_slug = self.kwargs.get('app'), self.kwargs.get('model')

        try:
            self.model = apps.get_model(self.app_label, self.model_slug)
        except LookupError:
            raise exceptions.BusinessException(
                error_code=exceptions.MODEL_SLUG_IS_INVALID
            )

        # 加载 admin 配置
        meta.load_custom_admin_module()

        if self.action == 'export_file':
            admin_class = self.get_bsm_model_admin()
            self._export_type_config = None
            if admin_class:
                exportable = getattr(admin_class, admin.BSM_EXPORTABLE, False)
                if exportable:
                    exportable_map = {item['key']: item for item in exportable}
                    file_type = self.request.query_params.get('fileformat')
                    if file_type in exportable_map:
                        valid_item = exportable_map[file_type]
                    else:
                        valid_item = [item for item in exportable if item['default']][0]

                    self._export_type_config = valid_item

                    if request.method.lower() == 'get':
                        if 'basebone_export_config' in list(dict(request.query_params)):
                            try:
                                basebone_export_config = json.loads(
                                    request.query_params.get('basebone_export_config')
                                )
                            except Exception:
                                basebone_export_config = None
                            self._export_type_config = basebone_export_config
                    elif request.method.lower() == 'post':
                        if 'basebone_export_config' in request.data:
                            basebone_export_config = request.data.get(
                                'basebone_export_config'
                            )
                            if not isinstance(basebone_export_config, dict):
                                basebone_export_config = None
                            self._export_type_config = basebone_export_config

                    if not self._export_type_config:
                        raise exceptions.BusinessException(
                            error_code=exceptions.MODEL_EXPORT_IS_NOT_SUPPORT
                        )

                    # FIXME: 如果不是新版导出，则重置 app_label 和 model_slug
                    if self._export_type_config.get('version') != 'v2':
                        self.app_label = self._export_type_config['app_label']
                        self.model_slug = self._export_type_config['model_slug']

                        # 检测模型是否合法
                        try:
                            self.model = apps.get_model(self.app_label, self.model_slug)
                        except LookupError:
                            raise exceptions.BusinessException(
                                error_code=exceptions.MODEL_SLUG_IS_INVALID
                            )
                else:
                    if request.method.lower() == 'get':
                        if 'basebone_export_config' in list(dict(request.query_params)):
                            try:
                                basebone_export_config = json.loads(
                                    request.query_params.get('basebone_export_config')
                                )
                            except Exception:
                                basebone_export_config = None
                            self._export_type_config = basebone_export_config
                    elif request.method.lower() == 'post':
                        if 'basebone_export_config' in request.data:
                            basebone_export_config = request.data.get(
                                'basebone_export_config'
                            )
                            if not isinstance(basebone_export_config, dict):
                                basebone_export_config = None
                            self._export_type_config = basebone_export_config
                    if not self._export_type_config:
                        raise exceptions.BusinessException(
                            error_code=exceptions.MODEL_EXPORT_IS_NOT_SUPPORT
                        )
            else:
                if request.method.lower() == 'get':
                    if 'basebone_export_config' in list(dict(request.query_params)):
                        try:
                            basebone_export_config = json.loads(
                                request.query_params.get('basebone_export_config')
                            )
                        except Exception:
                            basebone_export_config = None
                        self._export_type_config = basebone_export_config
                elif request.method.lower() == 'post':
                    if 'basebone_export_config' in request.data:
                        basebone_export_config = request.data.get(
                            'basebone_export_config'
                        )
                        if not isinstance(basebone_export_config, dict):
                            basebone_export_config = None
                        self._export_type_config = basebone_export_config
                if not self._export_type_config:
                    raise exceptions.BusinessException(
                        error_code=exceptions.MODEL_EXPORT_IS_NOT_SUPPORT
                    )

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

        self.check_app_model(request)
        self.validate_call_api_permission(request)
        self.get_expand_fields()
        self._get_data_with_tree(request)

        add_login_user_data(self, request.data)
        return result

    def validate_call_api_permission(self, request):
        """校验是否具有调用指定接口的权限

        例如管理人员调用商品的列表接口，如果开启了使用接口校验，则需要校验此

        用户是否具有调用此接口的权限，如果没有对应的权限，则就抛出没有权限

        注意：如果是云函数，则另做处理
        """
        if not settings.MANAGE_API_PERMISSION_VALIDATE_ENABLE:
            return

        # if self.action == 'func':
        #     func_name = request.data.get('func_name', None) or request.GET.get(
        #         'func_name', None
        #     )
        #     perm_list = [f'basebone_api_model_func_{func_name}']
        # else:
        #     perm_map = {
        #         'create': ['create'],
        #         'list': ['list'],
        #         'set': ['set'],
        #         'destroy': ['retrieve', 'destroy'],
        #         'update': ['retrieve', 'update'],
        #         'partial_update': ['retrieve', 'partial_update'],
        #         'custom_patch': ['retrieve', 'custom_patch'],
        #         'update_sort': ['retrieve', 'update_sort'],
        #         'batch': ['retrieve', 'batch'],
        #         'export_file': ['export_file'],
        #     }

        #     perm_list = [
        #         f'basebone_api_model_{item}' for item in perm_map.get(self.action)
        #     ]
        # check = request.user.has_perms(perm_list)
        # if not check:
        #     raise exceptions.BusinessException(error_code=exceptions.REQUEST_FORBIDDEN)

        # TODO: 暂时提供测试而已，后面会改掉
        perm_map = {
            'retrieve': ['view'],
            'create': ['add'],
            'list': ['view'],
            'update': ['view', 'change'],
            'partial_update': ['view', 'change'],
            'destroy': ['view', 'delete'],
        }
        perm_list = [
            f'{item}_{self.model_slug}' for item in perm_map.get(self.action, [])
        ]

        if perm_list:
            check = request.user.has_perms(perm_list)
            if not check:
                raise exceptions.BusinessException(
                    error_code=exceptions.REQUEST_FORBIDDEN
                )

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
        elif self.action in ['retrieve', 'set']:
            self.expand_fields = self.request.data.get(const.EXPAND_FIELDS)
            # 详情的展开字段和列表的展开字段分开处理
            if self.expand_fields is None and self.action == 'retrieve':
                # 对于详情的展开，直接读取 admin 中的配置
                admin_class = self.get_bsm_model_admin()
                if admin_class:
                    try:
                        detail_expand_fields = getattr(
                            admin_class, admin.BSM_DETAIL_EXPAND_FIELDS, None
                        )
                        detail_expand_fields = copy.deepcopy(detail_expand_fields)
                        if detail_expand_fields:
                            self.expand_fields = detail_expand_fields
                    except Exception:
                        pass
        elif self.action == 'export_file':
            # FIXME: 如果不是新版导出，则直接从导出配置中识别出扩展字段
            export_version = self._export_type_config.get('version', None)
            if export_version == 'v2':
                # 这里需要根据导出的字段自动识别出需要扩展的字段
                self.expand_fields = get_prefetch_fields_from_export_fields(
                    self.model, self._export_type_config['fields']
                )
            elif export_version == 'v3':
                self.expand_fields = get_prefetch_fields_from_export_fields(
                    self.model, [mp['field'] for mp in self._export_type_config['list_mapping']]
                )
            else:
                self.expand_fields = copy.deepcopy(
                    renderers.get_export_config_by_key(
                        self.model,
                        gmeta.GMETA_MANAGE_EXPORT_EXPAND_FIELDS,
                        self._export_type_config,
                    )
                )
                

    def _get_data_with_tree(self, request):
        """检测是否可以设置树形结构"""
        if isinstance(request.data, list):
            return
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
        """新版get_queryset方法，把组装queryset的方法全移出view之外，不与view绑定。
        """
        if getattr(django_settings, 'QUERYSET_VERSION', 'v1') == 'v2':
            log.debug('USING QUERYSET VERSION 2')
            return queryset_service.queryset(self.request, self.model, self.action, 
                filters=self.request.data.get(const.FILTER_CONDITIONS, []),
                fields=self.get_display_fields(),
                expand_fields=self.expand_fields,
                order=self.request.data.get(const.ORDER_BY_FIELDS),
                tree_data=self.tree_data,
                skip_distinct=self.action == 'statistics',
                view=self.request.data.get('view', None)
            )
        return self.get_queryset_legacy()

    def get_queryset_legacy(self):
        """动态的计算结果集

        - 如果是展开字段，这里做好是否关联查询
        - 如果 bsm admin 定义了 get_queryset 方法，贼继续使用 get_queryset 进行处理
        """
        admin_get_queryset = None
        admin_class = self.get_bsm_model_admin()
        if admin_class:
            admin_get_queryset = getattr(admin_class(), 'get_queryset', None)

        queryset = self.model.objects.all()

        context = {'user': self.request.user}

        expand_fields = self.expand_fields
        if expand_fields:
            expand_fields = self.translate_expand_fields(expand_fields)
            expand_dict = sort_expand_fields(expand_fields)
            display_fields = self.get_display_fields()
            queryset = queryset_utils.queryset_prefetch(queryset, expand_dict, context, display_fields=display_fields)
        if self.action not in ['get_chart', 'group_statistics']:
            queryset = queryset_utils.annotate(queryset, context=context)

        if hasattr(self.model, 'GMeta'):
            try:
                gm = self.model.GMeta()
            except Exception as e:
                log.error(str(e))
            else:
                if hasattr(gm, 'get_queryset'):
                    gmeta_get_queryset = gm.get_queryset
                    if gmeta_get_queryset is not None:
                        queryset = gmeta_get_queryset(queryset, self.request, self)

        queryset = self._get_queryset(queryset)

        if admin_get_queryset:
            queryset = admin_get_queryset(queryset, self.request, self)

        # 如果开启了 guardian 数据权限检测，那么这里会进行必要的筛选
        if settings.MANAGE_GUARDIAN_DATA_PERMISSION_CHECK:
            # 如果不是超级用户，则进行对应的数据筛选
            # FIXME: 目前只做查询类
            app_models = settings.MANAGE_GUARDIAN_DATA_APP_MODELS
            check_model = (
                isinstance(app_models, (list, set))
                and f'{self.app_label}__{self.model_slug}' in app_models
            )
            check_not_is_superuser = not self.request.user.is_superuser
            check_action = self.action in ['retrieve', 'list', 'set']

            if check_not_is_superuser and check_action and check_model:
                from guardian.ctypes import get_content_type
                from guardian.models import UserObjectPermission, GroupObjectPermission
                from django.contrib.auth.models import Permission

                content_type = get_content_type(self.model)
                permission = Permission.objects.filter(
                    codename=f'view_{self.model_slug}', content_type=content_type
                ).first()

                content_object_set = set()

                # 如果存在对应的权限
                if permission:
                    permission_object_list = UserObjectPermission.objects.filter(
                        user=self.request.user, permission=permission
                    ).values('object_pk')
                    for item in permission_object_list:
                        content_object_set.add(item['object_pk'])

                user_groups = self.request.user.groups.all()
                if user_groups:
                    group_object_list = GroupObjectPermission.objects.filter(
                        permission=permission, group__in=user_groups
                    ).values('object_pk')
                    for item in group_object_list:
                        content_object_set.add(item['object_pk'])

                if content_object_set:
                    queryset = queryset.filter(id__in=content_object_set)
        return queryset

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

        # 如果没有展开字段，则直接创建模型对应的序列化类
        if not expand_fields:
            serializer_class = create_serializer_class(
                model,
                tree_structure=tree_data,
                action=self.action,
                end_slug=self.end_slug,
            )
        else:
            # 如果有展开字段，则创建嵌套的序列化类
            serializer_class = multiple_create_serializer_class(
                model,
                expand_fields,
                tree_structure=tree_data,
                action=self.action,
                end_slug=self.end_slug,
                display_fields=self.get_display_fields(),
            )
        return serializer_class


class CommonManageViewSet(
    FormMixin,
    CheckValidateMixin,
    GroupStatisticsMixin,
    QuerySetMixin,
    GenericViewMixin,
    StatisticsMixin,
    BSMModelViewSet,
):
    """通用的管理接口视图
    list,set,retrieve,destroy的实现提到父类BSMModelViewSet
    """

    permission_classes = (IsAdminUser,)
    pagination_class = PageNumberPagination

    end_slug = MANAGE_END_SLUG

    def create(self, request, *args, **kwargs):
        """
        这里校验表单和序列化类分开创建

        原因：序列化类有可能嵌套
        """
        return rest_services.manage_create(self, request, request.data)

    def update(self, request, *args, **kwargs):
        """全量更新数据"""
        return rest_services.manage_update(self, request, False, request.data)
    
    def destroy(self, request, *args, **kwargs):
        """删除数据"""
        return rest_services.destroy(self, request, scope='admin')

    def partial_update(self, request, *args, **kwargs):
        """部分字段更新"""
        return rest_services.manage_update(self, request, True, request.data)

    @action(methods=['put'], detail=True, url_path='patch')
    def custom_patch(self, request, *args, **kwargs):
        return rest_services.manage_update(self, request, True, request.data)

    @action(methods=['POST', 'GET'], detail=False, url_path='update_sort')
    def update_sort(self, request, *args, **kwargs):
        return rest_services.update_sort(self, request, request.data)

    @action(methods=['POST'], detail=False, url_path='batch')
    def batch(self, request, app, model, **kwargs):
        """
        ## 批量操作

        ```python
        {
            action: 动作,
            data: 主键的列表,
            payload: 其他参数。
        }
        ```
        """
        serializer = batch_actions.BatchActionForm(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        serializer.handle()
        return success_response()

    @action(methods=['POST'], detail=False, url_path='import/file')
    def import_file(self, request, *args, **kwargs):
        """导入文件
        参数：
        1. detail_id
        2. detail_model
        3. import_config
        4. file（文件）
        4. model
        """
        print(request.data)
        config = json.loads(request.data['import_config'])
        content = request.data['file'].read()
        detail_id = request.data.get('detail_id', None)
        detail_model = request.data.get('detail_model', None)
        detail_field = request.data.get('detail_field', None)    
        
        detail_obj = None
        if detail_id:
            dm = apps.get_model(*detail_model.split('__'))
            detail_obj = queryset_service.queryset(request, dm).get(pk=detail_id)
            if not detail_obj:
                raise exceptions.BusinessException(error_message='找不到对象')

        if detail_obj:
            detail_filter = {detail_field: detail_obj}
            queryset = queryset_service.queryset(request, self.model).filter(**detail_filter)
        else:
            queryset = queryset_service.queryset(request, self.model)
        
        if config['file_type'] == 'excel':
            return import_excel(config, content, queryset, request, detail_obj)
        else:
            return import_excel(config, content, queryset, request, detail_obj)
    

    @action(methods=['get', 'post'], detail=False, url_path='export/file')
    def export_file(self, request, *args, **kwargs):
        """输出 excel 和 excel 文件

        ```
        Params:
            fileformat string csv | excel 形式使用 querystring 的形式
        ```
        """
        # 检测是否支持导出
        admin_class = self.get_bsm_model_admin()

        if not self._export_type_config:
            raise exceptions.BusinessException(
                error_code=exceptions.MODEL_EXPORT_IS_NOT_SUPPORT
            )

        export_version = self._export_type_config.get('version')
        if export_version == 'v2': 
            file_type = self._export_type_config['file_type']
            file_type = file_type if file_type in ('csv', 'excel') else 'csv'

            queryset = self.filter_queryset(self.get_queryset())
            serializer_class = get_export_serializer_class(
                self.model, self.get_serializer_class(), version=export_version
            )

            return renderers_v2.render(
                self.model,
                queryset,
                serializer_class,
                export_config=self._export_type_config,
                file_type=file_type
            )
        
        if export_version == 'v3':  # 第三版，优先导出Excel，支持指定模板
            detail_model = request.data.get('detail_model', None)
            detail_id = request.data.get('detail_id', None)
            
            detail_obj = None
            if detail_id and detail_model:
                dmodel = apps.get_model(*detail_model.split('__'))
                detail_obj = queryset_service.queryset(
                    request, dmodel).filter(pk=detail_id).last()
            return export_excel(self._export_type_config, self.get_queryset(), detail_obj)
        
        else:  # 原始旧版导出
            if admin_class:
                exportable = getattr(admin_class, admin.BSM_EXPORTABLE, False)
                if not exportable:
                    raise exceptions.BusinessException(
                        error_code=exceptions.MODEL_EXPORT_IS_NOT_SUPPORT
                    )
            else:
                raise exceptions.BusinessException(
                    error_code=exceptions.MODEL_EXPORT_IS_NOT_SUPPORT
                )
            serializer_queryset_handler = self._export_type_config.get(
                'serializer_queryset_handler'
            )
            if serializer_queryset_handler:
                func_handler = getattr(admin_class, serializer_queryset_handler, None)
                if func_handler:
                    queryset = func_handler(queryset)

            actual_app_label = self._export_type_config.get('actual_app_label')
            actual_model_slug = self._export_type_config.get('actual_model_slug')

            if actual_app_label and actual_model_slug:
                self.model = apps.get_model(actual_app_label, actual_model_slug)

            custom_serializer_class = self._export_type_config.get('serializer_class')
            serializer_class = get_export_serializer_class(
                self.model,
                self.get_serializer_class(),
                custom_serializer_class=custom_serializer_class,
            )
            return renderers.csv_render(
                self.model, queryset, serializer_class, export_config=self._export_type_config
            )


    @action(methods=['POST', 'GET'], detail=False, url_path='func')
    def func(self, request, app, model, **kwargs):
        """云函数, 由客户端直接调用的服务函数
        """
        data = request.data
        func_name = data.get('func_name', None) or request.GET.get('func_name', None)
        params = data.get('params', {}) or json.loads(request.GET.get('params', '{}'))
        return rest_services.manage_func(
            self, request.user, app, model, func_name, params
        )

    @action(methods=['GET', 'POST'], detail=False, url_name='functions')
    def functions(self, request, app, model, **kwargs):
        """获取云函数定义。
        """
        scene = request.query_params.get('scene')
        return rest_services.functions(self, app, model, scene)
