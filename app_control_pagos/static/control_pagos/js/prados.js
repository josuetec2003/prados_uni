$(function () {
  $('.chosen').chosen();
  $('[data-toggle="tooltip"]').tooltip();
  $('#id_identidad').mask('0000-0000-00000');
  $('#id_telefono1').mask('0000-0000');
  $('#id_telefono2').mask('0000-0000');

  $('#id_lotes').on('change', function () {
    var url = $(this).attr('data-url');
    var prima = $('#id_prima').val();
    console.log(prima);

    var lotes = [];
    $('#id_lotes option:selected').each(function(index,valor){
        lotes.push(parseInt(valor.value));
    });

    $.get(url, {'desde': 'lotes', 'prima': prima, 'lotes': JSON.stringify(lotes)}, function (data) {
        $('#monto-venta').text(data.monto);
    }, 'json');
  });

  $('#id_prima').on('keypress', function (e) {
    var tecla = e.keyCode || e.which;

    if (tecla == 13)
    {
      var url = $(this).attr('data-url');
      var prima = $(this).val();
      var lotes = [];
      $('#id_lotes option:selected').each(function(index,valor){
          lotes.push(parseInt(valor.value));
      });

      $.get(url, {'desde': 'prima', 'prima': prima, 'lotes': JSON.stringify(lotes)}, function (data) {
        $('#monto-venta').text(data.monto);
      }, 'json');
    }
  });

  $('#btn-vender').on('click', function () {
    var url = $(this).attr('data-url');
    var cliente = $('#id_cliente').val();
    var fecha = $('#id_fecha_adquisicion').val();

    var lotes = [];
    $('#id_lotes option:selected').each(function(index,valor){
        lotes.push(parseInt(valor.value));
    });

    var periodos = $('#id_periodos').val();
    var prima = $('#id_prima').val();
    var tasa = $('#id_tasa').val();
    var tipo_venta = $('#id_tipo_venta').val();

    ctx = {
      'cliente': cliente,
      'fecha': fecha,
      'periodos': periodos,
      'prima': prima,
      'tasa': tasa,
      'tipo_venta': tipo_venta,
      'lotes': JSON.stringify(lotes)
    };

    $.get(url, ctx, function (data) {
      notify(data.style, data.msg);

      if (data.style == 'success')
      {
        setTimeout(function () {
          location.href = data.url_redirect;
        }, 2000);
      }
    }, 'json');
  });

  $('#cbo-tipo-contrato').on('change', function () {
    var tipo = $(this).val();

    location.href = `/s/contrato/${tipo}/`;
  });

  $('#cbo-cliente-pago').on('change', function () {
    var id = $(this).val();
    var url = $(this).attr('data-url');

    if (id)
    {
      $.get(url, {'identidad': id}, function (respuesta) {
        $('#pagos-a-realizar').html(respuesta.html);
      }, 'json');
    } else {
      $('#pagos-a-realizar').empty();
    }

  });

  $(document).on('click', '.btn-realizar-pago', function () {
    $(this).attr('disabled', 'disabled');
    var id = $(this).attr('data-cuota-id');
    var url = $(this).attr('data-url');

    $.get(url, {'id': id}, function (respuesta) {
      if (respuesta.con_exito)
      {
        notify('success', respuesta.msg);

        setTimeout(function () {
          $('#pagos-a-realizar').fadeOut().empty().html(respuesta.html).fadeIn();
        }, 1500);
      }
    }, 'json');
  });

  $(document).on('click', '.btn-realizar-abono', function () {
    var id = $(this).attr('data-cuota-id');
    var url = $(this).attr('data-url');

    $.get(url, {'id': id, 'proceso': 'verificar-mora'}, function (respuesta) {
      if (!respuesta.con_exito)
        notify('warn', respuesta.msg);
      else
      {
        $('#btn-recalcular-id').attr('data-contrato-id', respuesta.id_contrato);
        $('#btn-crear-plan-nuevo').attr('data-contrato-id', respuesta.id_contrato);
        $('#contrato-num').text(respuesta.id_contrato + ' - ' + respuesta.cliente);
        $('#saldo-pendiente').val(respuesta.saldo_pendiente);
        $('#tasa-contrato').val(respuesta.tasa);
        $('#modal-abono').modal();
        $('#nueva-deuda').val('');
        $('#nuevo-plazo').val('');
        $('#nueva-cuota').val('');
        $('#txt-abono').val('');
      }
    }, 'json');
  });

  $('body').on('shown.bs.modal', '#modal-abono', function () {
      $('input#txt-abono', this).focus();
  })

  $('#btn-recalcular-id').on('click', function () {
    var id = $(this).attr('data-contrato-id');
    var url = $(this).data('url');
    var abono = $('#txt-abono').val();

    if (abono == '')
    {
      notify('warn', 'Ingrese el valor del abono');
      $('#txt-abono').focus();
      return;
    }

    $.get(url, {'id': id, 'abono': abono, 'proceso': 'recalcular-deuda'}, function (respuesta) {
      console.log(respuesta.con_exito);
      if (respuesta.con_exito)
      {
        $('#nueva-deuda').val(respuesta.nuevo_saldo);

        if (respuesta.nuevo_saldo == '0.0')
        {
          $('#btn-cancelar-deuda')
            .removeAttr('disabled')
            .attr('data-contrato-id', respuesta.id_contrato)
            .attr('data-saldo-float', respuesta.nuevo_saldo_float);

          $('#btn-crear-plan-nuevo').attr('disabled', 'disabled');
        } else {
          $('#nuevo-plazo').focus();
          $('#btn-cancelar-deuda').attr('disabled', 'disabled');
          $('#btn-crear-plan-nuevo').removeAttr('disabled');
        }
      } else {
        $('#nueva-deuda').val('');
        notify('warn', 'El abono no puede ser mayor al saldo');
        $('#btn-cancelar-deuda').attr('disabled', 'disabled');
        $('#btn-crear-plan-nuevo').removeAttr('disabled');

      }
    }, 'json');
  });

  $('#btn-cancelar-deuda').on('click', function () {
    if (!confirm('Confirma la cancelación de la deuda?')) return false;

    var id = $(this).data('contrato-id');
    var url = $(this).data('url');
    var saldo_restante = $(this).data('saldo-float');

    $.get(url, {'id': id, 'saldo_restante': saldo_restante}, function (respuesta) {
      notify('success', respuesta.msg);

      setTimeout(function () {
        location.href = respuesta.url;
      }, 1500);
    }, 'json');

  })

  $('#btn-nueva-cuota').on('click', function () {
    var nuevo_monto = $('#nueva-deuda').val();
    var tasa = parseFloat($('#tasa-contrato').val()) / 12;
    var nuevo_plazo = $('#nuevo-plazo').val();
    var tipo_plazo = $('#tipo-plazo').val();
    var abono = $('#txt-abono').val();

    if (nuevo_monto == '')
    {
      notify('warn', 'Recalcule la deuda primero');
      $('#txt-abono').focus();
      return false;
    }

    if (abono == '')
    {
      notify('warn', 'Recalcule la deuda primero');
      $('#txt-abono').focus();
      return false;
    }

    if (nuevo_plazo == '')
    {
      notify('warn', 'Ingrese el plazo');
      $('#nuevo-plazo').focus();
      return false;
    }

    if (tipo_plazo == 'anios')
      nuevo_plazo = parseInt(nuevo_plazo) * 12;
    else
      nuevo_plazo = parseInt(nuevo_plazo);

    nuevo_monto = parseFloat(nuevo_monto.replace(/,/g, ''))

    var cuota = (nuevo_monto * tasa) / (1 - Math.pow(1 + tasa, -nuevo_plazo));
    $('#nueva-cuota').val(cuota.toLocaleString(undefined, {maximumFractionDigits: 2}));

    return false;

  });

  $('#btn-filtrar-pagos').on('click', function () {
    var mes = $('#cbo-pagos-mes').val();
    var anio = $('#cbo-pagos-anio').val();
    var url = $(this).attr('data-url');

    location.href = `${url}?mes=${mes}&anio=${anio}`;
  });

  $('#btn-crear-plan-nuevo').on('click', function () {
    var abono = $('#txt-abono').val();
    var nuevo_plazo = $('#nuevo-plazo').val();
    var tipo_plazo = $('#tipo-plazo').val();
    var nueva_cuota = $('#nueva-cuota').val();
    var saldo_pendiente = $('#saldo-pendiente').val();
    var url = $(this).data('url');
    var contrato_id = $(this).data('contrato-id');


    if (abono == '')
    {
      notify('warn', 'Recalcule la deuda primero');
      $('#txt-abono').focus();
      return false;
    }

    if (nueva_cuota == '')
    {
      notify('warn', 'Recalcule la cuota');
      $('#nuevo-plazo').focus();
      return false;
    }

    if (tipo_plazo == 'anios')
      nuevo_plazo = parseInt(nuevo_plazo) * 12;
    else
      nuevo_plazo = parseInt(nuevo_plazo);

    abono = parseFloat(abono)
    nueva_cuota = parseFloat(nueva_cuota.replace(/,/g, ''))
    saldo_pendiente = parseFloat(saldo_pendiente.replace(/,/g, '').replace("L", ""))

    console.log('Abono:', abono);
    console.log('Plazo:', nuevo_plazo);
    console.log('Cuota:', nueva_cuota);

    var ctx = {
      'abono': abono,
      'plazo': nuevo_plazo,
      'cuota': nueva_cuota,
      'id': contrato_id,
      'saldo': saldo_pendiente,
      'proceso': 'crear-plan'
    };

    $.get(url, ctx, function (respuesta) {
      notify('success', respuesta.msg);

      setTimeout(function () {
        location.href = respuesta.url;
      }, 1500);
    }, 'json');

    return false;
  });

})

function notify (style, msg)
{
  $.notify.defaults({ className: style });
  $.notify(msg, {position: 'bottom'});
}

/*
 *   Prados Universitarios
 *   Josué Alfredo Alvarez (Developer)
 *   josuetec2003@gmail.com
 *   +504 9797-8830
 *   instagram.com/josuetec2003
 */









