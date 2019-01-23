
funcs = {}


def register_func(app, model, func_name, func, options):
    funcs[f'{app}/{model}/@{func_name}'] = (func, options)


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
    func, options = funcs.get(f'{app}/{model}/@{func_name}', (None, None))
    return func, options
