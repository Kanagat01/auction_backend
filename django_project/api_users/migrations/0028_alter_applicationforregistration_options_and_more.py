# Generated by Django 5.0.2 on 2024-10-15 12:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api_users', '0027_applicationforregistration'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='applicationforregistration',
            options={'verbose_name': 'Заявка на регистрацию', 'verbose_name_plural': 'Заявки на регистрацию'},
        ),
        migrations.AddField(
            model_name='settings',
            name='address',
            field=models.CharField(default='', max_length=5000, verbose_name='Адрес'),
            preserve_default=False,
        ),
    ]