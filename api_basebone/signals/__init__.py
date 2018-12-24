from django.dispatch import Signal

post_bsm_create = Signal(providing_args=['instance', 'create'])

