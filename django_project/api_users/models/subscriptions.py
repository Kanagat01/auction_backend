from django.db import models


class Subscription(models.Model):
    codename = models.CharField(
        max_length=50, unique=True, verbose_name="Кодовое имя")

    name = models.CharField(max_length=100, verbose_name="Название тарифа")
    price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Стоимость")
    days_without_payment = models.IntegerField(
        verbose_name="Количество дней без оплаты")

    class Meta:
        abstract = True


class CustomerSubscription(Subscription):
    class Meta:
        verbose_name = "Тариф"
        verbose_name_plural = "Тарифы Заказчик"

    def __str__(self):
        return self.name


class TransporterSubscription(Subscription):
    win_percentage_fee = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="% от суммы выигранной перевозки")

    class Meta:
        verbose_name = "Тариф"
        verbose_name_plural = "Тарифы Перевозчик"

    def __str__(self):
        return self.name
