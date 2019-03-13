from django.db import models

class Sector(models.Model):
  descripcion = models.CharField('Descripción', max_length=15)
  latitud = models.CharField(max_length=40, null=True, blank=True)
  longitud = models.CharField(max_length=40, null=True, blank=True)

  def __str__(self):
    return self.descripcion

# Disponible, Vendido, En proceso de pago
class EstadoLote(models.Model):
  descripcion = models.CharField(max_length=20)

  def __str__(self):
    return self.descripcion

class Lote(models.Model):
  numero = models.IntegerField()
  sector = models.ForeignKey(Sector, on_delete = models.CASCADE)
  precio = models.DecimalField(max_digits=15, decimal_places=2)
  estado = models.ForeignKey(EstadoLote, on_delete = models.CASCADE)

  def __str__(self):
    return '{0} > Lote #{1} > L {2:,}'.format(self.sector, self.numero, self.precio)

class Cliente(models.Model):
  identidad = models.CharField(max_length=15, primary_key=True)
  nombre = models.CharField(max_length=20)
  apellido = models.CharField(max_length=20)
  direccion = models.CharField('Dirección', max_length=150)
  telefono1 = models.CharField('Teléfono 1', max_length=10, null=True, blank=True)
  telefono2 = models.CharField('Teléfono 2', max_length=10, null=True, blank=True)
  email = models.EmailField('Correo', null=True, blank=True)

  def __str__(self):
    return '{} {}'.format(self.nombre, self.apellido)

class Periodo(models.Model):
  cantidad_anios = models.IntegerField()

  class Meta:
    ordering = ['cantidad_anios']

  def __str__(self):
    if self.cantidad_anios == 1:
      return '{} año'.format(self.cantidad_anios)
    else:
      return '{} años'.format(self.cantidad_anios)

class Contrato(models.Model):
  TIPO_VENTA = (
    ('credito', 'Crédito'),
    ('contado', 'Contado')
  )
  cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
  fecha_creacion = models.DateTimeField(auto_now_add=True)
  fecha_adquisicion = models.DateTimeField('Fecha adquisición')
  lotes = models.ManyToManyField(Lote)
  tipo_venta = models.CharField(max_length=7, choices=TIPO_VENTA, null=True, blank=True)
  periodos = models.ForeignKey(Periodo, on_delete=models.CASCADE, null=True, blank=True)
  prima = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
  tasa = models.CharField(max_length=3, null=True, blank=True)
  estado = models.BooleanField(default=True)

  @property
  def monto_total_lotes(self):
    monto_total = 0

    for lote in self.lotes.all():
      monto_total += float(lote.precio)

    return monto_total

  @property
  def monto_contrato_despues_de_prima(self):
    monto_total = 0

    for lote in self.lotes.all():
      monto_total += float(lote.precio)

    return monto_total - float(self.prima)

  def __str__(self):
    return 'Contrato #{} - {}'.format(self.id, self.cliente)

class PlanPagos(models.Model):
  fecha_creacion =  models.DateTimeField(auto_now_add=True)
  numero = models.IntegerField()
  contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE)
  abono = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
  saldo_deuda = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
  meses = models.IntegerField()
  estado = models.BooleanField(default=True)
  cuota = models.DecimalField(max_digits=15, decimal_places=2)
  saldo_restante_cancelado = models.BooleanField(default=False)
  monto_saldo_cancelado = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
  fecha_saldo_cancelado = models.DateTimeField(null=True, blank=True)

  def __str__(self):
    return '{} > Plan #{} > Estado: {}'.format(self.contrato, self.numero, self.estado)

# Fecha de pago
# Si el contrato se celebra el 24 de febrero o cualquier dia de febrero, la primera cuota corresponde al
# mes de marzo, pero el cliente puede cancelar marzo como fecha maxima el 5 de abril.

class DetallePlanPagos(models.Model):
  plan_pagos = models.ForeignKey(PlanPagos, on_delete=models.CASCADE)
  numero_cuota = models.IntegerField()
  cuota_capital = models.DecimalField(max_digits=15, decimal_places=2)
  cuota_intereses = models.DecimalField(max_digits=15, decimal_places=2)
  amortizacion = models.DecimalField(max_digits=15, decimal_places=2)
  fecha_maxima_pago = models.DateField()
  fecha_pago = models.DateTimeField(null=True, blank=True)
  cuota_pagada = models.BooleanField(default=False)

  def __str__(self):
    return 'Plan #{} = Cuota #{} > Amortizacion: {}: Pagada: {}'.format(self.plan_pagos.numero, self.numero_cuota, self.amortizacion, self.cuota_pagada)









