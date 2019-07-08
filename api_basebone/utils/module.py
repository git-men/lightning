import importlib
from django.conf import settings

# admin 类
BSM_ADMIN = 'admin'

# 管理后台的批量操作
BSM_BATCH_ACTION = 'actions'

# 管理后台的的自定义表单
BSM_FORM = 'forms'

# 管理后台导出的自定义序列化类
BSM_EXPORT = 'exports'

BSM_GLOBAL_MODULE = 'bsmconfig'

# 全局统一配置的菜单模块文件名
BSM_GLOBAL_MODULE_MENU = 'menu'
# 全局统一配置的菜单模块中声明的管理端的菜单的键
BSM_GLOBAL_MODULE_MENU_MANAGE = 'MANAGE_MENU'

# 全局统一的配置的模型角色配置的文件名
BSM_GLOBAL_MODULE_ROLES = 'roles'

"""
全局统一的配置的权限模块中对象的键

数据结构

ROLES = {
    member__user: {,
        'filters': 过滤条件'
    },
    ...
}
"""
BSM_GLOBAL_ROLES = 'ROLES'

# 角色中的配置，是否使用 bsm admin 中的 use_admin_filter_by_login_user 配置进行筛选
BSM_GLOBAL_ROLE_USE_ADMIN_FILTER_BY_LOGIN_USER = 'use_admin_filter_by_login_user'

BSM_GLOBAL_ROLE_QS_DISTINCT = 'distinct'


def get_admin_module(app_full_name, slug=BSM_ADMIN):
    """获取管理后台指定的模块"""
    try:
        module_name = f'{app_full_name}.bsm.{slug}'
        module = importlib.util.find_spec(module_name)
        if module:
            return importlib.import_module(module_name)
    except ModuleNotFoundError:
        return


def import_class_from_string(value):
    """
    尝试从一个字符串中加载一个类
    """
    try:
        module_path, class_name = value.rsplit('.', 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except (ImportError, AttributeError):
        raise ImportError(f'不能加载 {value}')


def get_bsm_global_module(config_module_name):
    """获取全局配置的模块"""
    try:
        module_name = getattr(settings, 'BSM_GLOBAL_MODULE', BSM_GLOBAL_MODULE)
        module_name = f'{module_name}.{config_module_name}'
        module = importlib.util.find_spec(module_name)
        if module:
            return importlib.import_module(module_name)
    except ModuleNotFoundError:
        return
