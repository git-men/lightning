def register_annotated_field(
    model, field_name, field_type, annotation, display_name=None
):
    if display_name is None:
        display_name = field_name

    if 'GMeta' not in model.__dict__:
        if hasattr(model, 'GMeta'):
            class GMeta(model.GMeta):
                annotated_fields = {}
        else:
            class GMeta:
                pass
        model.GMeta = GMeta

    if not hasattr(model.GMeta, 'annotated_fields'):
        model.GMeta.annotated_fields = {}

    model.GMeta.annotated_fields[field_name] = {
        'display_name': display_name,
        'type': field_type,
        'annotation': annotation,
    }


def register_computed_field(model, field_name, field_type, prop, display_name=None, deps=None):
    setattr(model, field_name, property(prop))

    if display_name is None:
        display_name = field_name

    if 'GMeta' not in model.__dict__:
        class GMeta:
            pass
        model.GMeta = GMeta

    if not hasattr(model.GMeta, 'computed_fields'):
        model.GMeta.computed_fields = []
    cfg = {
        'name': field_name,
        'display_name': display_name,
        'type': field_type,
    }

    if deps is not None:
        cfg['deps'] = deps

    model.GMeta.computed_fields.append(cfg)
