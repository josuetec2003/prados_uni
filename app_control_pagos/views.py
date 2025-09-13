from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.urls import reverse
from django.db.models import Q, Sum

from django.template import Context
from django.template.loader import get_template

from ast import literal_eval
from datetime import datetime, timedelta
import calendar

from .forms import SectorForm, LoteForm, ClienteForm, ContratoForm, MyPasswordChangeForm, CotizacionForm

from .models import (
  Sector, Lote, EstadoLote,
  Cliente,
  Periodo,
  Contrato, PlanPagos, DetallePlanPagos
)

@login_required()
def index(request):
  return render(request, 'app_pagos/index.html')

@login_required()
def lotes(request, objetivo = None, id = None):

  if objetivo is None:
    sector_form = SectorForm()
    estado_disponible = EstadoLote.objects.get(pk=1)
    lote_form = LoteForm(initial={'estado': estado_disponible})

  if objetivo == 'sector':
    lote_form = LoteForm()
    sector = Sector.objects.get(pk=id)
    sector_form = SectorForm(instance = sector)

  if objetivo == 'lote':
    sector_form = SectorForm()
    lote = Lote.objects.get(pk=id)
    lote_form = LoteForm(instance = lote)

  sectores = Sector.objects.all()
  lotes = Lote.objects.all()

  ctx = {
    'id': id,
    'sector_form': sector_form,
    'lote_form': lote_form,
    'sectores': sectores,
    'lotes': lotes
  }

  return render(request, 'app_pagos/lotes.html', ctx)

@login_required()
def agregar_sector(request, objetivo = None, id = None):
  if request.method == 'POST':

    form = None

    if objetivo == 'sector':
      sector = get_object_or_404(Sector, pk=id) if id else None
      form = SectorForm(request.POST or None, instance = sector)

    if objetivo == 'lote':
      lote = get_object_or_404(Lote, pk=id) if id else None
      form = LoteForm(request.POST or None, instance = lote)

    if form.is_valid():
        form.save()
        return HttpResponseRedirect(reverse('pagos:lotes'))
    else:
        return render(request, 'app_pagos/lotes.html', {'form': form})

@login_required
def clientes(request, id = None):

  if id:
    cliente = Cliente.objects.get(pk=id)
    form = ClienteForm(instance = cliente)
  else:
    form = ClienteForm()

  clientes = Cliente.objects.all()

  ctx = {
    'form': form,
    'clientes': clientes,
    'id': id
  }
  return render(request, 'app_pagos/clientes.html', ctx)

@login_required
def guardar_cliente(request, id = None):
  if request.method == 'POST':
    cliente = get_object_or_404(Cliente, pk=id) if id else None
    form = ClienteForm(request.POST or None, instance = cliente)

    if form.is_valid():
      form.save()

      return HttpResponseRedirect(reverse('pagos:clientes'))
    else:
      clientes = Cliente.objects.all()

      ctx = {
        'form': form,
        'clientes': clientes
      }
      return render(request, 'app_pagos/clientes.html', ctx)

@login_required
def contrato_view(request, tipo = None):
  form = ContratoForm(initial={'tipo_venta': 'credito'})
  q = request.GET.get('q')

  if q:
    contratos = Contrato.objects.filter( (Q(cliente__nombre__istartswith = q) | Q(cliente__apellido__istartswith = q)), anulado = False).order_by('-fecha_adquisicion')
  else:
    if tipo == 'credito':
      contratos = Contrato.objects.filter(tipo_venta = 'credito', estado = True, anulado = False).order_by('-fecha_adquisicion')
    elif tipo == 'contado':
      contratos = Contrato.objects.filter(tipo_venta = 'contado', anulado = False).order_by('-fecha_adquisicion')
    elif tipo == 'pagado':
      contratos = Contrato.objects.filter(estado = False, anulado = False).order_by('-fecha_adquisicion')
    else:
      contratos = Contrato.objects.filter(anulado = False).order_by('-fecha_adquisicion')

  ctx = {
    'form': form,
    'contratos': contratos,
    'tipo': tipo,
    'q': q
  }
  return render(request, 'app_pagos/contrato.html', ctx)

@login_required
def calcular_monto_venta(request):
  desde = request.GET.get('desde')
  lotes = request.GET.get('lotes')
  prima = request.GET.get('prima')

  monto = 0

  if prima == '':
    prima = 0

  for lote_id in literal_eval(lotes):
    lote = Lote.objects.get(pk=lote_id)
    monto += lote.precio

  monto = float(monto) - float(prima)

  return JsonResponse({'monto': 'L {0:,}'.format(monto)})

