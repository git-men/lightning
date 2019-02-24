from rest_framework import fields


class CharIntegerField(fields.IntegerField):

    def to_representation(self, value):
        return f'{value}'
