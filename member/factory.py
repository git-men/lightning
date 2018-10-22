import random
import factory
from factory import fuzzy

from member.models import Author


class AuthorFactory(factory.DjangoModelFactory):

    username = factory.Faker('md5')
    password = factory.Faker('md5')
    name = factory.Faker('name', locale='zh_CN')
    city = factory.Faker('city', locale='zh_CN')
    gender = fuzzy.FuzzyChoice(choices=dict(Author.GENDER_CHOICES))

    @factory.lazy_attribute
    def age(self):
        return random.randint(1, 100)

    class Meta:
        model = Author
