from collections import namedtuple

Param = namedtuple('Param', ['name', 'display_name', 'type', 'required', 'default', 'choices'])
Param.__new__.__defaults__ = (None,) * len(Param._fields)
_FORMATTERS = {}

def formatter(name=None, params=[]):
    def deco_func(func):
        # 做注册工作
        func_name = name if name else func.__name__
        _FORMATTERS[func_name] = (params, func)
        return func
    return deco_func

def format(value, formatter, params=None):
    if formatter not in _FORMATTERS:
        return value
    func = _FORMATTERS[formatter][1]
    # TODO，校验一下参数合法性
    return func(value, **params)

@formatter(name='prefix', params=[
    Param(name="prefix", display_name='前缀', type='str', required=True)
])
def prefix_formatter(value, prefix):
    return f'{prefix}{str(value)}'

@formatter(name='suffix', params=[
    Param(name="suffix", display_name='后缀', type='str', required=True)
])
def suffix_formatter(value, suffix):
    return f'{str(value)}{suffix}'

@formatter(name='bothfix', params=[
    Param(name="prefix", display_name='前缀', type='str'),
    Param(name="suffix", display_name='后缀', type='str')
])
def bothfix_formatter(value, prefix='', suffix=''):
    result = value
    if prefix:
        result = prefix_formatter(result, prefix)
    if suffix:
        result = suffix_formatter(result, suffix)
    return result
