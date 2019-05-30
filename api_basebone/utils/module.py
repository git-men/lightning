import importlib

# admin 类
BSM_ADMIN = 'admin'

# 管理后台的批量操作
BSM_BATCH_ACTION = 'actions'

# 管理后台的的自定义表单
BSM_FORM = 'forms'

# 管理后台导出的自定义序列化类
BSM_EXPORT = 'exports'


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
