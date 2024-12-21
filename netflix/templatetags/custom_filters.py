from django import template

register = template.Library()

@register.filter
def get_by_name(plans, name):
    """Returns the price of the plan with the given name."""
    for plan in plans:
        if plan['name'] == name:
            return plan['price']
    return 0
