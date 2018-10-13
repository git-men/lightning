from blog.factory import ArticleFactory


def create_data():
    ArticleFactory.create_batch(144)
