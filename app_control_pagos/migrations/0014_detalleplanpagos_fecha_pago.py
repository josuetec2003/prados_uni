# Generated by Django 2.1.5 on 2019-03-03 02:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_control_pagos', '0013_contrato_estado'),
    ]

    operations = [
        migrations.AddField(
            model_name='detalleplanpagos',
            name='fecha_pago',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
