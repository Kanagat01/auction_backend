# Generated by Django 5.0.2 on 2024-08-22 08:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api_auction', '0012_orderdocument_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderloadstage',
            name='completed',
            field=models.BooleanField(default=False, verbose_name='Завершено'),
        ),
        migrations.AddField(
            model_name='orderunloadstage',
            name='completed',
            field=models.BooleanField(default=False, verbose_name='Завершено'),
        ),
    ]