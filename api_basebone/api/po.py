from django.apps import apps

from api_basebone.api import const
from api_basebone.core import exceptions


class ApiPO:
    # def __init__(self):
    #     pass

    def __str__(self):
        return self.slug

    def __getitem__(self, k):
        return getattr(self, k)

    def __setitem__(self, k, v):
        return setattr(self, k, v)

    @property
    def method(self):
        '''API提交的方法'''
        return const.METHOD_MAP.get(self.operation)

    @property
    def expand_fields_set(self):
        '''展开字段的集合'''
        if self.expand_fields:
            return set(self.expand_fields.replace(' ', '').split(','))
        else:
            return set()

    def method_equal(self, method):
        return method.lower() in self.method

    def get_order_by_fields(self):
        if self.ordering:
            return self.ordering.replace(' ', '').split(',')
        else:
            return set()


class ParameterPO:
    # def __init__(self):
    #     pass

    def is_special_defined(self):
        """自定义参数，用于特殊用途"""
        return self.type in const.SPECIAL_TYPES

    def __getitem__(self, k):
        return getattr(self, k)

    def __setitem__(self, k, v):
        return setattr(self, k, v)

    def __str__(self):
        return self.name


class DisplayFieldPO:
    # def __init__(self):
    #     pass

    def __str__(self):
        return self.name

    def __getitem__(self, k):
        return getattr(self, k)

    def __setitem__(self, k, v):
        return setattr(self, k, v)


class SetFieldPO:
    # def __init__(self):
    #     pass

    def __str__(self):
        return self.name

    def __getitem__(self, k):
        return getattr(self, k)

    def __setitem__(self, k, v):
        return setattr(self, k, v)


class FilterPO:
    # def __init__(self):
    #     pass

    def __getitem__(self, k):
        return getattr(self, k)

    def __setitem__(self, k, v):
        return setattr(self, k, v)

    def toDict(self):
        d = {}
        d['type'] = self.type
        # if hasattr(self, 'parent'):
        #     d['parent'] = self.parent
        if hasattr(self, 'field'):
            d['field'] = self.field
        d['operator'] = self.operator
        if hasattr(self, 'value'):
            d['value'] = self.value
        d['layer'] = self.layer
        if hasattr(self, 'children'):
            d['children'] = []
            for f in self.children:
                child = f.toDict()
                d['children'].append(child)
        return d

    def __str__(self):
        if self.type == const.FILTER_TYPE_CONTAINER:
            return f'{self.operator}'
        elif self.type == const.FILTER_TYPE_CHILD:
            return f'{self.field} {self.operator} {self.value}'
        else:
            return ''


def loadAPIFromConfig(config):
    api = ApiPO()
    slug = config.get('slug', '')
    api.slug = slug
    api.config = config
    api.app = config.get('app')
    api.model = config.get('model')
    try:
        model_class = apps.get_model(api.app, api.model)
    except LookupError:
        raise exceptions.BusinessException(
            error_code=exceptions.PARAMETER_FORMAT_ERROR,
            error_data=f'{api.app}__{api.model} 不是有效的model',
        )
    api.operation = config.get('operation')
    if api.operation not in const.OPERATIONS:
        raise exceptions.BusinessException(
            error_code=exceptions.PARAMETER_FORMAT_ERROR,
            error_data=f'\'operation\': {api.operation} 不是合法的操作',
        )
    if 'summary' in config:
        api.summary = config['summary']
    if 'demo' in config:
        api.demo = config['demo']
    if 'ordering' in config:
        if isinstance(config['ordering'], list):
            api.ordering = ",".join(config['ordering'])
        else:
            api.ordering = config['ordering']
    if 'expand_fields' in config:
        if isinstance(config['expand_fields'], list):
            api.expand_fields = ",".join(config['expand_fields'])
        else:
            api.expand_fields = config['expand_fields']
    if 'func_name' in config:
        api.func_name = config['func_name']
    else:
        if api.operation == const.OPERATION_FUNC:
            """云函数api，却没有函数名"""
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data=f'\'operation\': {api.operation} 操作，必须有func_name函数名',
            )

    api.parameter = loadParametersFromConfig(api, config.get('parameter'))
    api.displayfield = loadDisplayFieldFromConfig(api, config.get('displayfield'))
    api.setfield = loadSetFieldFromConfig(
        api, config.get('setfield'), model_class, api.parameter
    )
    api.filter = loadFilterFromConfig(api, config.get('filter'))
    return api


