from api_basebone.permissions import BasePermission
default_app_config = 'lightning.apps.LightningConfig'

APPS = [
    'guardian',
    'api_basebone',
    'bsm_config',
    'shield',
    'storage',
    'puzzle',
    'lightning',
]

FUNC_SCENE_UNLIMIT = 'unlimit'
FUNC_SCENE_INLINE = 'inline'
FUNC_SCENE_BATCH = 'batch'

FUNC_DATA_TYPE_STRING = 'string'
FUNC_DATA_TYPE_INT = 'integer'
FUNC_DATA_TYPE_DECIMAL = 'decimal'
FUNC_DATA_TYPE_BOOL = 'bool'
FUNC_DATA_TYPE_REF = 'ref'
FUNC_DATA_TYPE_DATE = 'date'
FUNC_DATA_TYPE_IMAGE = 'image'
