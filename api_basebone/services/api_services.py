from django.db.models import Max
from django.db import transaction

from api_basebone.core import exceptions
from api_basebone.restful.serializers import (
    # create_serializer_class,
    multiple_create_serializer_class,
)

from api_basebone.models import Api, Parameter, DisplayField, SetField, Filter


def save_api(config):
    """api配置信息保存到数据库"""
    with transaction.atomic():
        slug = config.get('slug', '')
        api = Api.objects.filter(slug=slug).first()
        is_create = False
        if not api:
            api = Api()
            api.slug = slug
            is_create = True
        api.app = config.get('app')
        api.model = config.get('model')
        api.operation = config.get('operation')
        if api.operation not in Api.OPERATIONS:
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data=f'\'operation\': {api.operation} 不是合法的操作',
            )
        if ('ordering' in config) and config['ordering']:
            api.ordering = config['ordering']
        if ('func_name' in config) and config['func_name']:
            api.func_name = config['func_name']
        else:
            if api.operation == api.OPERATION_FUNC:
                """云函数api，却没有函数名"""
                raise exceptions.BusinessException(
                    error_code=exceptions.PARAMETER_FORMAT_ERROR,
                    error_data=f'\'operation\': {api.operation} 操作，必须有func_name函数名',
                )
        api.save()

        save_parameters(api, config.get('parameter'), is_create)
        save_display_fields(api, config.get('displayfield'), is_create)
        save_set_fields(api, config.get('setfield'), is_create)
        save_filters(api, config.get('filter'), is_create)


def save_parameters(api, parameters, is_create):
    if not is_create:
        Parameter.objects.filter(api__id=api.id).delete()

    if not parameters:
        return

    # if api.operation in (api.OPERATION_CREATE,):
    #     raise exceptions.BusinessException(
    #         error_code=exceptions.PARAMETER_FORMAT_ERROR,
    #         error_data=f'\'operation\': {api.operation} 操作不需要parameter参数',
    #     )

    pk_count = 0
    for param in parameters:
        param_type = param.get('type')
        if param_type not in Parameter.TYPES:
            """未定义的参数类型"""
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data=f'\'type\': {param_type} 不是合法的类型',
            )

        if (
            param_type in (Parameter.TYPE_PAGE_SIZE, Parameter.TYPE_PAGE_IDX)
            and api.operation != Api.OPERATION_LIST
        ):
            """不是查询操作，不应该定义分页参数"""
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data=f'\'operation\': {api.operation} 操作不需要分页参数',
            )

        if param_type == Parameter.TYPE_PK:
            if api.operation in (
                Api.OPERATION_RETRIEVE,
                Api.OPERATION_UPDATE,
                Api.OPERATION_REPLACE,
                Api.OPERATION_DELETE,
            ):
                pk_count += 1
            else:
                """修改、删除、详情以外的操作，不需要主键"""
                raise exceptions.BusinessException(
                    error_code=exceptions.PARAMETER_FORMAT_ERROR,
                    error_data=f'\'operation\': {api.operation} 操作不需要主键参数',
                )

        param_model = Parameter()
        param_model.api = api
        param_model.name = param.get('name')
        param_model.desc = param.get('desc')
        param_model.type = param_type
        param_model.required = param.get('required')
        if 'default' in param:
            param_model.default = param.get('default')

        param_model.save()

    if (pk_count != 1) and api.operation in (
        Api.OPERATION_RETRIEVE,
        Api.OPERATION_UPDATE,
        Api.OPERATION_REPLACE,
        Api.OPERATION_DELETE,
    ):
        """修改、删除、详情，必须有主键"""
        raise exceptions.BusinessException(
            error_code=exceptions.PARAMETER_FORMAT_ERROR,
            error_data=f'\'operation\': {api.operation} 操作有且只能有一个主键参数',
        )


def save_display_fields(api, fields, is_create):
    if not is_create:
        DisplayField.objects.filter(api__id=api.id).delete()

    if not fields:
        return

    if api.operation not in (
        api.OPERATION_LIST,
        api.OPERATION_RETRIEVE,
        api.OPERATION_CREATE,
        api.OPERATION_UPDATE,
        api.OPERATION_REPLACE,
    ):
        raise exceptions.BusinessException(
            error_code=exceptions.PARAMETER_FORMAT_ERROR,
            error_data=f'\'operation\': {api.operation} 操作不需要display-fields',
        )

    for field in fields:
        field_model = DisplayField()
        field_model.api = api
        if isinstance(field, str):
            field_model.name = field
        elif isinstance(field, dict):
            field_model.name = field.get('name')
        else:
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data='display-fields的格式不对',
            )
        field_model.save()


