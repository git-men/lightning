from functools import partial
component_resolver_map = {}


def component_resolver(component_type):
    return partial(component_resolver_map.__setitem__, component_type)
