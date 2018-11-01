from django.db import models


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