@login_required
def realizar_venta(request):
  cliente = request.GET.get('cliente')
  fecha = request.GET.get('fecha')
  lotes = request.GET.get('lotes')
  periodos = request.GET.get('periodos')
  prima = request.GET.get('prima')
  tasa = request.GET.get('tasa')
  tipo_venta = request.GET.get('tipo_venta')

  url_detalle_plan = None

  # Validaciones
  if cliente == '':
    return JsonResponse({'msg': 'Seleccione el cliente', 'style': 'warn'})

  if fecha == '':
    return JsonResponse({'msg': 'Seleccione la fecha', 'style': 'warn'})

  if len(literal_eval(lotes)) == 0:
    return JsonResponse({'msg': 'Seleccione al menos un lote', 'style': 'warn'})

  if tipo_venta == '':
    return JsonResponse({'msg': 'Seleccione el tipo de venta', 'style': 'warn'})
  else:

    cliente_obj = Cliente.objects.get(pk=cliente)

    if tipo_venta == 'credito':
      if periodos == '':
        return JsonResponse({'msg': 'Seleccione el periodo', 'style': 'warn'})

      if prima == '':
        return JsonResponse({'msg': 'Ingrese el monto de la prima', 'style': 'warn'})

      if tasa == '':
        return JsonResponse({'msg': 'Ingrese la tasa', 'style': 'warn'})

      if not '%' in tasa:
        return JsonResponse({'msg': 'Falta el % en la tasa', 'style': 'warn'})

      periodo_obj = Periodo.objects.get(pk=int(periodos))

      contrato = Contrato.objects.create(
        cliente = cliente_obj,
        fecha_adquisicion = fecha,
        periodos = periodo_obj,
        prima = float(prima),
        tasa = tasa,
        tipo_venta = tipo_venta
      )

      contrato.save()

      # Para agregar los lotes al contrato
      for lote_id in literal_eval(lotes):
        lote = Lote.objects.get(pk=lote_id)
        contrato.lotes.add(lote)
        en_estado_pagando = EstadoLote.objects.get(pk=3)
        lote.estado = en_estado_pagando
        lote.save()

      # CREAR EL PLAN DE PAGOS PARA EL CONTRATO

      monto = contrato.monto_contrato_despues_de_prima
      tasa = (float(contrato.tasa.strip('%')) / 100) / 12
      plazo = periodo_obj.cantidad_anios * 12
      cuota = (monto * tasa) / (1 - (1 + tasa) ** -plazo)

      plan = PlanPagos.objects.create(
        numero = 1,
        contrato = contrato,
        meses = plazo,
        cuota = cuota
      )

      # GENERAR EL DETALLE DE PAGOS DEL PLAN

      # monto = monto - capital;
      hoy = datetime.now()

      # Fecha 5 del mes en que se registra la venta del lote
      mes_dia_cinco = datetime(hoy.year, hoy.month, 5)

      # dias del mes actual (mes en que se registra la venta)
      dias_mes_actual = calendar.monthrange(mes_dia_cinco.year, mes_dia_cinco.month)[1]

      # Fecha 5 del siguiente mes
      # Este mes corresponde a la primera cuota, pero tiene hasta el 5 del siguiente para pagar
      mes_siguiente = mes_dia_cinco + timedelta(days=dias_mes_actual)


      for i in range(1, plazo + 1):
        intereses = monto * tasa
        capital = cuota - intereses
        monto = monto - capital

        # dias del mes de la cuota (i)
        dias_mes_cuota = calendar.monthrange(mes_siguiente.year, mes_siguiente.month)[1]

        # fecha maxima para pagar la primera cuota
        fecha_maxima_pago = mes_siguiente + timedelta(days = dias_mes_cuota)

        c = DetallePlanPagos.objects.create(
          plan_pagos = plan,
          numero_cuota = i,
          cuota_capital = capital,
          cuota_intereses = intereses,
          amortizacion = monto,
          fecha_maxima_pago = fecha_maxima_pago
        )

        mes_siguiente = fecha_maxima_pago

      url_detalle_plan = reverse('pagos:detalle_plan_pagos', args=[contrato.id])

    else:

      contrato = Contrato.objects.create(
        cliente = cliente_obj,
        fecha_adquisicion = fecha,
        tipo_venta = tipo_venta,
        estado = False
      )

      url_detalle_plan = reverse('pagos:info_contrato_contado', args=[contrato.id])

      for lote_id in literal_eval(lotes):
        lote = Lote.objects.get(pk=lote_id)
        contrato.lotes.add(lote)
        en_estado_pagado = EstadoLote.objects.get(pk=2)
        lote.estado = en_estado_pagado
        lote.save()


  return JsonResponse({'style': 'success', 'url_redirect': url_detalle_plan, 'msg': 'El contrato ha sido registrado con éxito'})

@login_required()
def detalle_plan_pagos(request, id):
  contrato = Contrato.objects.get(pk=id)

  #return HttpResponse(contrato.prima)

  # Plan vigente (si ya se pagó el lote, no habría ninguno)
  try:
    plan = PlanPagos.objects.get(contrato = contrato, estado = True)
    detalle = DetallePlanPagos.objects.filter(plan_pagos = plan, activo = True).order_by('numero_cuota')
  except:
    plan = None
    detalle = None

  try:
    plan_saldo_cancelado = PlanPagos.objects.get(contrato = contrato, estado = False, saldo_restante_cancelado = True)
  except:
    plan_saldo_cancelado = None


  # Planes anteriores
  planes_anteriores = PlanPagos.objects.filter(contrato = contrato, estado = False).order_by('-fecha_creacion')


  cuotas_pagadas = DetallePlanPagos.objects.filter(cuota_pagada = True, plan_pagos__contrato = contrato, activo=True)
  abonos = PlanPagos.objects.filter(contrato = contrato, abono__isnull = False)

  cuotas_pagadas_suma = 0
  for x in DetallePlanPagos.objects.filter(cuota_pagada = True, plan_pagos__contrato = contrato, activo=True): #.aggregate(suma = Sum('plan_pagos__cuota'))
    cuotas_pagadas_suma += float(x.pago_intereses + x.pago_capital) if x.pago_intereses else float(x.plan_pagos.cuota)

  abonos_suma = PlanPagos.objects.filter(contrato = contrato, abono__isnull = False).aggregate(suma = Sum('abono'))

  abonos_mismo_plan = cuotas_pagadas.filter(abono_a_capital__isnull=False, activo=True)

  total_contrato = 0

  if abonos_mismo_plan:
    total_contrato += float(abonos_mismo_plan.aggregate(suma = Sum('abono_a_capital'))['suma'])
  
  if cuotas_pagadas_suma > 0 and abonos_suma['suma']:
    total_contrato += cuotas_pagadas_suma + float(abonos_suma['suma'])

  elif cuotas_pagadas_suma > 0:
    total_contrato += cuotas_pagadas_suma

  total_contrato += float(contrato.prima)

  if plan_saldo_cancelado:
    total_contrato += float(plan_saldo_cancelado.monto_saldo_cancelado)

  ctx = {
    'plan': plan,
    'detalle': detalle,
    'planes_anteriores': planes_anteriores,
    'cuotas_pagadas': cuotas_pagadas,
    'abonos': abonos,
    'abonos_mismo_plan': abonos_mismo_plan,
    'contrato': contrato,
    'total_contrato': total_contrato,
    'plan_saldo_cancelado': plan_saldo_cancelado
  }

  return render(request, 'app_pagos/detalle_plan_pagos.html', ctx)