def save_set_fields(api, fields, is_create):
    if not is_create:
        SetField.objects.filter(api__id=api.id).delete()

    if not fields:
        return

    if api.operation not in (
        api.OPERATION_CREATE,
        api.OPERATION_UPDATE,
        api.OPERATION_REPLACE,
        api.OPERATION_UPDATE_BY_CONDITION,
    ):
        raise exceptions.BusinessException(
            error_code=exceptions.PARAMETER_FORMAT_ERROR,
            error_data=f'\'operation\': {api.operation} 操作不需要set-fields',
        )

    for field in fields:
        field_model = SetField()
        field_model.api = api
        if isinstance(field, list) and len(field) == 2:
            field_model.name = field[0]
            field_model.value = field[1]
        elif isinstance(field, dict):
            field_model.name = field.get('name')
            if 'value' in field:
                field_model.value = field.get('value')
            else:
                if api.operation in (
                    api.OPERATION_CREATE,
                    api.OPERATION_UPDATE,
                    api.OPERATION_REPLACE,
                    api.OPERATION_UPDATE_BY_CONDITION,
                ):
                    raise exceptions.BusinessException(
                        error_code=exceptions.PARAMETER_FORMAT_ERROR,
                        error_data=f'\'operation\': {api.operation} 操作，必须有列值set-fields.value',
                    )
        else:
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR, error_data='set-fields的格式不对'
            )
        field_model.save()


def save_filters(api, filters, is_create):
    if not is_create:
        Filter.objects.filter(api__id=api.id).delete()

    if not filters:
        if api.operation in (
            api.OPERATION_DELETE_BY_CONDITION,
            api.OPERATION_UPDATE_BY_CONDITION,
        ):
            if api.operation == api.OPERATION_DELETE_BY_CONDITION:
                action = '删除'
            else:
                action = '更新'

            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data=f'\'operation\': {api.operation} 操作不允许无条件{action}，必须有filters条件',
            )
        return

    if api.operation not in (
        api.OPERATION_LIST,
        api.OPERATION_UPDATE_BY_CONDITION,
        api.OPERATION_DELETE_BY_CONDITION,
    ):
        raise exceptions.BusinessException(
            error_code=exceptions.PARAMETER_FORMAT_ERROR,
            error_data=f'\'operation\': {api.operation} 操作不需要filters条件',
        )

    for filter in filters:
        save_one_filter(api, filter)


def save_one_filter(api, filter, parent=None):
    if 'children' in filter:
        filter_model = Filter()
        filter_model.api = api
        filter_model.type = Filter.TYPE_CONTAINER
        if parent:
            filter_model.parent = parent
            filter_model.layer = parent.layer + 1
        else:
            filter_model.layer = 0
        filter_model.operator = filter.get('operator')
        filter_model.save()

        children = filter.get('children')
        for child in children:
            save_one_filter(api, child, filter_model)
    else:
        filter_model = Filter()
        filter_model.api = api
        filter_model.type = Filter.TYPE_CHILD
        if parent:
            filter_model.parent = parent
            filter_model.layer = parent.layer + 1
        else:
            filter_model.layer = 0
        filter_model.field = filter.get('field')
        filter_model.operator = filter.get('operator')
        if 'value' in filter:
            filter_model.value = filter.get('value')
        filter_model.save()


def show_api(slug):
    api = Api.objects.filter(slug=slug).first()
    expand_fields = ['parameter_set', 'displayfield_set', 'setfield_set']
    serializer_class = multiple_create_serializer_class(Api, expand_fields)
    serializer = serializer_class(api)
    result = serializer.data

    filter_result = get_filters_json(api)
    result['filter'] = filter_result

    return result


def queryset_to_json(queryset, expand_fields, exclude_fields):
    serializer_class = multiple_create_serializer_class(
        queryset.model, expand_fields=expand_fields, exclude_fields=exclude_fields
    )
    serializer = serializer_class(queryset, many=True)
    return serializer.data


def get_filters_json(api):
    max_layer = Filter.objects.filter(api__id=api.id).aggregate(max=Max('layer'))['max']
    max_layer = max_layer or 0
    expand_fields = []
    exclude_fields = []
    for i in range(max_layer):
        if i == 0:
            expand_fields.append('children')
        else:
            expand_fields.append(expand_fields[-1] + '.children')
    queryset = Filter.objects.filter(api__id=api.id, parent__isnull=True)
    return queryset_to_json(queryset, expand_fields, exclude_fields)
