from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser


class UserTypes:
    CUSTOMER_COMPANY = 'customer_company'
    CUSTOMER_MANAGER = 'customer_manager'
    TRANSPORTER_COMPANY = 'transporter_company'
    TRANSPORTER_MANAGER = 'transporter_manager'
    DRIVER = 'driver'
    SUPER_ADMIN = 'super_admin'

    @classmethod
    def choices(cls):
        return (
            (cls.CUSTOMER_COMPANY, 'Заказчик (компания)'),
            (cls.CUSTOMER_MANAGER, 'Заказчик (менеджер)'),
            (cls.TRANSPORTER_COMPANY, 'Перевозчик (компания)'),
            (cls.TRANSPORTER_MANAGER, 'Перевозчик (менеджер)'),
            (cls.DRIVER, 'Водитель'),
            (cls.SUPER_ADMIN, 'Супер админ'),
        )


class UserModel(AbstractUser):
    email = models.EmailField(max_length=300, blank=True, null=True,
                              verbose_name='Электронная почта')
    user_type = models.CharField(
        max_length=20, choices=UserTypes.choices(), null=False, verbose_name='Тип')
    full_name = models.CharField(max_length=200, verbose_name='Полное имя')
    REQUIRED_FIELDS = ['full_name', 'user_type']

    # relationship fields:
    # customer_company
    # customer_manager
    # transporter_company
    # transporter_manager
    # driver_profile

    def clean(self):
        if self.email:
            if UserModel.objects.exclude(pk=self.pk).filter(email=self.email).exists():
                raise ValidationError({
                    'email': 'Должен быть уникальным',
                })

    def save(self, *args, **kwargs):
        self.clean()
        if not self.pk:
            super().save(*args, **kwargs)
            return

        if self.user_type == UserTypes.CUSTOMER_COMPANY and not hasattr(self, 'customer_company'):
            raise UserSaveException(
                f'User {self.pk} is "{self.user_type}" but has no "customer_company"')

        if self.user_type == UserTypes.CUSTOMER_MANAGER and not hasattr(self, 'customer_manager'):
            raise UserSaveException(
                f'User {self.pk} is "{self.user_type}" but has no "customer_manager"')

        if self.user_type == UserTypes.TRANSPORTER_COMPANY and not hasattr(self, 'transporter_company'):
            raise UserSaveException(
                f'User {self.pk} is "{self.user_type}" but has no "transporter_company"')

        if self.user_type == UserTypes.TRANSPORTER_MANAGER and not hasattr(self, 'transporter_manager'):
            raise UserSaveException(
                f'User {self.pk} is "{self.user_type}" but has no "transporter_manager"')

        if self.user_type == UserTypes.DRIVER and not hasattr(self, 'driver_profile'):
            raise UserSaveException(
                f'User {self.pk} is "{self.user_type}" but has no "driver_profile"')

        super().save(*args, **kwargs)


class UserSaveException(Exception):
    pass


class PasswordReset(models.Model):
    email = models.EmailField()
    token = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