@login_required()
def registrar_pago(request):
  # clientes = Cliente.objects.all().order_by('nombre')
  contratos = Contrato.objects.filter(estado = True)
  clientes = set([c.cliente for c in contratos])

  ctx = {
    'clientes': clientes
  }

  return render(request, 'app_pagos/registrar_pago.html', ctx)

@login_required()
def obtener_prestamos_cliente(request):
  identidad = request.GET.get('identidad')

  cliente = Cliente.objects.get(pk=identidad)

  contratos = Contrato.objects.filter(cliente=cliente, estado=True, anulado = False, tipo_venta = 'credito')

  html = ''

  if contratos:
    hoy = datetime.now()

    for contrato in contratos:
      lotes = '' # Estaba despues del for
      fecha_pago = ''

      try:
        plan = PlanPagos.objects.get(contrato=contrato, estado=True)
        cuota_a_pagar = DetallePlanPagos.objects.filter(plan_pagos=plan, cuota_pagada=False).order_by('numero_cuota').first()
        print('cuota_a_pagar', cuota_a_pagar)

        # si el plan es nuevo, no tendrá ultima cuota pagada, por lo tanto la variable quedará nula.
        # en este caso hay que obtener el valor de la deuda para mostrarla
        ultima_cuota_pagada = DetallePlanPagos.objects.filter(plan_pagos=plan, cuota_pagada=True, activo=True).order_by('numero_cuota').last()
        

        saldo_amortizacion = None
        fecha_ultimo_pago = None

        if not ultima_cuota_pagada:
          if not plan.saldo_deuda:
            saldo_amortizacion = plan.contrato.monto_contrato_despues_de_prima
          else:
            fecha_ultimo_pago = plan.fecha_creacion.strftime("%d/%m/%Y")
            saldo_amortizacion = plan.saldo_deuda
        else:
          if ultima_cuota_pagada.nuevo_saldo:
            saldo_amortizacion = ultima_cuota_pagada.nuevo_saldo
          else:
            saldo_amortizacion = ultima_cuota_pagada.amortizacion

          fecha_ultimo_pago = ultima_cuota_pagada.fecha_pago.strftime("%d/%m/%Y")

        url_procesar_pago = reverse('pagos:procesar_pago_cuota')
        url_realizar_abono = reverse('pagos:realizar_abono')
        url_plan_pagos = reverse('pagos:detalle_plan_pagos', args=[contrato.id])

        # ya que no se puede comparar date (fecha maxima pago) con datetime (fecha de hoy)
        fecha_maxima_pago = datetime.combine(cuota_a_pagar.fecha_maxima_pago, datetime.min.time())
        if hoy < fecha_maxima_pago:
          fecha_pago += '<span class="text-success"><strong>{}</strong></span>'.format(cuota_a_pagar.fecha_maxima_pago.strftime('%d/%m/%Y'))
        else:
          fecha_pago += '''
            <span class="text-danger"><strong>{}</strong></span>
          '''.format(cuota_a_pagar.fecha_maxima_pago.strftime('%d/%m/%Y'))

        for lote in contrato.lotes.all():
          lotes += '''
            <span class="badge badge-light">{}</span>
          '''.format(lote)
        
        # Para mostrar la fecha del ultimo pago realizado, ya sea cuota o creacion de un plan nuevo
        # El primer plan creado no tendra fecha de ultimo pago, para eso es este IF
        fup = '<span class="text-dark"><strong>{0}</strong></span>'.format(fecha_ultimo_pago) if fecha_ultimo_pago else ''

        cuota_pagar = 0
        
        if float(saldo_amortizacion) < float(plan.cuota):
          if cuota_a_pagar.pago_intereses:
            cuota_pagar = float(saldo_amortizacion) + float(cuota_a_pagar.pago_intereses)
          else:
            cuota_pagar = plan.cuota
        else:
          cuota_pagar = plan.cuota

        fecha_hoy = datetime.now().strftime('%Y-%m-%d')
        
        html += '''
          <div class="shadow-none p-3 mb-2 mt-2 bg-light rounded" id="div-cuota-{5}">
            <h5><span class="badge badge-success">Cuota por pagar: #{1}</span> <small><a href="{9}">Contrato #{0}</a></small></h5>
            {3}
            
            <table class="table table-sm mt-4">
              <tr>
                <td>Fecha del último pago:</td>
                <td>{10}</td>
              </tr>
              <tr>
                <td>Saldo:</td>
                <td><span class="text-danger"><strong>L{8:,}</strong></span></td>
              </tr>
              <tr>
                <td>Fecha máxima de pago:</td>
                <td>{4}</td>
              </tr>
              <tr>
                <td>Valor de la cuota:</td>
                <td><span class="text-info"><strong>L{2:,}</strong></span></td>
              </tr>
              <tr>
                <td>Fecha del pago:</td>
                <td><input type="date" id="fecha-pago-{5}" value="{11}" /></td>
              </tr>
            </table>

            <hr />
            
            <button class="btn btn-primary btn-realizar-pago" data-cuota-id="{5}" data-url="{6}">
              Registrar pago <i class="fas fa-fw fa-money-bill"></i></a>
            </button>
            <button class="btn btn-info btn-realizar-abono" data-cuota-id="{5}" data-url="{7}">
              Realizar abono <i class="fas fa-fw fa-plus"></i></a>
            </button>
          </div>
        '''.format(contrato.id, cuota_a_pagar.numero_cuota, cuota_pagar, lotes, fecha_pago, cuota_a_pagar.id, url_procesar_pago, url_realizar_abono, saldo_amortizacion, url_plan_pagos, fup, fecha_hoy)
      except Exception as e:
        print(f'Error: {e}')
  else:
    html += '''
      <div class="alert alert-warning mt-2" role="alert">
        Este cliente no tiene contratos pendientes
      </div>
    '''

  return JsonResponse({'html': html})

