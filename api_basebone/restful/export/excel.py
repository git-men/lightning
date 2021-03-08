import openpyxl
import collections
import requests
from tempfile import NamedTemporaryFile
from django.db.models.fields.related import ManyToManyField
from django.db.models.fields.reverse_related import ManyToManyRel, ManyToOneRel
from django.db.models.query import QuerySet
from django.http import HttpResponse

from api_basebone.utils.timezone import local_timestamp
from api_basebone.restful.export.formatter import format

def get_attribute(instance, field_path, formatter=None):
    # 获取对象属性值,并对其进行格式化
    print(f'getting {field_path} from instance: {instance}')
    def _get(obj, field):
        rs = getattr(obj, field, None)
        # 如果是一对多，多对多的refManager，把它all一下。
        opts = obj.__class__._meta
        try:
            field_cls = opts.get_field(field).__class__
        except:  # FIXME 找不到该字段是，可能是计算字段。
            field_cls = None
        if field_cls in [ManyToManyField, ManyToManyRel, ManyToOneRel]:
            return rs.all()
        return rs

    # 逐层获取属性
    result = instance
    paths = field_path.split('.')
    for path in paths:

        # 这里的result可以是Queryset，可以是List
        if isinstance(result, QuerySet) or isinstance(result, list):
            inter = []
            for item in result:
                rs = _get(item, path)
                if isinstance(rs, QuerySet) or isinstance(rs, list):
                    inter += rs
                else:
                    inter.append(rs)
            result = inter
        else:
            result = _get(result, path)
    
    # 格式化
    if not formatter:
        return result
    if isinstance(result, QuerySet) or isinstance(result, list):
        return [format(rs, formatter['type'], formatter['params']) for rs in result]
    return format(result, formatter['type'], formatter['params'])

def export_excel(config, queryset, detail=None):
    """
    导出Excel
    - config: 导出配置
    - queryset: 导出结果集
    - detail: 关联详情数据

    config结构示例：
    {
        "version": "v3",
        "template": "https://xxxx.com/yyy.xlsx",
        "list_start_line": 8,
        "detail_mapping": [{
            "position": "A1",
            "field": "superior.name",
            "formatter": {}
        }],
        "list_mapping": [{
            "column": "A",
            "field": "a", 
            "formatter": {
                "type": "prefix", 
                "params": {
                    "prefix": "姓  名：",
                }
            }, 
        }]
    }

    """
    app_label, model_name = queryset.model._meta.app_label, queryset.model._meta.model_name
    file_name = f'{app_label}-{model_name}-{local_timestamp()}'

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{file_name}.xlsx"'

    if not isinstance(config, dict):
        # 如果不是配置，可能是Key，通过其他方法获取配置内容。
        pass
    use_template = "template" in config
    if use_template:
        # 有模板，通过模板文件的md5值，从临时目录中获取一下。
        data = requests.get(config['template']).content
        with NamedTemporaryFile() as tmp:
            with open(tmp.name + '.xlsx', 'wb') as f:
                f.write(data)
            print('下载的文件：', tmp.name)

        workbook = openpyxl.load_workbook(tmp.name + '.xlsx')
        sheet = workbook.worksheets[0]
    else:
        workbook = openpyxl.Workbook()
        sheet = workbook.active

    detail_mapping = config.get('detail_mapping', [])
    
    list_mapping = config.get('list_mapping', [])
    # 渲染列表
    if list_mapping:
        if use_template:  # 指定模板
            row = config.get('list_start_line', 1)
            end = config.get('list_end_line')
            for instance in queryset:
                for field in list_mapping:
                    sheet[f'{field["column"]}{row}'] = get_attribute(instance, field['field'], field.get('formatter', None))
                row += 1
                
            sheet.delete_rows(row, end - row + 1)
        else:
            row = len(detail_mapping) + 1
            
            # 输出标題
            col = 1
            for field in list_mapping:
                title = field.get('title', '') # FIXME 考虑没有指定Title的情况。
                sheet.cell(row, col, title)
                col += 1
            row += 1

            for instance in queryset:
                col = 1
                for field in list_mapping:
                    sheet.cell(row, col, get_attribute(instance, field['field'], field.get('formatter', None)))
                    col += 1
                row += 1
    
    if detail_mapping:
        # 渲染关联详情
        if use_template:  # 模型指定位置
            for dfield in detail_mapping:
                position = dfield['position']
                if isinstance(position, str):
                    sheet[dfield['position']] = get_attribute(detail, dfield['field'], dfield.get('formatter', None))
                elif isinstance(position, dict):
                    row = position['related_row'] + config.get('list_start_line') + len(queryset) - 1
                    sheet.cell(row, position['column'], get_attribute(detail, dfield['field'], dfield.get('formatter', None)))
        else:  # 自动生成，从第一行起，合并单元格。
            cur = 1
            col_cnt = len(config.get('list_mapping', []))
            for dfield in detail_mapping:
                sheet.merge_cells(start_row=cur, start_column=1, end_row=cur, end_column=col_cnt)
                sheet[f'A{cur}'] = get_attribute(detail, dfield['field'], dfield.get('formatter', None))
                cur += 1

    with NamedTemporaryFile() as tmp:
        workbook.save(tmp.name)
        tmp.seek(0)
        content = tmp.read()
        response.write(content)
    return response
