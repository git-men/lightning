from rest_framework import serializers

from blog.models import Tag, Category, Article


class tagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class categorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = '__all__'


class articleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Article
        fields = '__all__'
