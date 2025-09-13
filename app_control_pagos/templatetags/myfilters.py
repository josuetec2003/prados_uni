from django import template

register = template.Library()

@register.filter(name='sum_value')
def sum_value(value, arg=None):
    if arg:
        return float(value) + float(arg)
    
    return float(value)

@register.filter(name='cuotas_activas')
def cuotas_activas(value, arg=None):
    return value.filter(activo=True, cuota_pagada=True)

@register.filter(name="fecha_corta")
def fecha_corta(value, arg=None):
    if value:
        return value.strftime('%d.%m.%y')
    
    return 'N.A'