import importlib

# admin 类
BSM_ADMIN = 'admin'

# 管理后台的批量操作
BSM_BATCH_ACTION = 'actions'

# 管理后台的的自定义表单
BSM_FORM = 'forms'


def get_admin_module(app_full_name, slug=BSM_ADMIN):
    """获取管理后台指定的模块"""
    try:
        module_name = f'{app_full_name}.bsm.{slug}'
        module = importlib.util.find_spec(module_name)
        if module:
            return importlib.import_module(module_name)
    except ModuleNotFoundError:
        return
