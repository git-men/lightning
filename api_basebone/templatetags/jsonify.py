import json
from django.template import Library

register = Library()


def jsonify(data):
    return json.dumps(data, ensure_ascii=False, indent=2)


register.filter('jsonify', jsonify)