@login_required()
def procesar_pago_cuota(request):
  # id de la cuota
  id = request.GET.get('id')
  fecha_del_pago = request.GET.get('fechaPago')
  msg = None

  cuota = DetallePlanPagos.objects.get(pk = id)
  cuota.cuota_pagada = True
  cuota.fecha_pago = fecha_del_pago #datetime.now()
  cuota.save()

  # determinar si es la ultima cuota
  ultima_cuota = DetallePlanPagos.objects.filter(plan_pagos = cuota.plan_pagos, activo=True).order_by('numero_cuota').last()

  if cuota.numero_cuota == ultima_cuota.numero_cuota:
    contrato = Contrato.objects.get(pk=cuota.plan_pagos.contrato.id)
    contrato.estado = False
    contrato.save()

    plan = PlanPagos.objects.get(pk=ultima_cuota.plan_pagos.id)
    plan.estado = False
    plan.save()

    estado_vendido = EstadoLote.objects.get(pk=2)

    # se ponen en estado vendido los lotes del contrato
    for lote in contrato.lotes.all():
      lote.estado = estado_vendido
      lote.save()

    msg = 'El contrato #{} ha sido cancelado completamente'.format(contrato.id)
  else:
    msg = 'Pago de la cuota ha sido registrado'

  # PARA MOSTRAR LA NUEVA CUOTA POR PAGAR
  cliente = Cliente.objects.get(pk = cuota.plan_pagos.contrato.cliente.identidad )

  contratos = Contrato.objects.filter(cliente=cliente, estado=True, anulado = False, tipo_venta = 'credito')

  html = ''

  if contratos:
    hoy = datetime.now()

    for contrato in contratos:
      lotes = ''
      fecha_pago = ''

      try:
        plan = PlanPagos.objects.get(contrato=contrato, estado=True)
        cuota_a_pagar = DetallePlanPagos.objects.filter(plan_pagos=plan, cuota_pagada=False).order_by('numero_cuota').first()

        # la ultima cuota pagada solo la tendrán los contratos que ya tengan al menos la primera cuota realizada
        ultima_cuota_pagada = DetallePlanPagos.objects.filter(plan_pagos=plan, cuota_pagada=True, activo=True).order_by('numero_cuota').last()

        saldo_amortizacion = None
        fecha_ultimo_pago = None

        if not ultima_cuota_pagada:
          if not plan.saldo_deuda:
            saldo_amortizacion = plan.contrato.monto_contrato_despues_de_prima
          else:
            saldo_amortizacion = plan.saldo_deuda
            fecha_ultimo_pago = plan.fecha_creacion.strftime("%d/%m/%Y")
        else:
          if ultima_cuota_pagada.nuevo_saldo:
            saldo_amortizacion = ultima_cuota_pagada.nuevo_saldo
          else:
            saldo_amortizacion = ultima_cuota_pagada.amortizacion

          fecha_ultimo_pago = ultima_cuota_pagada.fecha_pago.strftime("%d/%m/%Y")

        url_procesar_pago = reverse('pagos:procesar_pago_cuota')
        url_realizar_abono = reverse('pagos:realizar_abono')
        url_plan_pagos = reverse('pagos:detalle_plan_pagos', args=[contrato.id])

        # ya que no se puede comparar date (fecha maxima pago) con datetime (fecha de hoy)
        fecha_maxima_pago = datetime.combine(cuota_a_pagar.fecha_maxima_pago, datetime.min.time())
        if hoy < fecha_maxima_pago:
          fecha_pago += '<span class="text-success"><strong>{}</strong></span>'.format(cuota_a_pagar.fecha_maxima_pago.strftime('%d/%m/%Y'))
        else:
          fecha_pago += '''
            <span class="text-danger"><strong>{}</strong></span>
          '''.format(cuota_a_pagar.fecha_maxima_pago)

        for lote in contrato.lotes.all():
          lotes += '''
            <span class="badge badge-light">{}</span><br>
          '''.format(lote)

        fup = '<span class="text-dark"><strong>{0}</strong></span>'.format(fecha_ultimo_pago) if fecha_ultimo_pago else ''

        cuota_pagar = 0
        if float(saldo_amortizacion) < float(plan.cuota):
          cuota_pagar = float(saldo_amortizacion) + float(cuota_a_pagar.pago_intereses)
        else:
          cuota_pagar = plan.cuota
        
        fecha_hoy = datetime.now().strftime('%Y-%m-%d')

        html += '''
          <div class="shadow-none p-3 mb-2 mt-2 bg-light rounded" id="div-cuota-{5}">
            <h5><span class="badge badge-success">Cuota por pagar: #{1}</span> <small><a href="{9}">Contrato #{0}</a></small></h5>
            {3}
            
            <table class="table table-sm mt-4">
              <tr>
                <td>Fecha del último pago:</td>
                <td>{10}</td>
              </tr>
              <tr>
                <td>Saldo:</td>
                <td><span class="text-danger"><strong>L{8:,}</strong></span></td>
              </tr>
              <tr>
                <td>Fecha máxima de pago:</td>
                <td>{4}</td>
              </tr>
              <tr>
                <td>Valor de la cuota:</td>
                <td><span class="text-info"><strong>L{2:,}</strong></span></td>
              </tr>
              <tr>
                <td>Fecha del pago:</td>
                <td><input type="date" id="fecha-pago-{5}" value="{11}" /></td>
              </tr>
            </table>

            <button class="btn btn-primary btn-realizar-pago" data-cuota-id="{5}" data-url="{6}">
              Registrar pago <i class="fas fa-fw fa-money-bill"></i></a>
            </button>
            <button class="btn btn-info btn-realizar-abono" data-cuota-id="{5}" data-url="{7}">
              Realizar abono <i class="fas fa-fw fa-plus"></i></a>
            </button>
          </div>
        '''.format(contrato.id, cuota_a_pagar.numero_cuota, plan.cuota, lotes, fecha_pago, cuota_a_pagar.id, url_procesar_pago, url_realizar_abono, saldo_amortizacion, url_plan_pagos, fup, fecha_hoy)

      except Exception as e:
        html += '<div class="shadow-none p-3 mb-2 mt-2 bg-light rounded">{}</div>'.format(e)
  else:
    html += '''
      <div class="alert alert-warning mt-2" role="alert">
        Este cliente no tiene contratos pendientes
      </div>
    '''

  return JsonResponse({'con_exito': True, 'msg': msg, 'html': html})

