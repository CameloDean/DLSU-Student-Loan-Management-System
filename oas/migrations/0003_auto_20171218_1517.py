# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-12-18 07:17
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oas', '0002_auto_20171216_0023'),
    ]

    operations = [
        migrations.AlterField(
            model_name='info',
            name='deadline_of_payment',
            field=models.DateField(default=datetime.date.today),
        ),
    ]
