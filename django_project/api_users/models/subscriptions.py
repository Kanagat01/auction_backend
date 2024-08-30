from django.db import models
from django.core.validators import MinValueValidator


class Subscription(models.Model):
    codename = models.CharField(
        max_length=50, unique=True, verbose_name="Кодовое имя")

    name = models.CharField(max_length=100, verbose_name="Название тарифа")
    price = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)], verbose_name="Стоимость")
    days_without_payment = models.IntegerField(
        validators=[MinValueValidator(0)],
        verbose_name="Количество дней без оплаты")

    class Meta:
        abstract = True


class CustomerSubscription(Subscription):
    """
    Тариф для Заказчика
    Обьекты создаются автоматически в миграции 0015
    """

    class Meta:
        verbose_name = "Тариф"
        verbose_name_plural = "Тарифы Заказчик"

    def __str__(self):
        return self.name


class TransporterSubscription(Subscription):
    """
    Тариф для Перевозчика
    Обьекты создаются автоматически в миграции 0015
    """

    win_percentage_fee = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="% от суммы выигранной перевозки")

    class Meta:
        verbose_name = "Тариф"
        verbose_name_plural = "Тарифы Перевозчик"

    def __str__(self):
        return self.name
