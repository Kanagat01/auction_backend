# Generated by Django 5.0.2 on 2024-09-03 10:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api_users', '0022_alter_usermodel_has_unpaid_subscription'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='usermodel',
            name='has_unpaid_subscription',
        ),
        migrations.AddField(
            model_name='usermodel',
            name='subscription_paid',
            field=models.BooleanField(default=False, verbose_name='Тариф оплачен'),
        ),
    ]
