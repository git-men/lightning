from celery import shared_task
from member.models import User
import types
from lightning_code.models import Function
from api_basebone.sandbox.functions import __all__
from celery import Celery

lightning_rt_custom_functions = types.ModuleType('lightning_rt_custom_functions')

@shared_task
def call_function(db_func, params={}, develop_mode=False):
    """执行指定异步任务，调用动态函数
    """
    # 从数据库中查询到任务，读取最新代码，生成function对象，使用参数调用之。
    func = Function.objects.filter(name=db_func, enable=True).prefetch_related('parameters')
    if func:
        func = func[0]
    else:
        raise RuntimeError(f'function {db_func} not found')
    def_params = func.parameters.all()
    required_params = [p.name for p in def_params if p.required]
    optional_params = [p.name for p in def_params if not p.required]
    sign = ''
    if required_params:
        sign = ', '.join(required_params)
    if optional_params:
        sign = ', '.join([sign,
        ', '.join([f'{p}=None' for p in optional_params])])

    if develop_mode:
        # 启用开发模型，使用code字段的代码。
        code = func.code or ''
        head = f'def {func.name}({sign}):'
        head += '\n    from api_basebone.sandbox.functions import %s' % ', '.join(__all__)
        body = ('\n' + code.strip()).replace('\n', '\n' + ' ' * 4).replace('\t', ' ' * 4)
        print(head + body)
        exec(head + body)
        func_obj = locals().get(func.name, None)
    else:
        func.released_check_sum 
        func_name = f'{func.name}_{func.released_check_sum }'
        func_obj = getattr(lightning_rt_custom_functions, func_name, None)
        if not func_obj:
            code = func.released_code or ''
            head = f'def {func.name}({sign}):'
            head += '\n    from api_basebone.sandbox.functions import %s' % ', '.join(__all__)
            body = ('\n' + code.strip()).replace('\n', '\n' + ' ' * 4).replace('\t', ' ' * 4)
            print(head + body)
            exec(head + body)
            func_obj = locals().get(func.name, None)
            old_func = [f for f in dir(lightning_rt_custom_functions) if f.startswith(func.name)]
            for of in old_func:
                delattr(lightning_rt_custom_functions, of)
            
            setattr(lightning_rt_custom_functions, func_name, func_obj)
    return func_obj(**params)


@shared_task
def _excute_async(func_obj, params=None):
    """把一个方法变成异步调用。
    """
    return func_obj(**params)


# @shared_task
# def add_periodic_task(schedule, func, args=(), kwargs={}, name=None, develop_mode=False):
#     """增加定时调度任务
#     """
#     if not celery_app:
#         print('no celery instance found ...')
#         return
#     app = celery_app.values()[0]
#     app.add_periodic_task(
#         schedule,
#         call_function,
#         args=(func,),
#         kwargs={
#             'params': kwargs,
#             'develop_mode': develop_mode
#         },
#         name=name
#     )