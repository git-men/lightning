from django.db import transaction
from .models import Block


@transaction.atomic
def move(source, parent, index):
    source = Block.objects.get(id=source)
    parent = Block.objects.get(id=parent)
    sibling_count = parent.children.count()
    if index == sibling_count:
        source.move_to(parent, position='last-child')
    elif index < sibling_count:
        target = parent.children.all()[index]
        position = 'left'
        if parent == source.parent and target.lft > source.rght:
            position = 'right'
        source.move_to(target, position=position)
