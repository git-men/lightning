import inspect
from functools import wraps
from django.conf import settings

FUNCTION_RETRY_COUNT_LIMIT = getattr(
    settings, 'FUNCTION_RETRY_COUNT_LIMIT', 1)


def func_retry(max_limit=FUNCTION_RETRY_COUNT_LIMIT):
    """给函数加上重试机制"""

    if inspect.isfunction(max_limit):
        func = max_limit
        max_limit = FUNCTION_RETRY_COUNT_LIMIT

        @wraps(func)
        def wrapper(*args, count=1, **kwargs):
            try:
                return func()
            except Exception:
                if count > max_limit:
                    # 记录日志
                    print('end..', count, args, kwargs)
                else:
                    count = count + 1
                    wrapper(*args, count=count, **kwargs)
        return wrapper
    else:
        def middle(func):

            @wraps(func)
            def wrapper(*args, count=1, **kwargs):
                try:
                    return func()
                except Exception:
                    if count > max_limit:
                        # 记录日志
                        print('end..', count, args, kwargs)
                    else:
                        count = count + 1
                        wrapper(*args, count=count, **kwargs)
            return wrapper
        return middle


@func_retry(max_limit=4)
def retry():
    raise Exception('this si exxception')
    print('world')


@func_retry
def retrys():
    raise Exception('this si exxception')
    print('world')
