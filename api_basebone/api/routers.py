from rest_framework.routers import Route
from api_basebone.drf.routers import SimpleRouter


class ApiRouter(SimpleRouter):

    routes = [
        # List route.
        # Route(
        #     url=r'^{prefix}{trailing_slash}$',
        #     mapping={'get': 'list', 'post': 'create'},
        #     name='{basename}-list',
        #     detail=False,
        #     initkwargs={'suffix': 'List'},
        # ),
        # Dynamically generated list routes. Generated using
        # @action(detail=False) decorator on methods of the viewset.
        # DynamicRoute(
        #     url=r'^{prefix}/{url_path}{trailing_slash}$',
        #     name='{basename}-{url_name}',
        #     detail=False,
        #     initkwargs={},
        # ),
        # Detail route.
        Route(
            url=r'^{prefix}/{lookup}{trailing_slash}$',
            mapping={
                'get': 'api',
                'post': 'api',
                'put': 'api',
                'patch': 'api',
                'delete': 'api',
            },
            name='{basename}-detail',
            detail=True,
            initkwargs={},
        ),
        # Dynamically generated detail routes. Generated using
        # @action(detail=True) decorator on methods of the viewset.
        # DynamicRoute(
        #     url=r'^{prefix}/{lookup}/{url_path}{trailing_slash}$',
        #     name='{basename}-{url_name}',
        #     detail=True,
        #     initkwargs={},
        # ),
    ]
