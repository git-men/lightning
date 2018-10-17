from django.contrib.admin import ModelAdmin as DjangoModelAdmin


class ModelAdmin(DjangoModelAdmin):

    class ExtendMeta:
        pass
