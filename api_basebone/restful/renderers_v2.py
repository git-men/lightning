import codecs
import csv
from collections import OrderedDict

from django.http import HttpResponse
from pydash import objects

from api_basebone.core import gmeta
from api_basebone.core.decorators import BSM_ADMIN_COMPUTED_FIELDS_MAP
from api_basebone.utils.gmeta import get_attr_in_gmeta_class, get_gmeta_config_by_key
from api_basebone.utils.meta import get_all_relation_fields
from api_basebone.utils.timezone import local_timestamp


def get_no_concrete_or_m2m(model):
    """获取反向或者对对多字段名称列表"""
    return [
        item.name
        for item in get_all_relation_fields(model)
        if not item.concrete or item.many_to_many
    ]


def get_merge_fields(model, serializer_class, export_config):
    """
    针对合并的情况下，返回对应的字段列表和字段名称

    获取指定模型的反向字段和多对多字段列表

    返回的是 {
        field_nane: field_verbose_name
    }
    """
    default_fields = OrderedDict()

    # 指定导出的字段
    export_fields = export_config['fields']

    for item in model._meta.get_fields():
        if export_fields:
            if not item.concrete:
                default_fields[item.name] = item.related_model._meta.verbose_name
            else:
                default_fields[item.name] = item.verbose_name
        else:
            if item.concrete and not item.many_to_many:
                default_fields[item.name] = item.verbose_name

    # 添加 model GMeta 下声明的计算属性字段
    computed_fields = get_attr_in_gmeta_class(model, gmeta.GMETA_COMPUTED_FIELDS, [])
    for field in computed_fields:
        default_fields[field['name']] = field.get('display_name', field['name'])

    # 添加 admin 中声明的计算属性字段
    # 添加 model GMeta 下声明的计算属性字段
    admin_computed_fields = getattr(model, BSM_ADMIN_COMPUTED_FIELDS_MAP, {})
    for key, value in admin_computed_fields.items():
        default_fields[key] = value['display_name']

    if not isinstance(export_fields, (list, tuple)) or not export_fields:
        return default_fields

    fields = OrderedDict()

    # 反向和多对多的字段列表
    no_concrete_or_m2m_fields = get_no_concrete_or_m2m(model)

    for item in export_fields:
        # 针对多对多或者反向做对应的处理
        item_str = item[0] if isinstance(item, (list, tuple)) else item
        item_split = item_str.split('.')
        if item_split[0] in no_concrete_or_m2m_fields:
            fields[item_split[0]] = default_fields[item_split[0]]
            continue

        if isinstance(item, (list, tuple)):
            fields[item[0]] = item[1]
        else:
            fields[item] = default_fields[item]
    return fields


def row_data_merge(model, fields, data, export_fields):
    """获取不合并的行数据"""
    # return [objects.get(data, key) for key in fields.keys()]

    result = []
    # 反向和多对多的字段列表
    no_concrete_or_m2m_fields = get_no_concrete_or_m2m(model)
    for key in fields.keys():
        if key in no_concrete_or_m2m_fields:
            if not export_fields:
                result.append('')
                continue

            inner_data = objects.get(data, key)
            if not inner_data:
                result.append('')
                continue

            inner_field_dict = {}
            for export_item in export_fields:
                if isinstance(export_item, tuple):
                    if not export_item[0].startswith(key):
                        continue
                else:
                    if not export_item.startswith(key):
                        continue
                    inner_item_split = export_item.split('.', 1)
                    related_model = model._meta.get_field(key).related_model
                    inner_field_dict[inner_item_split[1]] = related_model._meta.get_field(
                        inner_item_split[1]
                    ).verbose_name

            inner_multiple_row = []
            for item in inner_data:
                inner_multiple_row.append(
                    ' '.join(
                        [
                            '{}: {}'.format(value, item.get(key, ''))
                            for key, value in inner_field_dict.items()
                        ]
                    )
                )
            result.append('\n'.join(inner_multiple_row))

        else:
            result.append(objects.get(data, key))
    return result


