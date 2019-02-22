import csv
from collections import OrderedDict
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.writer.excel import save_virtual_workbook

from api_basebone.core import gmeta
from api_basebone.utils.gmeta import get_gmeta_config_by_key


def get_fields(model):
    default_fields = OrderedDict()
    for item in model._meta.get_fields():
        if item.concrete and not item.many_to_many:
            default_fields[item.name] = item.verbose_name

    export_fields = get_gmeta_config_by_key(model, gmeta.GMETA_MANAGE_EXPORT_FIELDS)
    if not isinstance(export_fields, (list, tuple)) or not export_fields:
        return default_fields

    fields = OrderedDict()
    for item in export_fields:
        if isinstance(item, tuple):
            fields[item[0]] = item[1]
        else:
            fields[item] = default_fields[item]
    return fields


def row_data(fields, data):
    return [data[key] for key in fields.keys()]


def csv_render(model, queryset, serializer_class):
    """渲染数据"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="export.csv"'

    fields = get_fields(model)
    verbose_names = fields.values()

    writer = csv.writer(response)
    writer.writerow(verbose_names)

    for instance in queryset.iterator():
        instance_data = serializer_class(instance).data
        writer.writerow(row_data(fields, instance_data))
    return response


class ExcelResponse(HttpResponse):

    def __init__(self, model, queryset, serializer_class, *args, **kwargs):
        self.model = model
        self.queryset = queryset
        self.serializer_class = serializer_class
        self.output_filename = f'{model._meta.model_name}.excel'
        self.worksheet_name = 'Sheet 1'

        super().__init__(model.objects.all(), *args, **kwargs)

    @property
    def content(self):
        return b''.join(self._container)

    @content.setter
    def content(self, value):
        self['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        self['Content-Disposition'] = 'attachment; filename={}.xlsx'.format(self.output_filename)

        workbook = self.build_excel()
        workbook = save_virtual_workbook(workbook)
        self._container = [self.make_bytes(workbook)]

    def build_excel(self, *args, **kwargs):
        fields = get_fields(self.model)
        headers = fields.values()

        workbook = Workbook(write_only=True)
        workbook.guess_types = True
        worksheet = workbook.create_sheet(title=self.worksheet_name)
        worksheet.append(headers)

        serializer_class = self.serializer_class
        for instance in self.queryset.iterator():
            instance_data = serializer_class(instance).data
            worksheet.append(row_data(fields, instance_data))
        return workbook
