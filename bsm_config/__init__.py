default_app_config = 'bsm_config.apps.BsmConfigConfig'

def config_loader():
    from bsm_config.models import Admin
    configs = Admin.objects.all()
    return dict([(config.model, config.config) for config in configs])
