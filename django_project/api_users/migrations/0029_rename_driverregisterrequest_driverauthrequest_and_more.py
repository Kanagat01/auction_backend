# Generated by Django 5.0.2 on 2024-10-29 02:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api_users', '0028_alter_applicationforregistration_options_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='DriverRegisterRequest',
            new_name='DriverAuthRequest',
        ),
        migrations.RemoveField(
            model_name='driverprofile',
            name='birth_date',
        ),
    ]