def loadParametersFromConfig(api, parameters, parent=None):
    if not parameters:
        return []

    pk_count = 0
    po_list = []
    for param in parameters:
        param_type = param.get('type')
        if param_type not in const.TYPES:
            """未定义的参数类型"""
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data=f'\'type\': {param_type} 不是合法的类型',
            )

        if (
            param_type in (const.TYPE_PAGE_SIZE, const.TYPE_PAGE_IDX)
            and api.operation != const.OPERATION_LIST
        ):
            """不是查询操作，不应该定义分页参数"""
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data=f'\'operation\': {api.operation} 操作不需要分页参数',
            )

        if param_type == const.TYPE_PK:
            if api.operation in (
                const.OPERATION_RETRIEVE,
                const.OPERATION_UPDATE,
                const.OPERATION_REPLACE,
                const.OPERATION_DELETE,
            ):
                pk_count += 1
            else:
                """修改、删除、详情以外的操作，不需要主键"""
                raise exceptions.BusinessException(
                    error_code=exceptions.PARAMETER_FORMAT_ERROR,
                    error_data=f'\'operation\': {api.operation} 操作不需要主键参数',
                )

        if parent and (param_type in const.SPECIAL_TYPES):
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data='复杂数据类型不允许包含主键、分页等特殊类型',
            )

        po = ParameterPO()
        po.api = api
        if parent:
            po.parent = parent
            po.layer = parent.layer + 1
        else:
            po.layer = 0
        po.name = param.get('name')
        po.desc = param.get('desc')
        po.type = param_type
        po.required = param.get('required')

        if 'is_array' in param:
            po.is_array = param.get('is_array')
        if 'default' in param:
            po.default = param.get('default')

        if 'children' in param:
            loadParametersFromConfig(api, param['children'], po)
        po_list.append(po)

    if (pk_count != 1) and api.operation in (
        const.OPERATION_RETRIEVE,
        const.OPERATION_UPDATE,
        const.OPERATION_REPLACE,
        const.OPERATION_DELETE,
    ):
        """修改、删除、详情，必须有主键"""
        raise exceptions.BusinessException(
            error_code=exceptions.PARAMETER_FORMAT_ERROR,
            error_data=f'\'operation\': {api.operation} 操作有且只能有一个主键参数',
        )

    return po_list


def loadDisplayFieldFromConfig(api, fields):
    if not fields:
        return []

    if api.operation not in (
        const.OPERATION_LIST,
        const.OPERATION_RETRIEVE,
        const.OPERATION_CREATE,
        const.OPERATION_UPDATE,
        const.OPERATION_REPLACE,
    ):
        raise exceptions.BusinessException(
            error_code=exceptions.PARAMETER_FORMAT_ERROR,
            error_data=f'\'operation\': {api.operation} 操作不需要display-fields',
        )

    po_list = []
    for field in fields:
        po = DisplayFieldPO()
        po.api = api
        if isinstance(field, str):
            po.name = field
        elif isinstance(field, dict):
            po.name = field.get('name')
        else:
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data='display-fields的格式不对',
            )
        po_list.append(po)
    return po_list


def loadSetFieldFromConfig(api, fields, model_class, param_list):
    if api.operation not in (
        const.OPERATION_CREATE,
        const.OPERATION_UPDATE,
        const.OPERATION_REPLACE,
        const.OPERATION_UPDATE_BY_CONDITION,
    ):
        if fields:
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data=f'\'operation\': {api.operation} 操作不需要set-fields',
            )
        else:
            return []

    if not fields:
        fields = [
            [p.name, f'${{{p.name}}}'] for p in param_list if not p.is_special_defined()
        ]

    po_list = []
    meta_filed_names = [f.name for f in model_class._meta.get_fields()]
    for field in fields:
        po = SetFieldPO()
        po.api = api
        if isinstance(field, list) and len(field) == 2:
            po.name = field[0]
            po.value = field[1]
        elif isinstance(field, dict):
            po.name = field.get('name')
            if 'value' in field:
                po.value = field.get('value')
            else:
                if api.operation in (
                    const.OPERATION_CREATE,
                    const.OPERATION_UPDATE,
                    const.OPERATION_REPLACE,
                    const.OPERATION_UPDATE_BY_CONDITION,
                ):
                    raise exceptions.BusinessException(
                        error_code=exceptions.PARAMETER_FORMAT_ERROR,
                        error_data=f'\'operation\': {api.operation} 操作，必须有列值set-fields.value',
                    )
        else:
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR, error_data='set-fields的格式不对'
            )

        if po.name not in meta_filed_names:
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data=f'{api.app}__{api.model} 没有属性{po.name}',
            )
        po_list.append(po)

    return po_list


def loadFilterFromConfig(api, filters):
    if not filters:
        if api.operation in (
            const.OPERATION_DELETE_BY_CONDITION,
            const.OPERATION_UPDATE_BY_CONDITION,
        ):
            if api.operation == const.OPERATION_DELETE_BY_CONDITION:
                action = '删除'
            else:
                action = '更新'

            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data=f'\'operation\': {api.operation} 操作不允许无条件{action}，必须有filters条件',
            )
        return []

    if api.operation not in (
        const.OPERATION_LIST,
        const.OPERATION_UPDATE_BY_CONDITION,
        const.OPERATION_DELETE_BY_CONDITION,
    ):
        raise exceptions.BusinessException(
            error_code=exceptions.PARAMETER_FORMAT_ERROR,
            error_data=f'\'operation\': {api.operation} 操作不需要filters条件',
        )

    po_list = []
    for filter in filters:
        po = loadOneFilter(api, filter)
        po_list.append(po)

    return po_list


def loadOneFilter(api, filter, parent=None):
    if 'children' in filter:
        po = FilterPO()
        po.api = api
        po.type = const.FILTER_TYPE_CONTAINER
        if parent:
            po.parent = parent
            po.layer = parent.layer + 1
        else:
            po.layer = 0
        po.operator = filter.get('operator')

        children = filter.get('children')
        po.children = []
        for child in children:
            child_po = loadOneFilter(api, child, po)
            po.children.append(child_po)
    else:
        po = FilterPO()
        po.api = api
        po.type = const.FILTER_TYPE_CHILD
        if parent:
            po.parent = parent
            po.layer = parent.layer + 1
        else:
            po.layer = 0
        po.field = filter.get('field')
        po.operator = filter.get('operator')
        if 'value' in filter:
            po.value = filter.get('value')

    return po