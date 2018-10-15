from rest_framework.routers import SimpleRouter as OriginSimpleRouter


class SimpleRouter(OriginSimpleRouter):

    def __init__(self, **kwargs):
        self.custom_base_name = kwargs.pop('custom_base_name')
        super(SimpleRouter, self).__init__(**kwargs)

    def get_default_base_name(self, viewset):
        """
        If `base_name` is not specified, attempt to automatically determine
        it from the viewset.
        """
        queryset = getattr(viewset, 'queryset', None)

        if queryset is None:
            return self.custom_base_name

        return queryset.model._meta.object_name.lower()
