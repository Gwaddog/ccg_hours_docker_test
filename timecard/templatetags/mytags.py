from django import template
from datetime import timedelta
#
# See: https://docs.djangoproject.com/en/4.2/howto/custom-template-tags/
#

register = template.Library()
@register.filter(name='timedelta_filter')
def timedelta_filter(value, arg):
    """
    Returns the delta in seconds of an ending time and starting time.
    Use as: {{ending_time|timedelta_filter:starting_time }}
    """
    return timedelta(hours=value.hour,minutes=value.minute)-timedelta(hours=arg.hour,minutes=arg.minute)

@register.filter
def duration_filter(td):
    """
    Returns the file in hours and minute format
    """
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60

    return '{hours:02d}:{minutes:02d}'.format(hours=hours, minutes=minutes)

@register.filter
def div(value, arg):
    """Returns the value divided by the arg"""
    return value / arg

@register.filter
def mod(value, arg):
    """Returns the value modulo the arg"""
    return value % arg