@login_required()
def pagos_del_mes(request):
  anios = DetallePlanPagos.objects.dates('fecha_pago', 'year', order='DESC')

  if request.GET.get('mes') and request.GET.get('anio'):
    mes = int(request.GET.get('mes'))
    anio = int(request.GET.get('anio'))
  else:
    mes = datetime.now().month
    anio = datetime.now().year

  primas_mes = Contrato.objects.filter(fecha_adquisicion__month = mes, fecha_adquisicion__year = anio, tipo_venta = 'credito')
  pagos_mes = DetallePlanPagos.objects.filter(fecha_pago__month = mes, fecha_pago__year = anio).order_by('-fecha_pago')
  abonos_mes_misma_cuota = DetallePlanPagos.objects.filter(fecha_pago__month = mes, fecha_pago__year = anio, abono_a_capital__isnull=False).order_by('-fecha_pago')
  abonos_mes = PlanPagos.objects.filter(fecha_creacion__month = mes, fecha_creacion__year = anio, abono__isnull = False).order_by('-fecha_creacion')
  contratos_contado = Contrato.objects.filter(fecha_adquisicion__month = mes, fecha_adquisicion__year = anio, tipo_venta = 'contado')
  planes_saldo_cancelado = PlanPagos.objects.filter(fecha_saldo_cancelado__month = mes, fecha_saldo_cancelado__year = anio, estado = False, saldo_restante_cancelado = True)

  total_mes_primas = Contrato.objects.filter(fecha_adquisicion__month = mes, fecha_adquisicion__year = anio).aggregate(suma = Sum('prima'))
  total_mes_cuotas = 0 #pagos_mes.aggregate(suma = Sum('plan_pagos__cuota'))
  for pago in pagos_mes:
    if pago.pago_intereses:
      total_mes_cuotas += (float(pago.pago_intereses) + float(pago.pago_capital))
    else:
      total_mes_cuotas += float(pago.plan_pagos.cuota)

  total_mes_abonos = abonos_mes.aggregate(suma = Sum('abono'))
  total_mes_abonos_misma_cuota = abonos_mes_misma_cuota.aggregate(suma = Sum('abono_a_capital'))
  total_contratos_contado = contratos_contado.aggregate(suma = Sum('lotes__precio'))
  total_planes_saldo_cancelado = PlanPagos.objects.filter(fecha_saldo_cancelado__month = mes, fecha_saldo_cancelado__year = anio, estado = False, saldo_restante_cancelado = True).aggregate(suma = Sum('monto_saldo_cancelado'))

  total_cuotas_primas = 0

  if total_mes_primas['suma']:
    total_cuotas_primas += float(total_mes_primas['suma'])

  if total_mes_cuotas:
    total_cuotas_primas += float(total_mes_cuotas)

  if total_mes_abonos['suma']:
    total_cuotas_primas += float(total_mes_abonos['suma'])
  
  if total_mes_abonos_misma_cuota['suma']:
    total_cuotas_primas += float(total_mes_abonos_misma_cuota['suma'])

  if total_contratos_contado['suma']:
    total_cuotas_primas += float(total_contratos_contado['suma'])

  if total_planes_saldo_cancelado['suma']:
    total_cuotas_primas += float(total_planes_saldo_cancelado['suma'])

  ctx = {
    'anios': anios,
    'aniovar': anio,
    'mes': mes,
    'pagos_mes': pagos_mes,
    'primas_mes': primas_mes,
    'abonos_mes': abonos_mes,
    'abonos_mes_misma_cuota': abonos_mes_misma_cuota,
    'total_mes': total_cuotas_primas,
    'contratos_contado': contratos_contado,
    'planes_saldo_cancelado': planes_saldo_cancelado,
  }

  return render(request, 'app_pagos/pagos_del_mes.html', ctx)

