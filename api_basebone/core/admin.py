from importlib import import_module

from django.contrib.admin import ModelAdmin as DjangoModelAdmin
from django.conf import settings
from django.utils import six
from api_basebone.utils import get_lower_case_name
# 属性的常量声明

# 根据哪个字段进行筛选登录的用户，因为一个模型可能有多个字段指向用户模型
BSM_AUTH_FILTER_FIELD = 'user_field'

# 是否允许根据当前登录用户进行筛选
BSM_FILTER_BY_LOGIN_USER = 'filter_by_login_user'

# 声明父亲字段, 只用来针对树形结构做声明，只能配置单一的字段
BSM_PARENT_FIELD = 'parent_field'

BSM_DISPLAY = 'display'

# 以树型结构的表格展示
BSM_DISPLAY_IN_TREE = 'display_in_tree'

# 列表支持排序
BSM_DISPLAY_IN_SORT = 'display_in_sort'

BSM_SORT_KEY = 'sort_key'

BSM_INLINE_ACTIONS = 'inline_actions'

BSM_MAX_INLINE_ACTIONS = 'max_inline_actions'

BSM_TABLE_ACTIONS = 'table_actions'

# 批量操作
BSM_BATCH_ACTION = 'actions'

BSM_MODAL_FORM = 'modal_form'

BSM_MODAL_DETAIL = 'modal_detail'

BSM_MODAL_CONFIG = 'modal_config'

# 默认排序
BSM_ORDER_BY = 'order_by'

# 表单的过滤
BSM_FILTER = 'filter'

# 表单
BSM_FORM_FIELDS = 'form_fields'

# 表单分组的风格
BSM_FORM_LAYOUT = 'form_layout'

# 列表的风格
BSM_LIST_STYLE = 'list_style'

# 内联表单设置
BSM_INLINE_FORM_FIELDS = 'inline_form_fields'

# 数据详情的展开字段列表
BSM_DETAIL_EXPAND_FIELDS = 'form_expand_fields'

# 是否可以导出文件
BSM_EXPORTABLE = 'exportable'

# 默认的过滤条件
BSM_DEFAULT_FILTER = 'default_filter'

# 统计数据的配置
BSM_STATISTICS = 'statistics'

# 允许排序的字段
BSM_SORTABLE = 'sortable'

# 详情页
BSM_DETAILS = 'details'

# 详情布局
BSM_DETAIL_LAYOUT = 'detail_layout'

# 合法的前端管理端的设置
VALID_MANAGE_ATTRS = [
    BSM_AUTH_FILTER_FIELD,
    # BSM_FILTER_BY_LOGIN_USER,
    BSM_PARENT_FIELD,
    BSM_DISPLAY,
    BSM_INLINE_ACTIONS,
    BSM_MAX_INLINE_ACTIONS,
    BSM_TABLE_ACTIONS,
    BSM_BATCH_ACTION,
    BSM_MODAL_FORM,
    BSM_MODAL_DETAIL,
    BSM_MODAL_CONFIG,
    BSM_ORDER_BY,
    BSM_FILTER,
    BSM_FORM_FIELDS,
    BSM_FORM_LAYOUT,
    BSM_LIST_STYLE,
    BSM_INLINE_FORM_FIELDS,
    BSM_DETAIL_EXPAND_FIELDS,
    BSM_EXPORTABLE,
    BSM_STATISTICS,
    BSM_DISPLAY_IN_TREE,
    BSM_SORTABLE,
    BSM_DISPLAY_IN_SORT,
    BSM_SORT_KEY,
    'detail',  # 详情页临时配置
    BSM_DETAILS,
    BSM_DETAIL_LAYOUT,
]

# 属性和默认值映射
ATTRS_DICT = {
    BSM_AUTH_FILTER_FIELD: None,
    BSM_FILTER_BY_LOGIN_USER: False,
    BSM_PARENT_FIELD: None,
    BSM_EXPORTABLE: False,
}


class BSMAdmin:
    """通用套件全局定义管理配置的基类

    用户可以继承此类，然后重新定义配置，然后服务端导出配置，
    前端可以根据配置动态的构造管理后台界面
    """

    pass


for key, value in ATTRS_DICT.items():
    setattr(BSMAdmin, key, value)


class BSMAdminModule:
    """管理项目的 admin 的所有的 BSM 类"""

    modules = {}


def register(admin_class):
    _meta = admin_class.Meta.model._meta
    key = f'{_meta.app_label}__{_meta.model_name}'
    # if key not in BSMAdminModule.modules:
    BSMAdminModule.modules[key] = admin_class
    return admin_class


configs = {}
config_had_init = {}

def set_config(model, config):
    if isinstance(model, str):
        key = model
    else:
        key = '{}__{}'.format(model._meta.app_label, model._meta.model_name)
    if not config:
        del config[key]
    else:
        configs[key] = config

def get_config(model, name, view_type='list', view=None):
    """获取指定模型的配置值，优先获取配置数据的值，其实是类的值。
    """
    views = f'{view_type}Views'
    key = '{}__{}'.format(model._meta.app_label, model._meta.model_name)
    if not config_had_init.get(key, None):
        backend = getattr(settings, 'LIGHTNING_ADMIN_CONFIG_LOADER', None)
        if backend:
            func = backend.split('.')
            mod = '.'.join(func[:-1])
            method = func[-1]
            mod = import_module(mod)
            method = getattr(mod, method)
            cs = method()
            for k, v in cs.items():
                set_config(k, v)
        config_had_init[key] = True
    
    if key in configs:
        config = configs[key]
        result = config.get(name, {})
        config_vi = config.get(views, {}).get(view, None) if view else None
    else:
        cls = BSMAdminModule.modules.get(key)
        if not cls:
            return None
        result = getattr(cls, get_lower_case_name(name), None)
        config_vi = getattr(cls, views, {}).get(view, None) if view else None
    
    
    if view:  # 指定了视图
        if not config_vi:
            return None
        
        # 视图中没有定义属性，但是开启了继承，则使用默认的
        if name not in config_vi and config_vi.get('inherit', False):
            return result
        return config_vi.get(name, None)
