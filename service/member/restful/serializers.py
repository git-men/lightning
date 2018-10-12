from rest_framework import serializers
from member.models import Author, Ship

from api.serializers import BaseModelSerializerMixin


class authorSerializer(BaseModelSerializerMixin, serializers.ModelSerializer):

    class Meta:
        model = Author
        exclude = ('password', )


class shipSerializer(BaseModelSerializerMixin, serializers.ModelSerializer):

    class Meta:
        model = Ship