def get_no_merge_fields(model, serializer_class, export_config):
    """
    针对不合并的情况下，返回对应的字段列表和字段名称

    获取指定模型的反向字段和多对多字段列表

    返回的是 {
        field_nane: field_verbose_name
    }
    """
    default_fields = OrderedDict()

    # 指定导出的字段
    export_fields = export_config['fields']

    for item in model._meta.get_fields():
        if export_fields:
            if not item.concrete:
                default_fields[item.name] = item.related_model._meta.verbose_name
            else:
                default_fields[item.name] = item.verbose_name
        else:
            if item.concrete and not item.many_to_many:
                default_fields[item.name] = item.verbose_name

    # 添加 model GMeta 下声明的计算属性字段
    computed_fields = get_attr_in_gmeta_class(model, gmeta.GMETA_COMPUTED_FIELDS, [])
    for field in computed_fields:
        default_fields[field['name']] = field.get('display_name', field['name'])

    # 添加 admin 中声明的计算属性字段
    # 添加 model GMeta 下声明的计算属性字段
    admin_computed_fields = getattr(model, BSM_ADMIN_COMPUTED_FIELDS_MAP, {})
    for key, value in admin_computed_fields.items():
        default_fields[key] = value['display_name']

    if not isinstance(export_fields, (list, tuple)) or not export_fields:
        return default_fields

    fields = OrderedDict()

    # 反向和多对多的字段列表
    no_concrete_or_m2m_fields = get_no_concrete_or_m2m(model)

    for item in export_fields:

        if isinstance(item, (list, tuple)):
            fields[item[0]] = item[1]
        else:
            item_split = item.split('.')
            if item_split[0] in no_concrete_or_m2m_fields:
                relation_field = model._meta.get_field(item_split[0])
                parent_verbose_name = getattr(relation_field, 'verbose_name', '')
                if not parent_verbose_name:
                    parent_verbose_name = relation_field.related_model.__name__

                child_relation_field = relation_field.related_model._meta.get_field(
                    item_split[1]
                )

                fields[item] = '{}.{}'.format(
                    parent_verbose_name, child_relation_field.verbose_name
                )
            else:
                fields[item] = default_fields[item]
    return fields


def row_data_no_merge(model, fields, data, export_fields, nest_list_fields, writer):
    """不合并行数据的处理"""

    result = []
    max_nest_list = 0
    print(nest_list_fields)
    for nest_key in nest_list_fields:
        if nest_key in data:
            nest_list_data = data.get(nest_key, [])
            if not nest_list_data:
                continue
            clean_data_list = []

            for item in nest_list_data:
                item_data_dict = {
                    f'{nest_key}.{key}': value for key, value in item.items()
                }
                clean_data_list.append(item_data_dict)
            data[nest_key] = clean_data_list
            if len(clean_data_list) > max_nest_list:
                max_nest_list = len(clean_data_list)

    print(max_nest_list, 'this is max nest list')

    if max_nest_list == 0:
        writer.writerow([objects.get(data, key) for key in fields.keys()])
    else:
        for index in range(0, max_nest_list):
            row_data = []
            for key in fields.keys():
                key_split_str = key.split('.')[0]
                if key_split_str in nest_list_fields:
                    try:
                        value = data[key_split_str][index].get(key)
                    except Exception:
                        value = ''
                else:
                    value = objects.get(data, key) if index == 0 else ''
                row_data.append(value)
            writer.writerow(row_data)
    return result


def csv_render(model, queryset, serializer_class, export_config=None):
    """渲染数据"""
    app_label, model_name = model._meta.app_label, model._meta.model_name
    file_name = f'{app_label}-{model_name}-{local_timestamp()}'

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{file_name}.csv"'

    response.write(codecs.BOM_UTF8)
    writer = csv.writer(response)

    if export_config['merge_bref']:
        fields = get_merge_fields(model, serializer_class, export_config)
        verbose_names = fields.values()

        writer.writerow(verbose_names)

        # 处理结果集
        queryset_iter = queryset if isinstance(queryset, list) else queryset.all()

        for instance in queryset_iter:
            instance_data = serializer_class(instance).data

            # 写入一行数据
            writer.writerow(
                row_data_merge(model, fields, instance_data, export_config['fields'])
            )
    else:
        # 不合并的场景
        fields = get_no_merge_fields(model, serializer_class, export_config)
        verbose_names = fields.values()
        writer.writerow(verbose_names)

        # 处理结果集
        queryset_iter = queryset if isinstance(queryset, list) else queryset.all()

        export_fields = export_config['fields']
        no_concrete_or_m2m_fields = get_no_concrete_or_m2m(model)

        nest_list_fields = set()

        if export_fields:
            for item in export_fields:
                item_str = item[0] if isinstance(item, (list, tuple)) else item
                item_split = item_str.split('.')
                if item_split[0] in no_concrete_or_m2m_fields:
                    nest_list_fields.add(item_split[0])

        for instance in queryset_iter:
            instance_data = serializer_class(instance).data

            # 写入一行数据
            row_data_no_merge(
                model,
                fields,
                instance_data,
                export_config['fields'],
                nest_list_fields,
                writer,
            )
    return response
