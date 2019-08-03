# Generated by Django 2.2.3 on 2019-08-03 08:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_control_pagos', '0015_auto_20190309_1925'),
    ]

    operations = [
        migrations.AddField(
            model_name='contrato',
            name='anulado',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='planpagos',
            name='fecha_saldo_cancelado',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='planpagos',
            name='monto_saldo_cancelado',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True),
        ),
        migrations.AddField(
            model_name='planpagos',
            name='saldo_restante_cancelado',
            field=models.BooleanField(default=False),
        ),
    ]
