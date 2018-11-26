from django.dispatch import Signal

post_save = Signal(providing_args=['instance', 'create'])

