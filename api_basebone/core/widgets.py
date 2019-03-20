from enum import Enum, unique


@unique
class BSMWidgets(Enum):
    """存放各种组件常量

    保证和前端配置一致，同时是为了避免手写错误
    """

    TextInput = 'TextInput'
    TextArea = 'TextArea'
    RichTextEditor = 'RichTextEditor'
    NumberInput = 'NumberInput'
    Switch = 'Switch'
    Select = 'Select'
    InlineForm = 'InlineForm'
    TimePicker = 'TimePicker'
    ImageUploader = 'ImageUploader'
    FileUploader = 'FileUploader'
    Gallery = 'Gallery'
    Transfer = 'Transfer'
    TreeSelect = 'TreeSelect'
    PasswordInput = 'PasswordInput'
    Checkbox = 'Checkbox'
    Cascader = 'Cascader'
    Radio = 'Radio'
    SkuSpec = 'SkuSpec'  # TODO 这个以及后面的控件，都是自定义控件，可以不写在这里。
    DistrictSelect = 'DistrictSelect'

class Widgets:

    def __getattr__(self, key):
        widget = getattr(BSMWidgets, key, None)
        if not widget:
            raise AttributeError
        return widget.name


widgets = Widgets()
