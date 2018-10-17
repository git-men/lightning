from django.contrib.admin import ModelAdmin as DjangoModelAdmin


class ModelAdmin(DjangoModelAdmin):

    class GMeta:
        gmeta_auth_filter_field = None
