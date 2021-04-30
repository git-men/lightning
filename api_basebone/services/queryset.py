import logging

from django.contrib.auth import get_user_model

from api_basebone.utils.operators import build_filter_conditions2
from api_basebone.settings import settings
from api_basebone.utils.meta import get_bsm_model_admin, get_all_relation_fields
from api_basebone.utils import meta, module as basebone_module
from api_basebone.utils import queryset as queryset_utils
from api_basebone.core import admin
from api_basebone.core.admin import get_config
from api_basebone.restful.serializers import sort_expand_fields

log = logging.getLogger(__name__)


class Query:
    def __new__(cls, request, model, *args, **kwargs):
        if hasattr(model, 'GMeta') and hasattr(model.GMeta, 'query_class'):
            cls = model.GMeta.query_class
        return super().__new__(cls)

    def __init__(self, request, model, action='list', filters=[], fields=[], expand_fields=[], order=[], tree_data=None, skip_distinct=False, view=None):
        """通用数据查询类。
        - user，当前查询用户
        - model，查询的模型
        - filters，查询条件
        - fields，需要返回的字段
        - expand_fields，需要关联查询的其他字段
        - order, 排序
        """
        self.request = request
        self.model = model
        self.action = action
        self.filters = filters
        self.fields = fields
        self.expand_fields = expand_fields
        self.order = order
        self.tree_data = tree_data
        self.skip_distinct = skip_distinct
        self.view = view

    def basebone_get_model_role_config(self):
        """获取角色配置"""
        model = self.model
        role_config = getattr(
            basebone_module.get_bsm_global_module(
                basebone_module.BSM_GLOBAL_MODULE_ROLES
            ),
            basebone_module.BSM_GLOBAL_ROLES,
            None,
        )
        key_prefix = f'{model._meta.app_label}__{model._meta.model_name}'
        if isinstance(role_config, dict):
            return role_config.get(key_prefix, None)

    def get_user_role_filters(self, role_config):
        """获取此用户权限对应的过滤条件"""
        user = self.request.user
        if user and user.is_staff and user.is_superuser:
            return []

        if role_config and isinstance(role_config, dict):
            return role_config.get('filters')

    def expand_field_mapper(self, item):
        field_list = item.split('.')
        _model = self.model
        for index, value in enumerate(field_list):
            field = _model._meta.get_field(value)
            if meta.check_field_is_reverse(field):
                result = meta.get_relation_field_related_name(
                    field.related_model, field.remote_field.name
                )
                if result:
                    field_list[index] = result[0]
            if field.is_relation:
                _model = field.related_model
        return '.'.join(field_list)

    def translate_expand_fields(self):
        """转换展开字段"""
        for idx, item in enumerate(self.expand_fields):
            # 这里一定要在 expand_fields 原对象上修改，因为 expand_fields 传了进来修改完成后，外面后续的程序还要依赖于修改后的格式
            self.expand_fields[idx] = self.expand_field_mapper(item)

    def _guard(self, queryset):
        # 如果不是超级用户，则进行对应的数据筛选
        model = self.model
        action = self.action
        user = self.request.user
        app_models = settings.MANAGE_GUARDIAN_DATA_APP_MODELS
        check_model = (
            isinstance(app_models, (list, set))
            and f'{model._meta.app_label}__{model._meta.model_name}' in app_models
        )
        check_not_is_superuser = not user.is_superuser
        # FIXME: 目前只做查询类
        check_action = action in ['retrieve', 'list', 'set']

        if check_not_is_superuser and check_action and check_model:
            from guardian.ctypes import get_content_type
            from guardian.models import UserObjectPermission, GroupObjectPermission
            from django.contrib.auth.models import Permission

            content_type = get_content_type(model)
            permission = Permission.objects.filter(
                codename=f'view_{model._meta.model_name}', content_type=content_type
            ).first()

            content_object_set = set()

            # 如果存在对应的权限
            if permission:
                permission_object_list = UserObjectPermission.objects.filter(
                    user=user, permission=permission
                ).values('object_pk')
                for item in permission_object_list:
                    content_object_set.add(item['object_pk'])

            user_groups = user.groups.all()
            if user_groups:
                group_object_list = GroupObjectPermission.objects.filter(
                    permission=permission, group__in=user_groups
                ).values('object_pk')
                for item in group_object_list:
                    content_object_set.add(item['object_pk'])

            if content_object_set:
                queryset = queryset.filter(id__in=content_object_set)
            return queryset
        return queryset

    def get_queryset_by_filter_user(self, role_config, queryset):
        """通过用户过滤对应的数据集

        - 如果用户是超级用户，则不做任何过滤
        - 如果用户是普通用户，则客户端筛选的模型有引用到了用户模型，则过滤对应的数据集

        FIXME: 这里先根据模型角色配置做出对应的响应

        TODO: 当前一个用户只能属于一个用户组，如果用户没有属于任何组，则暂时不做任何处理
        """
        user = self.request.user
        model = self.model
        if user and user.is_staff and user.is_superuser:
            return queryset

        if role_config:
            # 如果
            config_key = basebone_module.BSM_GLOBAL_ROLE_USE_ADMIN_FILTER_BY_LOGIN_USER
            if role_config.get(config_key):
                return queryset

        # 检测模型中是否有字段引用了用户模型
        has_user_field = meta.get_related_model_field(model, get_user_model())
        if has_user_field:
            admin_class = get_bsm_model_admin(model)
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
        # fields = self.request.data.get(const.ORDER_BY_FIELDS)
        fields = self.order
        if isinstance(fields, list) and fields:
            return queryset.order_by(*fields)
        return queryset

    def should_distinct_queryset(self, fields):
        """检测是否需要

        检测是否需要对结果集去重，去重需要单独做好检测
        因为去重在统计业务中，如果去重，对于关联的查询，会做子查询，导致
        结果不符合预期

        这里对于关系字段都需要做去重操作

        - 一对多
        - 多对一
        - 多对多
        """
        model = self.model
        action = self.action
        # 如果动作是创建或者跟单条数据相关的，不在进行去重操作
        if action in [
            'create',
            'retrieve',
            'destroy',
            'custom_patch',
            'update',
            'partial_update',
        ]:
            return False

        if not fields:
            return False

        # 获取非一对一的关系字段
        relation_fields = [
            item.name
            for item in get_all_relation_fields(model)
            if not item.one_to_one
        ]

        if not isinstance(fields, list):
            fields = [fields]

        separator = '__'

        for item in fields:
            if not isinstance(item, str):
                continue
            field = item.split(separator)[0]
            if field in relation_fields:
                return True

    def get_queryset_by_filter_conditions(self, role_config, queryset):
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
        user = self.request.user
        model = self.model
        action = self.action
        filters = self.filters
        view = self.view
        # 原先的写法是`if not queryset or self.action in ['create']`，这样会引起queryset调用__bool__，并会触发fetch_all，导致请求变慢
        if action in ['create']:
            return queryset, False

        role_filters = self.get_user_role_filters(role_config)
        filter_conditions = filters
        # FIXME: 如果是更新业务，则客户端无需传入过滤条件，为什么不像 create 直接返回呢
        # 因为更新操作是需要一定的权限，比如 A 创建的数据， B 是否有权限进行更新呢，都需要
        # 考量
        if action in ['update', 'partial_update', 'custom_patch']:
            filter_conditions = []

        default_filter = get_config(model, 'defaultFilter', 'list', view)
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
            distinct_queryset = self.should_distinct_queryset(list(fields))
            cons = build_filter_conditions2(
                filter_conditions, context={'user': user}
            )

            if cons:
                queryset = queryset.filter(cons)
            return queryset, distinct_queryset
        return queryset, False

    def get_queryset_by_with_tree(self, queryset):
        """如果是树形结构，则需要做对应的过滤"""
        tree_data = self.tree_data
        if tree_data:
            params = {tree_data[0]: tree_data[2]}
            return queryset.filter(**params)
        return queryset

    def get_queryset(self):
        model = self.model
        request = self.request
        # 1. 从最原始的queryset开始
        queryset = model.objects.all()

        context = {'user': request.user} if request else {}

        admin_class = get_bsm_model_admin(model)

        # 2. 添加expand_field
        if self.expand_fields:
            self.translate_expand_fields()
            expand_dict = sort_expand_fields(self.expand_fields)
            queryset = queryset_utils.queryset_prefetch(queryset, expand_dict, context, display_fields=self.fields)

        # 3. 添加计算字段的annotate
        if self.action not in ['get_chart', 'group_statistics']:
            queryset = queryset_utils.annotate(queryset, context=context)

        # 4. 如果GMeta重定义了get_queryset
        if hasattr(model, 'GMeta') and request:
            try:
                gm = model.GMeta()
            except Exception as e:
                log.error(str(e))
            else:
                if hasattr(gm, 'get_queryset'):
                    gmeta_get_queryset = gm.get_queryset
                    if gmeta_get_queryset is not None:
                        queryset = gmeta_get_queryset(queryset, request, None)

        role_config = self.basebone_get_model_role_config()
        log.debug(f'role_config: {role_config}')

        # 5. 根据当前用户过滤
        if request:
            queryset = self.get_queryset_by_filter_user(role_config, queryset)
        # 6. 根据条件过滤
        queryset, distinct_queryset = self.get_queryset_by_filter_conditions(role_config, queryset)
        # 7. 添加排序信息
        queryset = self.get_queryset_by_order_by(queryset)
        # 8. 树型数据特殊滤
        queryset = self.get_queryset_by_with_tree(queryset)

        # 9. 检测是否在Admin覆盖了get_queryset
        if admin_class and request:
            admin_get_queryset = getattr(admin_class(), 'get_queryset', None)
            if admin_get_queryset:
                queryset = admin_get_queryset(queryset, request, None)

        # 10. 如果开启了 guardian 数据权限检测，那么这里会进行必要的筛选
        if settings.MANAGE_GUARDIAN_DATA_PERMISSION_CHECK and request:
            queryset = self._guard(queryset)

        # 11. 权限中配置是否去重
        if self.skip_distinct:  # 统计和图表的场景不需要distinct.
            return queryset

        role_distict = False
        if role_config and isinstance(role_config, dict):
            role_distict = role_config.get(
                basebone_module.BSM_GLOBAL_ROLE_QS_DISTINCT, False
            )
        if distinct_queryset or role_distict:
            log.debug(
                f'basebone distinct queryset or role_distinct: {distinct_queryset}, {role_distict}'
            )
            queryset = queryset.distinct()

        return queryset


def queryset(*args, **kwargs):
    query = Query(*args, **kwargs)
    return query.get_queryset()


__all__ = ['queryset', 'Query']
