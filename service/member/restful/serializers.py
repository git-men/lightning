from rest_framework import serializers
from member.models import Author


class AuthorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Author
