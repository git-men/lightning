from django.contrib import admin
from member.models import Author, Ship


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'name', 'gender', 'city', 'age')


@admin.register(Ship)
class ShipAdmin(admin.ModelAdmin):
    list_display = ('name', 'title')
