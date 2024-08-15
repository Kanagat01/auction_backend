from django.db import models


class OrderTransportBodyType(models.Model):
    name = models.CharField(
        max_length=300, verbose_name='Название типа кузова транспорта')

    class Meta:
        verbose_name = 'Тип кузова транспорта'
        verbose_name_plural = 'Типы кузовов транспорта'

    def __str__(self):
        return f'{self.pk} Тип кузова транспорта - [{self.name}]'


class OrderTransportLoadType(models.Model):
    name = models.CharField(
        max_length=300, verbose_name='Название типа загрузки транспорта')

    class Meta:
        verbose_name = 'Тип загрузки транспорта'
        verbose_name_plural = 'Типы загрузки транспорта'

    def __str__(self):
        return f'{self.pk} Тип загрузки транспорта - [{self.name}]'


class OrderTransportUnloadType(models.Model):
    name = models.CharField(
        max_length=300, verbose_name='Название типа разгрузки транспорта')

    class Meta:
        verbose_name = 'Тип выгрузки транспорта'
        verbose_name_plural = 'Типы выгрузки транспорта'

    def __str__(self):
        return f'{self.pk} Тип выгрузки транспорта - [{self.name}]'
