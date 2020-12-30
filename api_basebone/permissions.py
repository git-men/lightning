
class BasePermission(object):

    def has_permission(self, user, model, func_name, params, request):
        raise NotImplementedError()