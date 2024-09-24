from typing import Iterable
from rest_framework.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from api_users.models import TransporterManager, UserModel
from api_notification.models import Notification, NotificationType
from .order import OrderModel, OrderStatus


class OrderTracking(models.Model):
    order = models.OneToOneField(
        OrderModel, on_delete=models.CASCADE, verbose_name='Заказ', related_name='tracking')

    # relationship fields:
    # geopoints

    class Meta:
        verbose_name = 'Отслеживание'
        verbose_name_plural = 'Отслеживание'

    def __str__(self):
        return f'{self.id} Трэкинг - [{self.order}]'


class OrderTrackingGeoPoint(models.Model):
    tracking = models.ForeignKey(OrderTracking, on_delete=models.CASCADE, verbose_name='Отслеживание',
                                 related_name='geopoints')

    latitude = models.FloatField(verbose_name='Широта')
    longitude = models.FloatField(verbose_name='Долгота')

    created_at = models.DateTimeField(
        default=timezone.now, verbose_name='Время создания')

    class Meta:
        verbose_name = 'Геоточка'
        verbose_name_plural = 'Геоточки'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.tracking.order.make.add_or_update_order()

    def __str__(self):
        return f'{self.id} Геоточка - [{self.tracking}]'


class OrderDocument(models.Model):
    order = models.ForeignKey(OrderModel, on_delete=models.CASCADE,
                              verbose_name='Заказ', related_name='documents')

    file = models.FileField(upload_to='documents/', verbose_name='Файл')
    user = models.ForeignKey(UserModel, on_delete=models.SET_NULL,
                             null=True, verbose_name='Пользователь')
    created_at = models.DateTimeField(
        default=timezone.now, verbose_name='Время создания')

    class Meta:
        verbose_name = 'Документ'
        verbose_name_plural = 'Документы'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.order.make.add_or_update_order()

    def __str__(self):
        return f'{self.id} Документ - [{self.order}]'


class OrderOfferStatus:
    none = 'none'
    accepted = 'accepted'
    rejected = 'rejected'

    @classmethod
    def choices(cls):
        return (
            (cls.none, 'None'),
            (cls.accepted, 'Accepted'),
            (cls.rejected, 'Rejected'),
        )


class OrderOffer(models.Model):
    order = models.ForeignKey(
        OrderModel, on_delete=models.CASCADE, verbose_name='Заказ', related_name='offers')
    transporter_manager = models.ForeignKey(TransporterManager, on_delete=models.CASCADE, verbose_name='Перевозчик',
                                            related_name='offers')
    price = models.PositiveIntegerField(verbose_name='Цена')
    created_at = models.DateTimeField(
        default=timezone.now, verbose_name='Время создания')
    status = models.CharField(max_length=20, choices=OrderOfferStatus.choices(), default=OrderOfferStatus.none,
                              verbose_name='Статус')

    class Meta:
        verbose_name = 'Предложение'
        verbose_name_plural = 'Предложения'

    def __str__(self):
        return f'{self.id} Предложение - [{self.order}] - {self.transporter_manager}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.order.make.add_or_update_order()

    def make_rejected(self):
        if self.status != OrderOfferStatus.none:
            raise ValidationError(
                'You can not reject accepted or rejected offer')
        self.status = OrderOfferStatus.rejected
        self.save()

        if self.order.status == OrderStatus.in_direct:
            Notification.objects.create(
                user=self.order.customer_manager.user,
                title=f"Заказ отклонен",
                description=(
                    f"Транспортировка №{self.order.transportation_number} отклонена "
                    f"Перевозчиком {self.transporter_manager.company.company_name}"
                ),
                type=NotificationType.INFO
            )
            tr_managers = self.transporter_manager.company.managers.all()
            exclude_ids = []
            for manager in tr_managers:
                exclude_ids.append(manager.user.id)
                self.order.make.remove_order(
                    user_id=manager.user.id, order_status=self.order.status)

            self.order.make.add_or_update_order(exclude=exclude_ids)

    def make_accepted(self):
        if self.status != OrderOfferStatus.none:
            raise ValidationError('You can not accept rejected offer')

        if self.order.status == OrderStatus.in_direct:
            Notification.objects.create(
                user=self.order.customer_manager.user,
                title=f"Заказ перешел в работу",
                description=(
                    f"Транспортировка №{self.order.transportation_number} принята "
                    f"Перевозчиком {self.transporter_manager.company.company_name}"
                ),
                type=NotificationType.INFO
            )
        else:
            Notification.objects.create(
                user=self.transporter_manager.user,
                title=f"Ваше предложение принято",
                description=(
                    f'Ваше предложение на транспортировку №{self.order.transportation_number} было принято. '
                    'Статус заказа изменен на "Выполняется"'
                ),
                type=NotificationType.NEW_ORDER_BEING_EXECUTED
            )
        self.order.make.offer_accepted(self)

        if self.order.status != OrderStatus.in_direct:
            company = self.order.transporter_manager.company
            company.balance -= self.price * company.subscription.win_percentage_fee / 100
            company.save()
        self.status = OrderOfferStatus.accepted
        self.save()

    @staticmethod
    def get_lowest_price_for(order) -> int:
        offers = order.offers.filter(status=OrderOfferStatus.none)
        if offers.exists():
            return offers.order_by('price').first().price
        return order.start_price
