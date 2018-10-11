from django.contrib import admin
from member.models import Author


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('username', 'name', 'gender', 'city', 'age')
