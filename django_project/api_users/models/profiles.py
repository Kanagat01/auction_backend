from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from api_users.models.subscriptions import *
from api_users.models.user import UserModel


class PhoneNumberValidator(RegexValidator):
    '''Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed'''
    regex = r'^\+?1?\d{9,15}$'
    message = "invalid_phone_number"


class FullNameModel(models.Model):
    full_name = models.CharField(max_length=300, verbose_name="ФИО")


class CustomerCompany(models.Model):
    user = models.OneToOneField(
        UserModel, on_delete=models.CASCADE, related_name='customer_company')
    company_name = models.CharField(
        max_length=200, verbose_name='Название компании')
    subscription = models.CharField(max_length=300, choices=CustomerSubscriptions.choices(),
                                    default=CustomerSubscriptions.FREE, verbose_name='Подписка')
    allowed_transporter_companies = models.ManyToManyField('api_users.TransporterCompany',
                                                           related_name='allowed_customer_companies')

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
        return f'{self.pk} Менеджер заказчика - [{self.user}]'


class TransporterCompany(models.Model):
    user = models.OneToOneField(
        UserModel, on_delete=models.CASCADE, related_name='transporter_company')
    company_name = models.CharField(
        max_length=200, verbose_name='Название компании')
    subscription = models.CharField(max_length=300, choices=TransporterSubscriptions.choices(),
                                    default=TransporterSubscriptions.FREE, verbose_name='Подписка')

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
        return f'{self.pk} Менеджер перевозчика - [{self.user}]'


class DriverProfile(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, limit_choices_to={
                                     'model__in': ('usermodel', 'fullnamemodel')})
    object_id = models.PositiveIntegerField()
    user_or_fullname = GenericForeignKey('content_type', 'object_id')

    companies = models.ManyToManyField(
        TransporterCompany, related_name='drivers')
    birth_date = models.DateField(
        default=timezone.now().date, verbose_name='Дата рождения')
    passport_number = models.CharField(
        max_length=20, verbose_name='Номер паспорта')
    phone_number = models.CharField(
        validators=[PhoneNumberValidator()], max_length=17, verbose_name='Телефон')
    machine_data = models.CharField(
        max_length=300, verbose_name='Данные авто')
    machine_number = models.CharField(
        max_length=20, verbose_name='Номер авто')

    class Meta:
        verbose_name = 'Профиль водителя'
        verbose_name_plural = 'Профили водителей'
        # constraints = [
        #     models.UniqueConstraint(
        #         fields=['content_type', 'object_id', 'user_or_fullname'],
        #         name='unique_driver_profile'
        #     )
        # ]

    def __str__(self):
        return f'{self.pk} Профиль водителя - [{self.user_or_fullname.full_name}]'


class OrderViewer(models.Model):
    user = models.OneToOneField(
        UserModel, on_delete=models.CASCADE, related_name='order_viewer')
    # TODO: Change the name if needed
    order = models.ForeignKey('api_auction.OrderModel',
                              on_delete=models.CASCADE, related_name='viewers')

    class Meta:
        verbose_name = 'Просмотр заказа'
        verbose_name_plural = 'Просмотры заказов'

    def __str__(self):
        return f'{self.pk} Просмотр заказа - [{self.user}]'
