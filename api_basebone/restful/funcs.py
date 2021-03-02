import inspect
import types
from inspect import Parameter
from api_basebone.core import exceptions
from api_basebone.sandbox.functions import __all__
from hashlib import md5

from django.apps import apps


funcs = {}

lightning_rt_function_scripts = types.ModuleType("lightning_rt_function_scripts")

def register_func(app, model, func_name, func, options):
    if (app, model) not in funcs:
        funcs[app, model] = {}
    funcs[app, model][func_name] = func, options

def bsm_func(name, model, login_required=True, staff_required=False, superuser_required=False, permissions=[]):
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
                'permissions': permissions
            })
        return function
    return _decorator


def find_dynamic_func(app, model, func_name):
    """从api_db里加载一下动态云函数。
    """
    empty = (None, None)
    if not apps.is_installed('api_db'):
        return empty

    from api_db.models import Function
    # TODO, 加缓存。
    func = Function.objects.filter(model=f'{app}__{model}', name=func_name, enable=True).prefetch_related('functionparameter_set')
    if not func:
        return empty
    func_obj = func[0]
    if not func_obj.code:
        return empty
    
    check_sum = md5(func_obj.code.encode('utf-8')).hexdigest()
    script_name = f'{func_name}_{check_sum}'
    func = getattr(lightning_rt_function_scripts, script_name, None)
    if not func:
        params = func_obj.functionparameter_set.all()
        required_params = [p.name for p in params if p.required]
        optional_params = [p.name for p in params if not p.required]
        sign = ''
        if required_params:
            sign = ', '.join(required_params)
        if optional_params:
            sign = ', '.join([sign,
            ', '.join([f'{p}=None' for p in optional_params])])
        scene_param = {
            Function.SCENE_UNLIMIT: '',
            Function.SCENE_INLINE_ACTION: 'id',
            Function.SCENE_BATCH_ACTION: 'ids',
        }[func_obj.scene]
        if sign or scene_param:
            if sign:
                if scene_param:
                    sign = ', '.join([scene_param, sign])
            else:
                if scene_param:
                    sign = scene_param
            params_str = ', '.join(['user', sign, '**context'])
        else:
            params_str = ', '.join(['user', '**context'])
        head = f'def {func_name}({params_str}):'
        head += '\n    from api_basebone.sandbox.functions import %s' % ', '.join(__all__)
        body = ('\n' + func_obj.code.strip()).replace('\n', '\n' + ' ' * 4).replace('\t', ' ' * 4)
        print(head + body)
        exec(head + body)
        func = locals().get(func_name, None)
        if not func:
            print('can not create function from code')
            return
        
        # 先清理旧版本的模块方法
        old_func = [f for f in dir(lightning_rt_function_scripts) if f.startswith(func_name)]
        for of in old_func:
            delattr(lightning_rt_function_scripts, of)
        
        # 把新版本的方法植入
        setattr(lightning_rt_function_scripts, script_name, func)
    
    return func, {
        'login_required': func_obj.login_required,
        'staff_required': func_obj.staff_required,
        'superuser_required': func_obj.superuser_required
    }


def find_func(app, model, func_name):
    if (app, model) not in funcs or func_name not in funcs[app, model]:
        func, options = find_dynamic_func(app, model, func_name)
        if not func:
            return func, options
    else:
        func, options = funcs[app, model][func_name]

    def proxy(*args, **kwargs):
        signature = inspect.signature(func)
        required = {k for k, p in list(signature.parameters.items())[len(args):] if p.default == Parameter.empty and p.kind in [Parameter.KEYWORD_ONLY, Parameter.POSITIONAL_OR_KEYWORD]}
        lack = required - kwargs.keys()
        if lack:
            raise exceptions.BusinessException(exceptions.PARAMETER_FORMAT_ERROR, '、'.join(lack)+' 必填')
        return func(*args, **kwargs)

    return proxy, options


def functions_for_model(app, model):
    return funcs.get((app, model), {})