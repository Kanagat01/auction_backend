from django.db import models
from django.contrib.auth.models import AbstractUser


class UserTypes:
    CUSTOMER_COMPANY = 'customer_company'
    CUSTOMER_MANAGER = 'customer_manager'
    TRANSPORTER_COMPANY = 'transporter_company'
    TRANSPORTER_MANAGER = 'transporter_manager'
    ORDER_VIEWER = 'order_viewer'
    DRIVER = 'driver'
    SUPER_ADMIN = 'super_admin'

    @classmethod
    def choices(cls):
        return (
            (cls.CUSTOMER_COMPANY, 'Заказчик (компания)'),
            (cls.CUSTOMER_MANAGER, 'Заказчик (менеджер)'),
            (cls.TRANSPORTER_COMPANY, 'Перевозчик (компания)'),
            (cls.TRANSPORTER_MANAGER, 'Перевозчик (менеджер)'),
            (cls.ORDER_VIEWER, 'Просмотрщик заказов'),
            (cls.DRIVER, 'Водитель'),
            (cls.SUPER_ADMIN, 'Супер админ'),
        )


class UserModel(AbstractUser):
    email = models.EmailField(
        unique=True, verbose_name='Электронная почта', max_length=300)
    blocked = models.BooleanField(default=False, verbose_name='Заблокирован')
    user_type = models.CharField(
        max_length=20, choices=UserTypes.choices(), null=False, verbose_name='Тип')
    full_name = models.CharField(max_length=200, )
    REQUIRED_FIELDS = ['full_name', 'user_type', 'email']

    # relationship fields:
    # customer_company
    # customer_manager
    # transporter_company
    # transporter_manager
    # driver_profile
    # order_viewer

    def save(self, *args, **kwargs):
        if not self.id:
            super().save(*args, **kwargs)
            return

        if self.user_type == UserTypes.CUSTOMER_COMPANY and not hasattr(self, 'customer_company'):
            raise UserSaveException(
                f'User {self.id} is "{self.user_type}" but has no "customer_company"')

        if self.user_type == UserTypes.CUSTOMER_MANAGER and not hasattr(self, 'customer_manager'):
            raise UserSaveException(
                f'User {self.id} is "{self.user_type}" but has no "customer_manager"')

        if self.user_type == UserTypes.TRANSPORTER_COMPANY and not hasattr(self, 'transporter_company'):
            raise UserSaveException(
                f'User {self.id} is "{self.user_type}" but has no "transporter_company"')

        if self.user_type == UserTypes.TRANSPORTER_MANAGER and not hasattr(self, 'transporter_manager'):
            raise UserSaveException(
                f'User {self.id} is "{self.user_type}" but has no "transporter_manager"')

        if self.user_type == UserTypes.DRIVER and not hasattr(self, 'driver_profile'):
            raise UserSaveException(
                f'User {self.id} is "{self.user_type}" but has no "driver_profile"')

        if self.user_type == UserTypes.ORDER_VIEWER and not hasattr(self, 'order_viewer'):
            raise UserSaveException(
                f'User {self.id} is "{self.user_type}" but has no "order_viewer"')

        super().save(*args, **kwargs)


class UserSaveException(Exception):
    pass
