from rest_framework import serializers
from member.models import Author

from api.serializers import BaseModelSerializerMixin


class authorSerializer(BaseModelSerializerMixin, serializers.ModelSerializer):

    class Meta:
        model = Author
        exclude = ('password', )
