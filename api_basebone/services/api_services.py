from django.db.models import Max

from api_basebone.core import exceptions
from api_basebone.restful.serializers import (
    # create_serializer_class,
    multiple_create_serializer_class,
)

from api_basebone.models import Api, Parameter, Field, Filter


def save_api(config):
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
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data=f'\'operation\': {api.operation} 操作，必须有func_name函数名',
            )
    api.save()

    save_parameters(api, config.get('parameters'), is_create)

    save_fields(api, config.get('fields'), is_create)

    save_filters(api, config.get('filters'), is_create)


def save_parameters(api, parameters, is_create):
    if not is_create:
        Parameter.objects.filter(api__id=api.id).delete()

    if not parameters:
        return

    if api.operation in (api.OPERATION_CREATE,):
        raise exceptions.BusinessException(
            error_code=exceptions.PARAMETER_FORMAT_ERROR,
            error_data=f'\'operation\': {api.operation} 操作不需要parameter参数',
        )

    for param in parameters:
        param_type = param.get('type')
        if param_type not in Parameter.TYPES:
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data=f'\'type\': {param_type} 不是合法的类型',
            )

        if (
            param_type in (Parameter.TYPE_PAGE_SIZE, Parameter.TYPE_PAGE_IDX)
            and api.operation != Api.OPERATION_LIST
        ):
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data=f'\'operation\': {api.operation} 操作不需要分页参数',
            )

        if param_type == Parameter.TYPE_PK and api.operation not in (
            Api.OPERATION_RETRIEVE,
            Api.OPERATION_UPDATE,
            Api.OPERATION_REPLACE,
            Api.OPERATION_DELETE,
        ):
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data=f'\'operation\': {api.operation} 操作不需要主键参数',
            )

        if param_type != Parameter.TYPE_PK and api.operation in (
            Api.OPERATION_RETRIEVE,
            Api.OPERATION_UPDATE,
            Api.OPERATION_REPLACE,
            Api.OPERATION_DELETE,
        ):
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data=f'\'operation\': {api.operation} 操作只能有主键参数',
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


def save_fields(api, fields, is_create):
    if not is_create:
        Field.objects.filter(api__id=api.id).delete()

    if not fields:
        return

    if api.operation not in (api.OPERATION_LIST, api.OPERATION_UPDATE_BY_CONDITION):
        raise exceptions.BusinessException(
            error_code=exceptions.PARAMETER_FORMAT_ERROR,
            error_data=f'\'operation\': {api.operation} 操作不需要fields',
        )

    for field in fields:
        field_model = Field()
        field_model.api = api
        if isinstance(field, str):
            field_model.name = field
        elif isinstance(field, list) and len(field) == 2:
            field_model.name = field[0]
            field_model.value = field[1]
        elif isinstance(field, dict):
            field_model.name = field.get('name')
            if 'value' in field:
                field_model.value = field.get('value')
            else:
                if api.operation == api.OPERATION_UPDATE_BY_CONDITION:
                    raise exceptions.BusinessException(
                        error_code=exceptions.PARAMETER_FORMAT_ERROR,
                        error_data=f'\'operation\': {api.operation} 操作，必须有列值fields.value',
                    )
        else:
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR, error_data='fields的格式不对'
            )
        field_model.save()


def save_filters(api, filters, is_create):
    if not is_create:
        Filter.objects.filter(api__id=api.id).delete()

    if not filters:
        if api.operation == api.OPERATION_DELETE_BY_CONDITION:
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data=f'\'operation\': {api.operation} 操作不允许无条件删除，必须有filters条件',
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
    expand_fields = ['parameter_set', 'field_set']
    serializer_class = multiple_create_serializer_class(Api, expand_fields)
    serializer = serializer_class(api)
    result = serializer.data

    # result_param = show_parameters(api)
    # if result_param:
    #     result['parameters'] = result_param

    # field_param = show_fields(api)
    # if field_param:
    #     result['fields'] = field_param

    filter_result = get_filters_json(api)
    if filter_result:
        result['filter'] = filter_result

    return result


def queryset_to_json(queryset, expand_fields, exclude_fields):
    serializer_class = multiple_create_serializer_class(
        queryset.model, expand_fields=expand_fields, exclude_fields=exclude_fields
    )
    serializer = serializer_class(queryset, many=True)
    return serializer.data


# def show_parameters(api):
#     expand_fields = []
#     queryset = Parameter.objects.filter(api__id=api.id)
#     return queryset_to_json(queryset, expand_fields)


# def show_fields(api):
#     expand_fields = []
#     queryset = Field.objects.filter(api__id=api.id)
#     return queryset_to_json(queryset, expand_fields)


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
