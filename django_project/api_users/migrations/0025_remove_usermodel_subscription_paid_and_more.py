# Generated by Django 5.0.2 on 2024-09-12 04:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api_users', '0024_alter_usermodel_full_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='usermodel',
            name='subscription_paid',
        ),
        migrations.AddField(
            model_name='customercompany',
            name='subscription_paid',
            field=models.BooleanField(default=False, verbose_name='Тариф оплачен'),
        ),
        migrations.AddField(
            model_name='transportercompany',
            name='subscription_paid',
            field=models.BooleanField(default=False, verbose_name='Тариф оплачен'),
        ),
    ]