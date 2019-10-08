from api_basebone.services import api_services

APP = 'api_basebone'

show_api = {
    "slug": f"{APP}__show_api",
    "app": APP,
    "model": "api",
    "operation": "func",
    "func_name": "show_api",
    "parameter": [{"name": "slug", "type": "string", "required": True, "desc": ""}],
}

API_CONFIGS = [show_api]

api_services.load_api_data(APP, API_CONFIGS)
