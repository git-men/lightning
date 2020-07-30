import datetime
from django.conf import settings
from django.db.models.fields import warnings, exceptions
from django.utils import timezone
from django.utils.dateparse import (
    datetime_re,
    parse_date,
    parse_datetime,
)


def gm_parse_datetime(value):
    if settings.USE_TZ:
        return parse_datetime(value)

    match = datetime_re.match(value)
    if match:
        kw = match.groupdict()
        kw.pop('tzinfo')
        kw.pop('microsecond')
        kw = {k: int(v) for k, v in kw.items() if v is not None}
        return datetime.datetime(**kw)


class DateTimeFieldExtend:
    """查询扩展"""

    def to_python(self, value):
        print(value, type(value))
        if value is None:
            return value
        if isinstance(value, datetime.datetime):
            return value
        if isinstance(value, datetime.date):
            value = datetime.datetime(value.year, value.month, value.day)
            if settings.USE_TZ:
                warnings.warn(
                    "DateTimeField %s.%s received a naive datetime "
                    "(%s) while time zone support is active."
                    % (self.model.__name__, self.name, value),
                    RuntimeWarning,
                )
                default_timezone = timezone.get_default_timezone()
                value = timezone.make_aware(value, default_timezone)
            return value

        try:
            parsed = gm_parse_datetime(value)
            if parsed is not None:
                return parsed
        except ValueError:
            raise exceptions.ValidationError(
                self.error_messages['invalid_datetime'],
                code='invalid_datetime',
                params={'value': value},
            )

        try:
            parsed = parse_date(value)
            if parsed is not None:
                return datetime.datetime(parsed.year, parsed.month, parsed.day)
        except ValueError:
            raise exceptions.ValidationError(
                self.error_messages['invalid_date'],
                code='invalid_date',
                params={'value': value},
            )

        raise exceptions.ValidationError(
            self.error_messages['invalid'], code='invalid', params={'value': value},
        )
