from bsm_config.models import Setting

def get_settins():
    data = Setting.objects.all()
    settings = {}
    for setting in data:
        print(setting)
        settings.update({
            setting.key: setting.value
        })
    print(settings)
    return settings