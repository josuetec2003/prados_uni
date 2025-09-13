from django.contrib import admin

from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import *

class UserAdmin(BaseUserAdmin):
  def get_queryset(self, request):
    qs = super().get_queryset(request)
    if not request.user.is_superuser:
      return qs.filter(is_superuser=False)
    return qs

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(Contrato)
class ContratoAdmin(admin.ModelAdmin):
  readonly_fields = ['monto_contrato_despues_de_prima']

class DetallePlanPagosInline(admin.TabularInline):
  model = DetallePlanPagos

@admin.register(PlanPagos)
class PlanPagosAdmin(admin.ModelAdmin):
  inlines = [DetallePlanPagosInline, ]

admin.site.register(Sector)
admin.site.register(EstadoLote)

@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
  list_display = [field.name for field in Lote._meta.fields]
  list_editable = ('estado',)

admin.site.register(Cliente)
admin.site.register(Periodo)







