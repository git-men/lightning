from django.contrib import admin
from member.models import Author, Ship

from api_basebone.core.admin import ModelAdmin


@admin.register(Author)
class AuthorAdmin(ModelAdmin):
    list_display = ('id', 'username', 'name', 'gender', 'city', 'age')


@admin.register(Ship)
class ShipAdmin(ModelAdmin):
    list_display = ('name', 'title')
