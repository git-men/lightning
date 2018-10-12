from rest_framework import serializers

from api.serializers import BaseModelSerializerMixin
from blog.models import Tag, Category, Article


class tagSerializer(BaseModelSerializerMixin, serializers.ModelSerializer):

    class Meta(BaseModelSerializerMixin.Meta):
        model = Tag


class categorySerializer(BaseModelSerializerMixin, serializers.ModelSerializer):

    class Meta(BaseModelSerializerMixin.Meta):
        model = Category


class articleSerializer(BaseModelSerializerMixin, serializers.ModelSerializer, ):

    class Meta(BaseModelSerializerMixin.Meta):
        model = Article
