from functools import partial
component_resolver_map = {}


class component_resolver:
    def __init__(self, component_type):
        self.component_type = component_type

    def __call__(self, func):
        component_resolver_map[self.component_type] = func
        return func
