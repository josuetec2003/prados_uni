from django.urls import path
from . import views

app_name = 'pagos'

urlpatterns = [
  path('', views.index, name="index"),

  path('clientes/', views.clientes, name="clientes"),
  path('cliente/<str:id>/editar/', views.clientes, name="editar_cliente"),
  path('cliente/guardar/', views.guardar_cliente, name="agregar_cliente"),
  path('cliente/<str:id>/guardar/', views.guardar_cliente, name="guardar_cliente"),

  path('sectores-y-lotes/', views.lotes, name="lotes"),
  path('<str:objetivo>/<int:id>/editar/', views.lotes, name="editar_sector"),
  path('<str:objetivo>/guardar/', views.agregar_sector, name="guardar_sector"),
  path('<str:objetivo>/actualizar/<int:id>/', views.agregar_sector, name="actualizar_sector"),

  path('contrato/<str:tipo>/', views.contrato_view, name="contrato"),
  path('calcular-monto-venta/', views.calcular_monto_venta, name="calcular_monto_venta"),
  path('realizar-venta/', views.realizar_venta, name="realizar_venta"),
  path('contrato-plan/<int:id>/', views.detalle_plan_pagos, name="detalle_plan_pagos"),
  path('registrar-pago/', views.registrar_pago, name="registrar_pago"),
  path('obtener-prestamos-cliente/', views.obtener_prestamos_cliente, name="obtener_prestamos_cliente"),
  path('procesar-pago-cuota/', views.procesar_pago_cuota, name="procesar_pago_cuota"),
  path('pagos-del-mes/', views.pagos_del_mes, name="pagos_del_mes"),
  path('realizar-abono/', views.realizar_abono, name="realizar_abono"),
  path('nueva-contrasena/', views.cambiar_contrasena_view, name="cambiar_contrasena_view"),
  path('guardar-nueva-contrasena/', views.guardar_nueva_contrasena, name="guardar_nueva_contrasena"),
  path('cotizacion/', views.cotizacion_view, name="cotizacion_view"),
  path('generar-cotizacion/', views.generar_cotizacion, name="generar_cotizacion"),
  path('info-contrato-contado/<int:id>/', views.info_contrato_contado, name="info_contrato_contado"),


]
