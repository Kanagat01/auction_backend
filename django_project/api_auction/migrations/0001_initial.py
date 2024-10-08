# Generated by Django 5.0.2 on 2024-05-19 15:27

import api_auction.models.order
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='OrderDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='documents/', verbose_name='Файл')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Время создания')),
            ],
            options={
                'verbose_name': 'Документ',
                'verbose_name_plural': 'Документы',
            },
        ),
        migrations.CreateModel(
            name='OrderLoadStage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='Дата')),
                ('time_start', models.TimeField(verbose_name='Время начала')),
                ('time_end', models.TimeField(verbose_name='Время окончания')),
                ('company', models.CharField(max_length=300, verbose_name='Компания')),
                ('address', models.CharField(max_length=5000, verbose_name='Адрес')),
                ('contact_person', models.CharField(max_length=300, verbose_name='Контактное лицо')),
                ('cargo', models.CharField(max_length=300, verbose_name='Груз')),
                ('weight', models.PositiveIntegerField(verbose_name='Вес')),
                ('volume', models.PositiveIntegerField(verbose_name='Объем')),
                ('comments', models.TextField(max_length=20000, verbose_name='Комментарии к поставке')),
            ],
            options={
                'verbose_name': 'Этап загрузки поставки',
                'verbose_name_plural': 'Этапы загрузки поставки',
            },
        ),
        migrations.CreateModel(
            name='OrderModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Время создания')),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Время обновления')),
                ('status', models.CharField(choices=[('unpublished', 'Не опубликован'), ('cancelled', 'Отменен'), ('in_auction', 'В аукционе'), ('in_bidding', 'В торгах'), ('in_direct', 'В напрямую'), ('being_executed', 'Выполняется'), ('completed', 'Завершен')], default='unpublished', max_length=300, verbose_name='Статус заказа')),
                ('transportation_number', models.IntegerField(default=api_auction.models.order.get_unix_time, verbose_name='Номер транспортировки')),
                ('start_price', models.PositiveIntegerField(verbose_name='Стартовая цена')),
                ('price_step', models.PositiveIntegerField(verbose_name='Шаг цены')),
                ('comments_for_transporter', models.TextField(max_length=20000, verbose_name='Комментарии для перевозчика')),
                ('additional_requirements', models.TextField(max_length=20000, verbose_name='Дополнительные требования')),
                ('transport_volume', models.PositiveIntegerField(verbose_name='Объем ТС (м3)')),
                ('temp_mode', models.CharField(max_length=300, verbose_name='Температурный режим')),
                ('adr', models.PositiveIntegerField(default=False, verbose_name='ADR [шт.]')),
                ('transport_body_width', models.PositiveIntegerField(verbose_name='Ширина кузова')),
                ('transport_body_length', models.PositiveIntegerField(verbose_name='Длина кузова')),
                ('transport_body_height', models.PositiveIntegerField(verbose_name='Высота кузова')),
            ],
            options={
                'verbose_name': 'Заказ',
                'verbose_name_plural': 'Заказы',
            },
        ),
        migrations.CreateModel(
            name='OrderOffer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.PositiveIntegerField(verbose_name='Цена')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Время создания')),
                ('status', models.CharField(choices=[('none', 'None'), ('accepted', 'Accepted'), ('rejected', 'Rejected')], default='none', max_length=20, verbose_name='Статус')),
            ],
            options={
                'verbose_name': 'Предложение',
                'verbose_name_plural': 'Предложения',
            },
        ),
        migrations.CreateModel(
            name='OrderStageCouple',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Время создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Время обновления')),
                ('order_stage_number', models.IntegerField(default=api_auction.models.order.get_unix_time, verbose_name='Номер поставки')),
            ],
            options={
                'verbose_name': 'Поставки заказа',
                'verbose_name_plural': 'Поставки заказов',
            },
        ),
        migrations.CreateModel(
            name='OrderTracking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'verbose_name': 'Отслеживание',
                'verbose_name_plural': 'Отслеживание',
            },
        ),
        migrations.CreateModel(
            name='OrderTrackingGeoPoint',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('latitude', models.FloatField(verbose_name='Широта')),
                ('longitude', models.FloatField(verbose_name='Долгота')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Время создания')),
            ],
            options={
                'verbose_name': 'Геоточка',
                'verbose_name_plural': 'Геоточки',
            },
        ),
        migrations.CreateModel(
            name='OrderTransportBodyType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=300, verbose_name='Название типа кузова транспорта')),
            ],
            options={
                'verbose_name': 'Тип кузова транспорта',
                'verbose_name_plural': 'Типы кузовов транспорта',
            },
        ),
        migrations.CreateModel(
            name='OrderTransportLoadType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=300, verbose_name='Название типа загрузки транспорта')),
            ],
            options={
                'verbose_name': 'Тип загрузки транспорта',
                'verbose_name_plural': 'Типы загрузки транспорта',
            },
        ),
        migrations.CreateModel(
            name='OrderTransportUnloadType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=300, verbose_name='Название типа разгрузки транспорта')),
            ],
            options={
                'verbose_name': 'Тип выгрузки транспорта',
                'verbose_name_plural': 'Типы выгрузки транспорта',
            },
        ),
        migrations.CreateModel(
            name='OrderUnloadStage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='Дата')),
                ('time_start', models.TimeField(verbose_name='Время начала')),
                ('time_end', models.TimeField(verbose_name='Время окончания')),
                ('company', models.CharField(max_length=300, verbose_name='Компания')),
                ('address', models.CharField(max_length=5000, verbose_name='Адрес')),
                ('contact_person', models.CharField(max_length=300, verbose_name='Контактное лицо')),
                ('cargo', models.CharField(max_length=300, verbose_name='Груз')),
                ('weight', models.PositiveIntegerField(verbose_name='Вес')),
                ('volume', models.PositiveIntegerField(verbose_name='Объем')),
                ('comments', models.TextField(max_length=20000, verbose_name='Комментарии к поставке')),
            ],
            options={
                'verbose_name': 'Этап выгрузки поставки',
                'verbose_name_plural': 'Этапы выгрузки поставки',
            },
        ),
    ]
