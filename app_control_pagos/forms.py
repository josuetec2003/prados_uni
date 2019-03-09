from django import forms
from django.forms import ModelForm
from django.urls import reverse
from django.contrib.auth.forms import PasswordChangeForm
from .models import Sector, Lote, Cliente, Contrato, EstadoLote
from datetime import datetime

class MyPasswordChangeForm(PasswordChangeForm):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

    self.base_fields['old_password'].widget.attrs['class'] = 'form-control'
    self.base_fields['new_password1'].widget.attrs['class'] = 'form-control'
    self.base_fields['new_password2'].widget.attrs['class'] = 'form-control'

class ContratoForm(ModelForm):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    estado_disponible = EstadoLote.objects.get(pk=1)
    self.fields['lotes'].queryset = Lote.objects.filter(estado = estado_disponible)

  class Meta:
    model = Contrato
    fields = '__all__'
    widgets = {
      'cliente': forms.Select(attrs={'class': 'chosen'}),
      'tipo_venta': forms.Select(attrs={'class': 'form-control'}),
      'fecha_adquisicion': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'date'}),
      'lotes': forms.Select(attrs={'class': 'chosen', 'multiple': 'multiple', 'data-url': '/s/calcular-monto-venta/'}),
      'periodos': forms.Select(attrs={'class': 'chosen'}),
      'prima': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Presione ENTER para ver nuevo saldo', 'data-url': '/s/calcular-monto-venta/'}),
      'tasa': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tasa anual en porcentaje (%)'}),
      'estado': forms.HiddenInput()
    }

class CotizacionForm(ModelForm):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    estado_disponible = EstadoLote.objects.get(pk=1)
    self.fields['lotes'].queryset = Lote.objects.filter(estado = estado_disponible)

  class Meta:
    model = Contrato
    fields = ['lotes', 'periodos', 'prima', 'tasa']
    widgets = {
      'lotes': forms.Select(attrs={'required':'required', 'class': 'chosen', 'multiple': 'multiple', 'data-url': '/s/calcular-monto-venta/'}),
      'periodos': forms.Select(attrs={'class': 'chosen', 'required':'required'}),
      'prima': forms.NumberInput(attrs={'required':'required', 'class': 'form-control', 'placeholder': 'Ingrese el monto de la prima', 'data-url': '/s/calcular-monto-venta/'}),
      'tasa': forms.TextInput(attrs={'required':'required', 'class': 'form-control', 'placeholder': 'Tasa anual en porcentaje (%)'}),
    }

class SectorForm(ModelForm):
  class Meta:
    model = Sector
    fields = ['descripcion']
    widgets = {
      'descripcion': forms.TextInput(attrs={'class': 'form-control'})
    }

class LoteForm(ModelForm):
  class Meta:
    model = Lote
    fields = '__all__'
    widgets = {
      'numero': forms.NumberInput(attrs={'class': 'form-control'}),
      'sector': forms.Select(attrs={'class': 'form-control'}),
      'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
      'estado': forms.HiddenInput()
    }

class ClienteForm(ModelForm):
  class Meta:
    model = Cliente
    fields = '__all__'
    widgets = {
      'identidad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0000-0000-00000'}),
      'nombre': forms.TextInput(attrs={'class': 'form-control'}),
      'apellido': forms.TextInput(attrs={'class': 'form-control',}),
      'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': '3'}),
      'telefono1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0000-0000'}),
      'telefono2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0000-0000'}),
      'email': forms.EmailInput(attrs={'class': 'form-control'})
    }


#  widgets = {
#   'ciclo': forms.HiddenInput(),
#   'laguna': Select(attrs={'class': 'form-control'}),
#   'fecha_siembra': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'date', 'readonly': 'readonly'}),
#   'densidad': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
#   'tipo': Select(attrs={'class': 'form-control'}),
#   'fca': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
#   'dias_cosecha': forms.NumberInput(attrs={'class': 'form-control'}),
#   'fecha_cosecha': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'date', 'readonly': 'readonly'}),
#   'dias_secado': forms.NumberInput(attrs={'class': 'form-control'}),
#   'crecimiento_semanal': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
#   'cinc_cinc': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ejemplo: 50%'}),
#   'peso_cosecha': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any', 'readonly': 'readonly'}),
#   'camarones_por_m2': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any', 'readonly': 'readonly'}),
#   'libras_totales': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any', 'readonly': 'readonly'}),
#   'rendimiento_por_ha': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any', 'readonly': 'readonly'}),
#   'copia': forms.HiddenInput(),
#   'copia_de': forms.HiddenInput()
# }
