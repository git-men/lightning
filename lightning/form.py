class FormField(dict):
    def __init__(self, name, params=None, show_if=None):
        super().__init__({'name': name, 'widget': type(self).__name__, 'params': params or {}, 'showIf': show_if or []})


class TextInput(FormField):
    pass


class NumberInput(TextInput):
    pass


class Select(FormField):
    def __init__(self, name, params=None, nested_form=None):
        super().__init__(name, params)
        if nested_form is not None:
            self['nestedForm'] = nested_form


class InnerTable(FormField):
    def __init__(self, name, fields=None, display=None, can_add=True):
        params = {'canAdd': can_add}
        if fields is not None:
            params['fields'] = fields
        if display is not None:
            params['display'] = display
        super().__init__(name, params=params)


class InlineForm(FormField):
    def __init__(self, name, fields=None, can_add=True):
        params = {'canAdd': can_add}
        if fields is not None:
            params['fields'] = fields
        super().__init__(name, params=params)


class Radio(FormField):
    pass


class Gallery(FormField):
    pass


class Cascader(FormField):
    pass


class MultiFileUploader(FormField):
    pass


class PasswordInput(FormField):
    pass


class DatePicker(FormField):
    pass


class Transfer(FormField):
    pass
