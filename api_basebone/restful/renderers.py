import csv

from collections import OrderedDict

from django.http import HttpResponse

from openpyxl import Workbook
from openpyxl.writer.excel import save_virtual_workbook

from api_basebone.restful.serializers import create_serializer_class


def get_fields(model):
    result = OrderedDict()
    for i in model._meta.get_fields():
        if i.concrete and not i.many_to_many:
            result[i.name] = i
    return result


def csv_render(model):
    """渲染数据"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="export.csv"'

    serializer_class = create_serializer_class(model)
    serializer = serializer_class(model.objects.all(), many=True)

    fields = get_fields(model)
    verbose_names = [
        value.verbose_name for key, value in fields.items()
    ]

    writer = csv.writer(response)
    writer.writerow(verbose_names)
    for row in serializer.data:
        writer.writerow(row.values())
    return response


class ExcelResponse(HttpResponse):

    def __init__(self, model, *args, **kwargs):
        self.model = model
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
        workbook = self.build_excel(value)
        workbook = save_virtual_workbook(workbook)
        self._container = [self.make_bytes(workbook)]

    def build_excel(self, data):
        fields = get_fields(self.model)
        headers = [value.verbose_name for key, value in fields.items()]

        workbook = Workbook(write_only=True)
        workbook.guess_types = True
        worksheet = workbook.create_sheet(title=self.worksheet_name)
        worksheet.append(headers)

        serializer_class = create_serializer_class(self.model)
        for instance in data.iterator():
            instance_data = serializer_class(instance).data
            instance_data_list = [
                instance_data[key] for key, value in fields.items()
            ]
            worksheet.append(instance_data_list)
        return workbook
