# Generated by Django 5.0.2 on 2024-08-29 03:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api_users', '0013_settings'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customercompany',
            name='subscription',
            field=models.CharField(choices=[('customer_unpaid', 'Заказчик НЕоплаченный'), (
                'customer_paid', 'Заказчик оплаченный')], default='customer_unpaid', null=True, max_length=300, verbose_name='Подписка')
        ),
        migrations.AlterField(
            model_name='transportercompany',
            name='subscription',
            field=models.CharField(choices=[('transporter_unpaid', 'Перевозчик НЕоплаченный'), ('transporter_paid',
                                   'Перевозчик оплаченный')], default='transporter_unpaid', null=True, max_length=300, verbose_name='Подписка')
        ),
    ]