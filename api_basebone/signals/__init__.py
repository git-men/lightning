from django.dispatch import Signal

post_bsm_create = Signal(providing_args=['instance', 'create', 'request', 'old_instance'])
before_bsm_create = Signal(providing_args=['instance', 'create', 'request'])
post_bsm_delete = Signal(providing_args=['instance', 'request'])
before_bsm_delete = Signal(providing_args=['instance', 'request'])
