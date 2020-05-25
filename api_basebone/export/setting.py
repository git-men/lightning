from bsm_config.models import Setting

def get_settins():
    data = Setting.objects.all()
    settings = {}
    for setting in data:
        settings.update({
            setting.key: setting.value
        })
    return settings