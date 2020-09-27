import inspect
from inspect import Parameter
from api_basebone.core import exceptions


funcs = {}


def register_func(app, model, func_name, func, options):
    funcs[app, model, func_name] = func, options


def bsm_func(name, model, login_required=True, staff_required=False, superuser_required=False):
    # 做注册工作，把下层的方法注册到funcs里面去。
    def _decorator(function):
        app = model._meta.app_label
        model_name = model._meta.model_name
        func_name = name if name else function.__name__
        register_func(
            app, model_name, func_name, function, {
                'login_required': login_required,
                'staff_required': staff_required,
                'superuser_required': superuser_required,
                'permissions': []
            })
        return function
    return _decorator


def find_func(app, model, func_name):
    if (app, model, func_name) not in funcs:
        return None, None
    func, options = funcs[app, model, func_name]

    def proxy(*args, **kwargs):
        signature = inspect.signature(func)
        required = {k for k, p in list(signature.parameters.items())[len(args):] if p.default == Parameter.empty and p.kind in [Parameter.KEYWORD_ONLY, Parameter.POSITIONAL_OR_KEYWORD]}
        lack = required - kwargs.keys()
        if lack:
            raise exceptions.BusinessException(exceptions.PARAMETER_FORMAT_ERROR, '、'.join(lack)+' 必填')
        return func(*args, **kwargs)

    return proxy, options
