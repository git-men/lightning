from rest_framework import serializers
from member.models import Author
from utils import uuid4


class CreateUpdateForm(serializers.ModelSerializer):

    class Meta:
        model = Author
        fields = ('name', 'city', 'gender', 'age')

    def create(self, validated_data):
        validated_data['username'] = uuid4()
        return Author.objects.create(**validated_data)
