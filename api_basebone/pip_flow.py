"""
数据的操作

通过一系列的操作，对数据进行清洗
"""
from api_basebone.utils import meta


def add_login_user_data(view, data):
    """
    给数据添加上用户数据

    对于字段，这里分：正向的关系字段，反向的关系字段
    """
    app_label, model_name, model = view.app_label, view.model_slug, view.model
    relation_field = meta.get_reverse_fields(model)

    