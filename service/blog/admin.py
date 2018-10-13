# from django.apps import apps
from django.contrib import admin
from blog.models import Tag, Category, Article

# app_list = ['blog']

# for app_name in app_list:
#     application = apps.get_app_config(app_name)

#     for model in application.get_models():
#         admin.site.register(model)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'show', 'parent')


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'is_public', 'author')
