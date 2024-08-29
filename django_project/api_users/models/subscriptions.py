from django.db import models


class CustomerSubscription(models.Model):
    codename = models.CharField(
        max_length=50, unique=True, verbose_name="Кодовое имя")

    name = models.CharField(max_length=100, verbose_name="Название тарифа")
    price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Стоимость")
    days_without_payment = models.IntegerField(
        verbose_name="Количество дней без оплаты")

    class Meta:
        verbose_name = "Тариф"
        verbose_name_plural = "Тарифы Заказчик"

    def __str__(self):
        return self.name


class TransporterSubscription(models.Model):
    codename = models.CharField(
        max_length=50, unique=True, verbose_name="Кодовое имя")

    name = models.CharField(max_length=100, verbose_name="Название тарифа")
    price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Стоимость")
    win_percentage_fee = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="% от суммы выигранной перевозки")
    days_without_payment = models.IntegerField(
        verbose_name="Количество дней без оплаты")

    class Meta:
        verbose_name = "Тариф"
        verbose_name_plural = "Тарифы Перевозчик"

    def __str__(self):
        return self.name
