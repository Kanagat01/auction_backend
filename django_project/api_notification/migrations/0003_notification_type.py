# Generated by Django 5.0.2 on 2024-07-17 00:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api_notification', '0002_alter_notification_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='type',
            field=models.CharField(choices=[('info', 'Информационная'), ('new_order_in_auction', 'Новый заказ в аукционе'), ('new_order_in_bidding', 'Новый заказ в торгах'), ('new_order_in_direct', 'Новый заказ назначен напрямую'), ('new_order_being_executed', 'Новый заказ принят в исполнение')], default=1, max_length=24, verbose_name='Тип'),
            preserve_default=False,
        ),
    ]
