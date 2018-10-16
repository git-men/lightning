"""
涉及到 model._meta 相关的工具方法
"""

from django.contrib.auth import get_user_model


def get_related_model_field(model, related_model):
    """
    model 中的关系字段是否指向 related_model

    例如，文章 Article 中的有一个字段
    """
    for f in model._meta.get_fields():
        if f.is_relation and f.concrete:
            if f.model is related_model:
                return f