@login_required()
def realizar_abono(request):

  if request.is_ajax():
    id = request.GET.get('id')
    proceso = request.GET.get('proceso')
    abono = request.GET.get('abono')
    plazo = request.GET.get('plazo')
    cuota = request.GET.get('cuota')
    saldo = request.GET.get('saldo')

    if proceso == 'verificar-mora':
      cuota = DetallePlanPagos.objects.get(pk=id)
      cuota_por_pagar = DetallePlanPagos.objects.filter(plan_pagos = cuota.plan_pagos, cuota_pagada = False, activo=True).order_by('numero_cuota').first()
      ultima_cuota_pagada = DetallePlanPagos.objects.filter(plan_pagos = cuota.plan_pagos, cuota_pagada = True, activo=True).order_by('numero_cuota').last()
      fecha_dt_cuota_por_pagar = datetime.combine(cuota_por_pagar.fecha_maxima_pago, datetime.min.time())

      hoy = datetime.now()

      if hoy > fecha_dt_cuota_por_pagar:
        meses = DetallePlanPagos.objects.filter(
          plan_pagos = cuota.plan_pagos,
          cuota_pagada = False,
          fecha_maxima_pago__lt=hoy).count()

        return JsonResponse({'con_exito': False, 'msg': 'No puede abonar ya que tiene {} cuota(s) atrasada(s)'.format(meses)})
      else:

        # hay ultima cuota cuando al menos se ha pagado una cuota
        if ultima_cuota_pagada:
          amor = ultima_cuota_pagada.amortizacion if not ultima_cuota_pagada.nuevo_saldo else ultima_cuota_pagada.nuevo_saldo
        else:
          # SI NO HAY ULTIMA CUOTA PAGADA
          # Esto sucedera si al crear el plan, en vez de hacer el pago de una cuota, se hace un abono
          # ...el plan activo no tiene saldo_deuda, por tanto, se procede a calcular el saldo basado en
          # ...la suma de los lotes, menos el monto de prima que pago el cliente al inicio del contrato
          if not cuota.plan_pagos.saldo_deuda:
            monto_lotes = 0
            for lote in cuota.plan_pagos.contrato.lotes.all():
              monto_lotes += float(lote.precio)

            amor = monto_lotes - float(cuota.plan_pagos.contrato.prima)
          else:
            # Al no haber ultima cuota pagada y el plan tenga saldo_deuda, significa que es un plan nuevo que
            # ...arrastro el saldo de la deuda pendiente en el plan anterior y se usa para mostrarlo al usuario
            # ...cuando quiera hacerse otro abono (un plan nuevo)
            amor = cuota.plan_pagos.saldo_deuda

        return JsonResponse({
          'con_exito': True, 
          'msg': 'Puede realizar abonos', 
          'tasa': float(cuota.plan_pagos.contrato.tasa.strip('%')) / 100, 
          'saldo_pendiente': 'L{:,}'.format(amor), 
          'id_contrato': cuota.plan_pagos.contrato.id, 
          'cliente': str(cuota.plan_pagos.contrato.cliente),
          'cuota': round(float(cuota.plan_pagos.cuota), 2)
        })
        #return JsonResponse({'con_exito': True, 'msg': 'Puede realizar abonos', 'tasa': float(cuota.plan_pagos.contrato.tasa.strip('%')) / 100, 'saldo_pendiente': 'L{:,}'.format(cuota.plan_pagos.saldo_deuda), 'id_contrato': cuota.plan_pagos.contrato.id, 'cliente': str(cuota.plan_pagos.contrato.cliente)})

    elif proceso == 'recalcular-deuda':
      contrato = Contrato.objects.get(pk=id)
      plan_activo = PlanPagos.objects.get(contrato = contrato, estado = True)
      ultima_cuota_pagada = DetallePlanPagos.objects.filter(plan_pagos = plan_activo, cuota_pagada = True, activo=True).order_by('numero_cuota').last()
      con_exito = None
      nuevo_saldo = 0

      if ultima_cuota_pagada:
        saldo = ultima_cuota_pagada.nuevo_saldo if ultima_cuota_pagada.nuevo_saldo else ultima_cuota_pagada.amortizacion
        # si el abono es mayor que el saldo
        if float(abono) <= float(saldo):
          nuevo_saldo = float(saldo) - float(abono)
          con_exito = True
        else:
          con_exito = False
      else:
        if not plan_activo.saldo_deuda:
          monto_lotes = 0
          for lote in contrato.lotes.all():
            monto_lotes += float(lote.precio)

          monto_lotes -= float(contrato.prima)
        else:
          monto_lotes = float(plan_activo.saldo_deuda)

        if float(abono) <= monto_lotes:
          nuevo_saldo = monto_lotes - float(abono)
          con_exito = True
        else:
          con_exito = False

      return JsonResponse({'con_exito': con_exito, 'nuevo_saldo_float': float(abono), 'id_contrato': contrato.id, 'nuevo_saldo': '{:,}'.format(round(nuevo_saldo, 2))})

    elif proceso == 'crear-plan':
      contrato = Contrato.objects.get(pk=id)
      plan_activo = PlanPagos.objects.get(contrato = contrato, estado = True)
      plan_activo.estado = False
      plan_activo.save()

      # crear nuevo plan
      plan_nuevo = PlanPagos.objects.create(
        numero = plan_activo.numero + 1,
        contrato = contrato,
        abono = abono,
        meses = plazo,
        saldo_deuda = float(saldo) - float(abono),
        estado = True,
        cuota = cuota
      )

      hoy = datetime.now()

      # Obtener fecha de la ultima cuota pagada del plan activo (plan desactivado)
      ultima_cuota = plan_activo.detalleplanpagos_set.filter(cuota_pagada=True).order_by('fecha_pago').last()

      # Fecha 5 del mes en que se está creando el nuevo plan
      #mes_dia_cinco = datetime(hoy.year, hoy.month, 5)
      mes_dia_cinco = ultima_cuota.fecha_maxima_pago

      # dias del mes actual (mes en que se registra el plan)
      dias_mes_actual = calendar.monthrange(mes_dia_cinco.year, mes_dia_cinco.month)[1]

      # Fecha 5 del siguiente mes
      # Este mes corresponde a la primera cuota, pero tiene hasta el 5 del siguiente para pagar
      fecha_maxima_pago = mes_dia_cinco + timedelta(days=dias_mes_actual)

      tasa = float(contrato.tasa.strip('%')) / 100 / 12
      monto = float(plan_nuevo.saldo_deuda)
      cuota = float(cuota)

      for i in range(1, int(plazo) + 1):
        intereses = monto * tasa
        capital = cuota - intereses
        monto = monto - capital

        c = DetallePlanPagos.objects.create(
          plan_pagos = plan_nuevo,
          numero_cuota = i,
          cuota_capital = capital,
          cuota_intereses = intereses,
          amortizacion = monto,
          fecha_maxima_pago = fecha_maxima_pago
        )

        dias_mes_siguiente = calendar.monthrange(fecha_maxima_pago.year, fecha_maxima_pago.month)[1]

        # Fecha 5 del siguiente mes
        # Este mes corresponde a la primera cuota, pero tiene hasta el 5 del siguiente para pagar
        fecha_maxima_pago = fecha_maxima_pago + timedelta(days=dias_mes_siguiente)

      url_detalle_plan = reverse('pagos:detalle_plan_pagos', args=[contrato.id])

      return JsonResponse({'url': url_detalle_plan, 'msg': 'Se ha creado un nuevo plan de pagos'})
    
    elif proceso == 'abonar-a-capital':
      contrato = Contrato.objects.get(pk=id)
      plan_activo = PlanPagos.objects.get(contrato = contrato, estado = True)

      ultima_cuota_pagada = plan_activo.detalleplanpagos_set.filter(cuota_pagada=True, abono_a_capital__isnull=True, activo=True).order_by('fecha_maxima_pago').last()
      if ultima_cuota_pagada:
        #cuota_anterior = plan_activo.detalleplanpagos_set.filter(numero_cuota = ultima_cuota_pagada.numero_cuota - 1).order_by('fecha_maxima_pago').last()
        ultimo_saldo_amortizado = 0

        if ultima_cuota_pagada.nuevo_saldo:
          ultimo_saldo_amortizado = float(ultima_cuota_pagada.nuevo_saldo)
        else:
          ultimo_saldo_amortizado = float(ultima_cuota_pagada.amortizacion)

        ultima_cuota_pagada.abono_a_capital = abono
        ultima_cuota_pagada.abono_registrado_por = request.user
        ultima_cuota_pagada.nuevo_saldo = ultimo_saldo_amortizado - float(abono)
        ultima_cuota_pagada.save()

        plan_activo.saldo_deuda = ultima_cuota_pagada.nuevo_saldo
        plan_activo.save()

        nuevo_saldo = ultima_cuota_pagada.nuevo_saldo
        tasa_contrato = int(contrato.tasa.replace('%', '')) / 12.0 / 100.0
        siguientes_cuotas = plan_activo.detalleplanpagos_set.filter(cuota_pagada=False).order_by('fecha_maxima_pago')
        for cuota in siguientes_cuotas:
          nuevo_pago_interes = nuevo_saldo * tasa_contrato
          nuevo_pago_capital = float(plan_activo.cuota) - float(nuevo_pago_interes)

          if nuevo_pago_capital > nuevo_saldo:
            nuevo_pago_capital = nuevo_saldo
            nuevo_saldo = 0
          else:
            nuevo_saldo = nuevo_saldo - nuevo_pago_capital

          cuota.nuevo_saldo = nuevo_saldo
          cuota.pago_intereses = nuevo_pago_interes
          cuota.pago_capital = nuevo_pago_capital
          cuota.activo = nuevo_pago_interes > 0
          cuota.cuota_pagada = nuevo_pago_interes == 0
          cuota.save()

        url_detalle_plan = reverse('pagos:detalle_plan_pagos', args=[contrato.id])
        
        return JsonResponse({'url': url_detalle_plan, 'msg': 'Abono aplicado', 'ok': True})
      else:
        return JsonResponse({'msg': 'El cliente debe estar al dia primero', 'ok': False})

