from django import template
from django.http import QueryDict

register = template.Library()

@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    """
    Replace or add query parameters to the current URL
    Usage: {% url_replace page=2 sort=name %}
    """
    request = context['request']
    query = request.GET.copy()
    
    for key, value in kwargs.items():
        query[key] = value
    
    return query.urlencode() 