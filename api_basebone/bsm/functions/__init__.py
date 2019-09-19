from api_basebone.restful.funcs import bsm_func

from api_basebone.models import Api

from api_basebone.services import api_services


@bsm_func(staff_required=True, name='show_api', model=Api)
def show_api(user, slug, **kwargs):
    return api_services.show_api(slug)


@bsm_func(staff_required=True, name='api_save', model=Api)
def api_save(user, config, **kwargs):
    api_services.save_api(config)
    return api_services.show_api(config.get('slug', ''))