@login_required()
def cancelar_deuda(request):
  # id contrato
  id = request.GET.get('id')
  saldo_restante = request.GET.get('saldo_restante')

  contrato = Contrato.objects.get(pk=id)
  contrato.estado = False
  contrato.save()

  plan = PlanPagos.objects.get(contrato=contrato, estado=True)
  plan.saldo_restante_cancelado = True
  plan.monto_saldo_cancelado = float(saldo_restante)
  plan.estado = False
  plan.fecha_saldo_cancelado = datetime.now()
  plan.save()

  # Cambiar el estado de los lotes
  estado_vendido = EstadoLote.objects.get(descripcion = 'Vendido')
  for lote in contrato.lotes.all():
    lote.estado = estado_vendido
    lote.save()

  url_detalle_plan = reverse('pagos:detalle_plan_pagos', args=[contrato.id])

  return JsonResponse({'msg': 'El contrato ha sido cancelado completamente', 'url': url_detalle_plan})

@login_required()
def cambiar_contrasena_view(request):
  form = MyPasswordChangeForm(request.user)

  return render(request, 'app_pagos/cambiar_contrasena.html', {'form': form})

@login_required()
def guardar_nueva_contrasena(request):
  if request.method == 'POST':
    form = MyPasswordChangeForm(user=request.user, data=request.POST)
    if form.is_valid():
      form.save()
      logout(request)
      return HttpResponseRedirect('/')
    else:
      return render(request, 'app_pagos/cambiar_contrasena.html', {'form': form})

  else:
    form = PasswordChangeForm(user=request.user)

@login_required()
def cotizacion_view(request):
  form = CotizacionForm()
  return render(request, 'app_pagos/cotizacion.html', {'form': form})

@login_required()
def generar_cotizacion(request):
  if request.method == 'POST':
    lotes = request.POST.getlist('lotes')
    periodos = request.POST.get('periodos')
    prima = request.POST.get('prima')
    tasa = request.POST.get('tasa')
    cliente = request.POST.get('cliente')

    if cliente == '':
      return HttpResponseRedirect(reverse('pagos:cotizacion_view'))

    elif lotes == []:
      return HttpResponseRedirect(reverse('pagos:cotizacion_view'))

    elif periodos == '':
      return HttpResponseRedirect(reverse('pagos:cotizacion_view'))

    elif prima == '':
      return HttpResponseRedirect(reverse('pagos:cotizacion_view'))

    elif tasa == '':
      return HttpResponseRedirect(reverse('pagos:cotizacion_view'))

    else:
      # generar la cotizacion
      periodo = Periodo.objects.get(pk = int(periodos))

      monto_total_lotes = 0

      for lote_id in lotes:
        lote = Lote.objects.get(pk = int(lote_id))
        monto_total_lotes += float(lote.precio)

      monto_despues_de_prima = monto_total_lotes - float(prima)
      meses = periodo.cantidad_anios * 12
      tasa = float(tasa.strip('%')) / 100 / 12

      cuota = (monto_despues_de_prima * tasa) / (1 - (1 + tasa) ** -meses)

      hoy = datetime.now()

      # Fecha 5 del mes en que se realiza la cotizacion
      mes_dia_cinco = datetime(hoy.year, hoy.month, 5)

      # dias del mes actual (mes en que se registra la venta)
      dias_mes_actual = calendar.monthrange(mes_dia_cinco.year, mes_dia_cinco.month)[1]

      # Fecha 5 del siguiente mes
      # Este mes corresponde a la primera cuota, pero tiene hasta el 5 del siguiente para pagar
      mes_siguiente = mes_dia_cinco + timedelta(days=dias_mes_actual)

      html = '''
        <table class="table table-sm table-bordered table-font-small">
          <thead class="thead-dark">
            <tr class="text-center">
              <th>Cuota</th>
              <th>Fecha pago</th>
              <th>Pago a capital</th>
              <th>Pago a intereses</th>
              <th>Saldo</th>
            </tr>
          </thead>
      '''

      for i in range(1, meses + 1):
        intereses = monto_despues_de_prima * tasa
        capital = cuota - intereses
        monto_despues_de_prima = monto_despues_de_prima - capital

        # dias del mes de la cuota (i)
        dias_mes_cuota = calendar.monthrange(mes_siguiente.year, mes_siguiente.month)[1]

        # fecha maxima para pagar la primera cuota
        fecha_maxima_pago = mes_siguiente + timedelta(days = dias_mes_cuota)

        # generar el html
        html += '''
          <tr>
            <td class="cuota">Cuota {}</td>
            <td class="fecha">{}</td>
            <td>{:,}</td>
            <td>{:,}</td>
            <td><div class="text-right">{:,}</div></td>
          </tr>
        '''.format(i, fecha_maxima_pago.strftime("%d/%m/%Y"), round(capital, 2), round(intereses, 2), round(monto_despues_de_prima, 2))

        mes_siguiente = fecha_maxima_pago

      html += '</table>'

      ctx = {
        'html': html,
        'cliente': cliente,
        'prima': 'L{:,}'.format(round(float(prima), 2)),
        'tasa': tasa * 100 * 12,
        'periodo': periodo.cantidad_anios,
        'cuota': 'L{:,}'.format(round(cuota, 2)),
        'fecha': datetime.now()
      }

      return render(request, 'app_pagos/cotizacion_pdf.html', ctx)

