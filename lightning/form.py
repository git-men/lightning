class TextInput(dict):
    def __init__(self, name, params=None):
        super().__init__({'name': name, 'widget': type(self).__name__, 'params': params or {}})


class InnerTable(TextInput):
    def __init__(self, name, fields=None, display=None, can_add=True):
        params = {'canAdd': can_add}
        if fields is not None:
            params['fields'] = fields
        if display is not None:
            params['display'] = display
        super().__init__(name, params=params)


class InlineForm(TextInput):
    def __init__(self, name, fields=None, can_add=True):
        params = {'canAdd': can_add}
        if fields is not None:
            params['fields'] = fields
        super().__init__(name, params=params)
