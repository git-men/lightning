import random
import factory
from factory import fuzzy
from faker import Faker

from blog.models import Tag, Category, Article
from member.factory import AuthorFactory


faker = Faker()
zh_faker = Faker(locale='zh_CN')


class TagFactory(factory.DjangoModelFactory):

    name = factory.Faker('word', 'zh_CN')

    class Meta:
        model = Tag


class CategoryFactory(factory.DjangoModelFactory):

    name = factory.Faker('word')
    show = factory.Faker('pybool')

    @factory.lazy_attribute
    def parent(self):
        if faker.pybool():
            return CategoryFactory(parent=None)

    class Meta:
        model = Category


class ArticleFactory(factory.DjangoModelFactory):

    title = factory.Faker('company')
    index_pic = 'https://gw.alipayobjects.com/zos/rmsportal/mqaQswcyDLcXyDKnZfES.png'
    is_public = factory.Faker('pybool')
    author = factory.SubFactory(AuthorFactory)

    @factory.lazy_attribute
    def summary(self):
        return zh_faker.paragraph()[:45]

    @factory.lazy_attribute
    def content(self):
        return ''.join(list(zh_faker.paragraphs()))

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        instance = super()._create(model_class, *args, **kwargs)

        if Tag.objects.count() < 100:
            TagFactory.create_batch(100 - Tag.objects.count())

        tag_random = random.randint(1, 95)

        instance.tags.add(
            *Tag.objects.all()[tag_random:tag_random+3]
        )

        if Category.objects.count() < 100:
            CategoryFactory.create_batch(100 - Category.objects.count())

        category_random = random.randint(1, 95)
        instance.categories.add(
            *Category.objects.all()[category_random:category_random+3]
        )
        return instance

    class Meta:
        model = Article
