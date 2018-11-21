import importlib


def get_admin_module(app_full_name, slug='admin'):
    """获取管理后台指定的模块"""
    try:
        module_name = f'{app_full_name}.bsm.{slug}'
        module = importlib.util.find_spec(module_name)
        if module:
            return importlib.import_module(module_name)
    except ModuleNotFoundError:
        return
