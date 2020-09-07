def register_annotated_field(
    model, field_name, field_type, annotation, display_name=None
):
    if display_name is None:
        display_name = field_name

    if not hasattr(model, 'GMeta'):
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
