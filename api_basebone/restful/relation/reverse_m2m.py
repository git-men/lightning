"""
处理反向多对多关系的数据

注意中间表中的数据，可能会新增，会更新，会删除

# FIXME:
    - 对于使用自定义的 through 模型场景时，不做处理

反向的字段，注意以下情况

- related_query_name 和 related_name 同时声明的情况
- related_query_name 声明，但是 related_name 没有声明

场景描述：

    class AModel(models.Model):
        pass

    class BModel(models.Model):
        a = models.ManyToManyField(AModel)
        name = models.CharField()

AModel 请求数据时，字段中包含 bmodel 对象如下数据格式：

    FIXME: 创建和更新时可以传入：
        bmodel: [
            {
                name: 'xxxx'
            }
        ]

    或者

    FIXME: 只有更新时可以传入包含主键的数据:
        bmodel: [
            {
                'id': xxxx,
                'name': 'update xxxxx'
            }
        ]
"""

from api_basebone.core import exceptions
from api_basebone.utils import meta
from api_basebone.restful.serializers import create_serializer_class


def reverse_many_to_many(instance, field, data):
    """
    处理反向多对多关系的数据

    Params:
        instance object 对象
        field object 反向的字段
        data list 反向的模型字典列表数据
    """

    # 反向关系的数据必须是数组
    if not isinstance(data, list):
        raise exceptions.BusinessException(
            error_code=exceptions.PARAMETER_FORMAT_ERROR,
            error_data=f'{field.name}: {data} 只能是列表',
        )

    # TODO: 如果使用了自定义的中间表，此种业务暂时不做处理
    # TODO: 支持自定义中间表，如果非单纯中间表让它自行报异常，中间表必填值以后可以考虑使用 through_defaults
    # if field.through_fields:
    #     return

    model = field.related_model
    related_name = meta.get_accessor_name(field)
    reverse_manager = getattr(instance, related_name, None) if related_name else None

    if not data:
        # 传入数据为空的场景
        # 更新操作，如果传入空的数据，则清除掉此对象所有的数据
        if reverse_manager:
            reverse_manager.clear()
        return

    # 传入数据不为空的情况下
    pk_field_name = model._meta.pk.name
    # 迭代处理反向数据，这个时候还没有处理数据和对象的关系
    reverse_object_list = set()
    for item_value in data:
        if  isinstance(item_value, dict):
            if  pk_field_name not in item_value:
                # 创建反向模型的数据
                serializer = create_serializer_class(model)(data=item_value)
                serializer.is_valid(raise_exception=True)
                item_instance = serializer.save()
            else:
                # 更新反向模型的数据
                item_instance = model.objects.filter(
                    **{pk_field_name: item_value[pk_field_name]}
                ).first()
                if not item_instance:
                    raise exceptions.BusinessException(
                        error_code=exceptions.OBJECT_NOT_FOUND,
                        error_data=f'{pk_field_name}: {item_value} 指定的主键找不到对应的数据',
                    )
                serializer = create_serializer_class(model)(
                    instance=item_instance, data=item_value, partial=True
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
            reverse_object_list.add(item_instance.pk)
        else:
            reverse_object_list.add(item_value)

    # 处理数据和 instance 之间的关系
    if reverse_manager:
        reverse_manager.set(list(reverse_object_list))
