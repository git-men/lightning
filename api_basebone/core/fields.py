import json
from django.db import models
from jsonfield import JSONField as OriginJSONField
from api_basebone.core.object_model import ObjectModel


class BoneRichTextField(models.TextField):
    """富文本字段"""

    def get_bsm_internal_type(self):
        return 'BoneRichTextField'


class BoneImageCharField(models.CharField):
    """存储图片的数据，以字符串的形式"""

    def get_bsm_internal_type(self):
        return 'BoneImageCharField'


class BoneImageUrlField(models.URLField):
    """存储图片链接"""

    def get_bsm_internal_type(self):
        return 'BoneImageUrlField'


class BoneFileUrlField(models.URLField):
    """存储文件链接"""

    def get_bsm_internal_type(self):
        return 'BoneFileUrlField'


class JSONField(OriginJSONField):
    def get_prep_value(self, value):
        """把对象转换为字符串"""
        if self.null and value is None:
            return None

        if isinstance(value, (dict, list)):
            return json.dumps(value, **self.dump_kwargs)
        return value

    def from_db_value(self, value, expression, connection, context):
        if isinstance(value, str):
            return json.loads(value)
        return value


class ObjectField(JSONField):
    """
    """

    def __init__(self, object_model: ObjectModel = None, **kwargs):
        self.object_model = object_model or ObjectModel()
        super(ObjectField, self).__init__(**kwargs)

    def get_bsm_internal_type(self):
        return 'JsonObjectField'

    def from_db_value(self, value, expression, connection, context):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except:
                return {}
        return value


class ArrayField(JSONField):

    def __init__(self, item_model: ObjectModel = None, item_type: str = 'string', **kwargs):
        self.item_model = item_model or ObjectModel()
        self.item_type = item_type
        super(ArrayField, self).__init__(**kwargs)

    def get_bsm_internal_type(self):
        return 'JsonArrayField'

    def from_db_value(self, value, expression, connection, context):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except:
                return {}
        return value
