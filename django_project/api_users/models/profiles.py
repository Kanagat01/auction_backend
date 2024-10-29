from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db import models
from django.core.validators import RegexValidator

from api_users.models.subscriptions import *
from api_users.models.user import UserModel


class PhoneNumberValidator(RegexValidator):
    '''Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed'''
    regex = r'^\+?1?\d{9,15}$'
    message = "invalid_phone_number"


class DriverProfile(models.Model):
    user = models.OneToOneField(
        UserModel, on_delete=models.CASCADE, related_name='driver_profile')
    passport_number = models.CharField(
        max_length=20, verbose_name='Номер паспорта')
    phone_number = models.CharField(max_length=17, unique=True,
                                    validators=[PhoneNumberValidator()], verbose_name='Телефон')
    machine_data = models.CharField(
        max_length=300, verbose_name='Машина')
    machine_number = models.CharField(
        max_length=20, unique=True, verbose_name='Номер машины')

    class Meta:
        verbose_name = 'Профиль водителя'
        verbose_name_plural = 'Профили водителей'

    def save(self, *args, **kwargs):
        if self.phone_number and self.user.username != self.phone_number:
            self.user.username = self.phone_number
            self.user.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.pk} Профиль водителя - [{self.user.full_name}]'


class BaseCompany(models.Model):
    company_name = models.CharField(
        max_length=200, verbose_name='Название компании')
    balance = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name='Баланс компании'
    )
    subscription_paid = models.BooleanField(
        default=False, verbose_name="Тариф оплачен")
    details = models.TextField(verbose_name="Реквизиты", blank=True, null=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.subscription and not self.subscription_paid and self.balance >= self.subscription.price:
            self.balance -= self.subscription.price
            self.subscription_paid = True
        super().save(*args, **kwargs)

        channel_layer = get_channel_layer()
        user_ids = [self.user.pk, *[m.user.id for m in self.managers.all()]]
        for user_id in user_ids:
            async_to_sync(channel_layer.group_send)(
                f"user_{user_id}", {
                    "type": "update_balance",
                    "new_balance": float(self.balance)
                }
            )


class CustomerCompany(BaseCompany):
    user = models.OneToOneField(
        UserModel, on_delete=models.CASCADE, related_name='customer_company', verbose_name='Пользователь')
    subscription = models.ForeignKey(
        CustomerSubscription, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Тариф')
    allowed_transporter_companies = models.ManyToManyField('api_users.TransporterCompany', blank=True,
                                                           related_name='allowed_customer_companies', verbose_name='Перевозчики компании')

    class Meta:
        verbose_name = 'Компания заказчика'
        verbose_name_plural = 'Компании заказчиков'

    def __str__(self):
        return f'{self.pk} Компания заказчика - [{self.company_name}]'

    def is_transporter_company_allowed(self, transporter_company: 'TransporterCompany'):
        return self.allowed_transporter_companies.filter(pk=transporter_company.pk).exists()


class CustomerManager(models.Model):
    user = models.OneToOneField(
        UserModel, on_delete=models.CASCADE, related_name='customer_manager')
    company = models.ForeignKey(
        CustomerCompany, on_delete=models.CASCADE, related_name='managers')

    class Meta:
        verbose_name = 'Менеджер заказчика'
        verbose_name_plural = 'Менеджеры заказчиков'

    def __str__(self):
        return f'#{self.pk} {self.user.full_name}'


class TransporterCompany(BaseCompany):
    user = models.OneToOneField(
        UserModel, on_delete=models.CASCADE, related_name='transporter_company')
    subscription = models.ForeignKey(
        TransporterSubscription, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Тариф')

    class Meta:
        verbose_name = 'Компания перевозчика'
        verbose_name_plural = 'Компании перевозчиков'

    def __str__(self):
        return f'{self.pk} Компания перевозчика - [{self.company_name}]'

    def get_manager(self) -> 'TransporterManager':
        return self.managers.first()


class TransporterManager(models.Model):
    user = models.OneToOneField(
        UserModel, on_delete=models.CASCADE, related_name='transporter_manager')
    company = models.ForeignKey(
        TransporterCompany, on_delete=models.CASCADE, related_name='managers')

    class Meta:
        verbose_name = 'Менеджер перевозчика'
        verbose_name_plural = 'Менеджеры перевозчиков'

    def __str__(self):
        return f'#{self.pk} {self.user.full_name}'