@login_required()
def info_contrato_contado(request, id):

  try:
    contrato = Contrato.objects.get(pk=id)
    monto_total_lotes = 0

    for lote in contrato.lotes.all():
      monto_total_lotes += float(lote.precio)

  except:
    contrato = None

  ctx = {
    'id': id,
    'contrato': contrato,
    'monto_total_lotes': monto_total_lotes
  }

  return render(request, 'app_pagos/info_contrato_contado.html', ctx)

@login_required()
def anular_contrato(request, idc):
  contrato = Contrato.objects.get(pk=idc)
  contrato.anulado = True
  contrato.save()

  # Volver disponibles los lotes
  disponible = EstadoLote.objects.get(pk=1)
  for lote in contrato.lotes.all():
    lote.estado = disponible
    lote.save()

  return HttpResponseRedirect(reverse('pagos:contrato', args=['todos']))

@login_required()
def estado_cuenta_view(request, idc):
  contrato = Contrato.objects.get(pk=idc)
  planes = contrato.planpagos_set.all().order_by('-id')

  html = ''
  for plan in planes:
    filas = ''
    cuotas = plan.detalleplanpagos_set.filter(activo=True, cuota_pagada=True)

    for i, cuota in enumerate(cuotas, start=1):
      
      es_ultima = i == cuotas.count()
      if es_ultima:
        if cuota.abono_a_capital:
          abono = cuota.abono_a_capital
        elif cuota.plan_pagos.monto_saldo_cancelado:
          abono = cuota.plan_pagos.monto_saldo_cancelado
        else:
          abono = 0
      else:
        abono = cuota.abono_a_capital if cuota.abono_a_capital else 0
        

      print(i, cuotas.count(), i == cuotas.count(), abono)

      if cuota.pago_intereses:
        filas += f'''
          <tr>
            <td class='text-center'>{cuota.numero_cuota}</td>
            <td class='text-center'>{cuota.fecha_maxima_pago.strftime('%d.%m.%y')}/{cuota.fecha_pago.strftime('%d.%m.%y') if cuota.fecha_pago else 'N.A'}</td>
            <td class='text-right'>L. {abono:,}</td>
            <td class='text-right'>L. {cuota.pago_capital:,}</td>
            <td class='text-right'>L. {cuota.pago_intereses:,}</td>
            <td class='text-right'>L. {cuota.nuevo_saldo:,}</td>
            <td class='text-center'>{"Pag." if cuota.cuota_pagada else "-"}</td>
          </tr>
        '''
      else:
        filas += f'''
          <tr>
            <td class='text-center'>{cuota.numero_cuota}</td>
            <td class='text-center'>{cuota.fecha_maxima_pago.strftime('%d.%m.%y')}/{cuota.fecha_pago.strftime('%d.%m.%y') if cuota.fecha_pago else 'N.A'}</td>
            <td class='text-right'>L. {abono:,}</td>
            <td class='text-right'>L. {cuota.cuota_capital:,}</td>
            <td class='text-right'>L. {cuota.cuota_intereses:,}</td>
            <td class='text-right'>L. {cuota.amortizacion:,}</td>
            <td class='text-center'>{"Pag." if cuota.cuota_pagada else "-"}</td>
          </tr>
        '''

    if filas == '':
      filas = '''
        <tr>
          <td colspan='7' class='text-center'>No hay pagos aún</td>
        </tr>
      '''

    tabla = f'''
      <table class="table table-sm table-bordered table-font-small" style="width: 100%">
        <thead class="thead-dark">
          <tr class="text-center">
            <th>#C</th>
            <th>F. Cuota/Pago</th>
            <th>Abono</th>
            <th>C.Cap</th>
            <th>C.Int</th>
            <th>Saldo</th>
            <th>Obs.</th>
          </tr>
        </thead>
        <tbody>{filas}</tbody>
      </table>
    '''

    html += f'''
      <div>
        <h5>Plan #{plan.numero} - Cuota: L{plan.cuota:,}{f" - Abono al plan: L{plan.abono:,}" if plan.abono else ""}</h5>
        {tabla}
      </div>
    '''
  
  ctx = {
    'html': html, 
    'idc': idc, 
    'adquirido_en': contrato.fecha_adquisicion.strftime('%d/%m/%Y'),
    'contrato': contrato
  }

  return render(request, 'app_pagos/estado_cuenta_pdf.html', ctx)

