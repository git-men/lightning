from api_basebone.utils import meta
from api_basebone.core import exceptions
from api_basebone.restful.serializers import (
    create_serializer_class,
    multiple_create_serializer_class,
)
from api_basebone.restful.relation import reverse_many_to_many


def forward_many_to_many(field, value, update_data):
    """处理正向的多对多关系

    - 如果多对多关系的字段的值不是列表，则不做任何处理
    - 如果传进来的值是一个列表，则不做任何处理

    上面的后续校验扔给下一步的创建或者更新的表单验证
    """
    if not (isinstance(value, list) and value):
        return

    key = field.name
    pure_data, object_data = [], []
    for item in value:
        object_data.append(item) if isinstance(item, dict) else pure_data.append(item)

    # 如果不包含对象数据，则不做任何处理
    if not object_data:
        return

    model = field.related_model
    pk_field_name = model._meta.pk.name

    # 筛选更新的列表和创建的列表
    create_list, update_list = [], []
    for item in object_data:
        update_list.append(item) if pk_field_name in item else create_list.append(item)

    if create_list:
        create_ids = []
        for item_data in create_list:

            # FIXME: 嵌套处理
            forward_relation_hand(model, item_data)

            serializer = create_serializer_class(model, allow_one_to_one=True)(data=item_data)
            serializer.is_valid(raise_exception=True)
            create_ids.append(serializer.save().pk)
        pure_data += create_ids

    if update_list:
        update_data_map = {item[pk_field_name]: item for item in update_list}
        filter_params = {f'{pk_field_name}__in': update_data_map.keys()}
        queryset = model.objects.filter(**filter_params)

        # 检查查询出的数据是否和传入的 id 长度一致
        if queryset.count() != len(update_list):
            raise exceptions.BusinessException(
                error_code=exceptions.OBJECT_NOT_FOUND,
                error_data=f'{key}: {update_list} 存在不合法的数据',
            )

        for instance in queryset.iterator():
            item_data = update_data_map.get(getattr(instance, pk_field_name, None))

            # FIXME: 嵌套处理
            forward_relation_hand(model, item_data)
            serializer = create_serializer_class(model, allow_one_to_one=True)(
                instance=instance, data=item_data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
        pure_data += update_data_map.keys()
    update_data[key] = pure_data
    return update_data


def forward_one_to_many(field, value, update_data):
    """处理正向的一对多关系

    - 如果数据不是一个字典，则直接返回
    - 如果数据是字典，字典中没有包含主键，则对字典中的数据进行创建
    - 如果数据是字典，字典中包含主键，则对主键指定的数据进行更新
    """
    if not isinstance(value, dict):
        return

    model, key = field.related_model, field.name
    pk_field_name = model._meta.pk.name

    # 如果传进来的数据不包含主键，则代表是创建数据
    if pk_field_name not in value:
        # FIXME: 嵌套处理
        forward_relation_hand(model, value)

        serializer = create_serializer_class(model, allow_one_to_one=True)(data=value)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        update_data[key] = instance.pk
        reverse_relation(model, value, instance)
        return update_data

    # 如果传进来的数据包含主键，则代表是更新数据
    instance = model.objects.filter(**{pk_field_name: value[pk_field_name]}).first()
    if not instance:
        raise exceptions.BusinessException(
            error_code=exceptions.OBJECT_NOT_FOUND,
            error_data=f'{key}: {value} 指定的主键找不到对应的数据',
        )

    # FIXME: 嵌套处理
    forward_relation_hand(model, value)

    serializer = create_serializer_class(model, allow_one_to_one=True)(
        instance=instance, data=value, partial=True
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    update_data[key] = value[pk_field_name]
    reverse_relation(model, value, instance)
    return update_data


def reverse_one_to_many(field, value, instance, detail=True):
    """处理反向字段的多对一的数据

    对于此种场景，数据格式是包含对象的列表或者已经存在对象的主键

    注意事项：
    - 创建时，不能传入包含主键的数据

    场景描述：
        class AModel(models.Model):
            pass

        class BModel(models.Model):
            a = models.ForgignKey(AModel)
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
    model, key = field.related_model, field.name
    pk_field_name = model._meta.pk.name

    # 进行到这一步，说明对应的键时存在的，对于反向字段，就直接校验数据
    if not isinstance(value, list):
        raise exceptions.BusinessException(
            error_code=exceptions.PARAMETER_FORMAT_ERROR,
            error_data=f'{key}: {value} 只能是列表',
        )

    # 这里需要判断创造和更新
    if detail:
        # 如果是更新，如果传入空的数据，则删除掉对应的数据
        if not value:
            try:
                related_name = meta.get_relation_field_related_name(
                    model, field.remote_field.name
                )
                if related_name:
                    relation = getattr(instance, related_name[0], None)
                    if relation:
                        relation.all().delete()
                        return
            except Exception as e:
                raise exceptions.BusinessException(
                    error_code=exceptions.PARAMETER_FORMAT_ERROR, error_data=str(e)
                )
    else:
        # 如果是创建，如果传进来的值为空
        if not value:
            return

    value = forward_relation_hand(model, value)

    pure_id_list, object_data_list = [], []
    for item in value:
        if isinstance(item, dict):
            object_data_list.append(item)
            if pk_field_name in item:
                pure_id_list.append(item[pk_field_name])
        else:
            pure_id_list.append(item)

    if object_data_list:
        # TODO: 创建时，不能传入包含主键的数据
        for item in object_data_list:
            if not detail and pk_field_name in item:
                raise exceptions.BusinessException(
                    error_code=exceptions.PARAMETER_BUSINESS_ERROR,
                    error_data=f'{key}: {value} 当前为 create 操作，不能传入包含主键的数据',
                )

        for item_value in object_data_list:
            if pk_field_name in item_value:
                # 此时说明是更新的数据
                pk_value = model._meta.pk.to_python(item_value[pk_field_name])

                filter_params = {
                    pk_field_name: pk_value,
                    # FIXME 註釋掉這句之後會有安全隱患 field.remote_field.name: instance,
                }
                obj = model.objects.filter(**filter_params).first()
                if not obj:
                    raise exceptions.BusinessException(
                        error_code=exceptions.OBJECT_NOT_FOUND,
                        error_data=f'{key}: {value} 指定的主键找不到对应的数据',
                    )

                item_value[field.remote_field.name] = instance.pk
                serializer = create_serializer_class(model, allow_one_to_one=True)(
                    instance=obj, data=item_value, partial=True
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
            else:
                # 如果传进来的数据不包含主键，则代表是创建数据
                item_value[field.remote_field.name] = instance.pk
                serializer = create_serializer_class(model, allow_one_to_one=True)(data=item_value)
                serializer.is_valid(raise_exception=True)
                obj = serializer.save()
                if detail:
                    pure_id_list.append(getattr(obj, pk_field_name))

            reverse_relation(field.related_model, item_value, obj)

    # 如果是更新，则删除掉对应的数据
    if detail and pure_id_list:
        pure_id_list = [model._meta.pk.to_python(item) for item in pure_id_list]
        relation = meta.get_relation_field_related_name(model, field.remote_field.name)

        if relation:
            model.objects.filter(pk__in=pure_id_list).update(
                **{relation[1].name: instance}
            )
            getattr(instance, relation[0]).exclude(
                **{f'{pk_field_name}__in': pure_id_list}
            ).delete()
    elif pure_id_list:
        # 如果是创建，则需要创建对应的数据
        pure_id_list = [model._meta.pk.to_python(item) for item in pure_id_list]
        relation = meta.get_relation_field_related_name(model, field.remote_field.name)
        getattr(instance, relation[0]).add(
            *model.objects.filter(**{f'{pk_field_name}__in': pure_id_list})
        )


def forward_relation_hand(model, data):
    """正向的关系字段预处理

    例如文章和图片存在多对多，在新建文章时，对于图片，前端有可能会 push 以下数据

        - 包含对象的列表，[{字段：值，字段：值...}]
        - 包含 id 的列表
        - 包含 id 和对象的列表

    对于这种场景，需要检查客户端传进来的数据，同时需要做对应的预处理

    这里处理的是正向字段，而不是反向字段，所以获取关系字段时，不包含反向字段

    这里面包含两种关系
    - 正向的一对多
    - 正向的多不多
    """
    # 这里的 data 是原始数据，这里可能会存在递归处理，第一次是从客户端传进来的数据
    if not (data and isinstance(data, (dict, list))):
        return

    if isinstance(data, dict):
        update_data = {}
        for key, value in data.items():
            field = meta.get_relation_field(model, key)
            if not field:
                continue

            if field.concrete:
                if field.many_to_many:
                    forward_many_to_many(field, value, update_data)
                else:
                    forward_one_to_many(field, value, update_data)
        data.update(update_data)
        return data
    else:
        for value in data:
            forward_relation_hand(model, value)
        return data


def reverse_one_to_one(field, value, instance):
    model = field.related_model
    pk_field = model._meta.pk
    to_field_value = getattr(instance, field.field_name)
    if isinstance(value, dict):
        remote_field_name = field.remote_field.name

        Serializer = create_serializer_class(model, allow_one_to_one=True)
        value = forward_relation_hand(model, value)
        if pk_field.name not in value:
            model.objects.filter(**{field.remote_field.name: to_field_value}).delete()
            value[field.remote_field.name] = to_field_value
            serializer = Serializer(data=value)
        else:
            pk_value = pk_field.to_python(value[pk_field.name])
            filter_params = {
                pk_field.name: pk_value,
                field.remote_field.name: to_field_value,
            }
            obj = model.objects.filter(**filter_params).first()
            if not obj:
                raise exceptions.BusinessException(
                    error_code=exceptions.OBJECT_NOT_FOUND,
                    error_data=f'{model}指定的主键[{pk_value}]找不到对应的数据',
                )

            value[remote_field_name] = to_field_value
            serializer = Serializer(instance=obj, data=value, partial=True)

        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        reverse_relation(field.related_model, value, obj)
    else:
        if value is None:
            model.objects.filter(**{field.remote_field.name: to_field_value}).delete()
        else:
            pass
            # 不應該改掉原先的關聯關係，所以註釋掉，改爲pass了。什麼都不做。
            # model.objects.filter(**{pk_field.name: pk_field.to_python(value)}).update(**{field.remote_field.name: to_field_value})


def reverse_relation(model, data, instance):
    # 如果存在反向字段数据，则需要处理
    reverse_relation_fields = meta.get_reverse_fields(model)
    if reverse_relation_fields:
        for item in reverse_relation_fields:
            if item.name in data:
                reverse_relation_hand(
                    item.model, {item.name: data[item.name]}, instance=instance, whole_data=data
                )


def reverse_relation_hand(model, data, instance, detail=True, whole_data=None):
    """反向关系字段的处理

    Params:
        model object 模型类
        data list | dict 数据
        instance object 数据对象
        detail bool 更新或者创建
    """
    if not (data and isinstance(data, (dict, list))):
        return

    for key, value in data.items():
        # 查找关系字段
        field = meta.get_relation_field(model, key, reverse=True)
        if not field:
            continue

        if meta.check_field_is_reverse(field):
            # 这里说明反向字段肯定传了进来，值的校验放在各个处理方法中
            if field.many_to_many:
                reverse_many_to_many(instance, field, value)
            elif field.one_to_many:
                reverse_one_to_many(field, value, instance, detail=detail)
            elif field.parent_link and isinstance(value, dict):
                model = field.related_model
                remote_field_name = field.remote_field.name

                class ParentLinkSerializer(create_serializer_class(model, allow_one_to_one=True)):
                    """支持parent_link=True"""
                    def build_field(self, field_name, *args, **kwargs):
                        if field_name == remote_field_name:
                            from rest_framework.utils.model_meta import RelationInfo
                            from rest_framework.utils.model_meta import _get_to_field
                            relation_info = RelationInfo(
                                model_field=field.remote_field,
                                related_model=field.remote_field.remote_field.model,
                                to_many=False,
                                to_field=_get_to_field(field.remote_field),
                                has_through_model=False,
                                reverse=False
                            )
                            return self.build_relational_field(field_name, relation_info)
                        return super().build_field(field_name, *args, **kwargs)
                value = forward_relation_hand(model, value)
                value.update(whole_data)
                value[remote_field_name] = instance.pk
                serializer = ParentLinkSerializer(data=value)
                print(value, serializer.Meta.fields)
                serializer.is_valid(raise_exception=True)
                obj = serializer.save()
                reverse_relation(model, value, obj)
            elif field.one_to_one:
                reverse_one_to_one(field, value, instance)


data = [
    {
        "key": {"id": 1, "name": "颜色", "data_type": "string"},
        "level": 0,
        "values": [
            {
                "cover": {"name": "wwwwwww-3", "url": "http://fjadskfasd.com"},
                "value": {"id": 1, "value": "黄色", "key": 1},
            }
        ],
    }
]
