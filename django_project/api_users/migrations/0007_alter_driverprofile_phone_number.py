# Generated by Django 5.0.2 on 2024-08-15 10:52

import api_users.models.profiles
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api_users', '0006_alter_driverprofile_machine_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='driverprofile',
            name='phone_number',
            field=models.CharField(max_length=17, unique=True, validators=[api_users.models.profiles.PhoneNumberValidator()], verbose_name='Телефон'),
        ),
    ]