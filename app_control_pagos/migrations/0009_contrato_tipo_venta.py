# Generated by Django 2.1.5 on 2019-02-24 22:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_control_pagos', '0008_auto_20190224_1607'),
    ]

    operations = [
        migrations.AddField(
            model_name='contrato',
            name='tipo_venta',
            field=models.CharField(blank=True, choices=[('Crédito', 'Crédito'), ('Contado', 'Contado')], max_length=7, null=True),
        ),
    ]
