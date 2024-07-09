from rest_framework.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from api_users.models import TransporterManager
from .order import OrderModel


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

    def __str__(self):
        return f'{self.id} Геоточка - [{self.tracking}]'


class OrderDocument(models.Model):
    order = models.ForeignKey('OrderModel', on_delete=models.CASCADE,
                              verbose_name='Заказ', related_name='documents')

    file = models.FileField(upload_to='documents/', verbose_name='Файл')
    created_at = models.DateTimeField(
        default=timezone.now, verbose_name='Время создания')

    class Meta:
        verbose_name = 'Документ'
        verbose_name_plural = 'Документы'

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

    def make_rejected(self):
        if self.status != OrderOfferStatus.none:
            raise ValidationError(
                'You can not reject accepted or rejected offer')
        self.status = OrderOfferStatus.rejected
        self.save()

    def make_accepted(self):
        if self.status != OrderOfferStatus.none:
            raise ValidationError('You can not accept rejected offer')
        self.order.make.offer_accepted(self)
        self.status = OrderOfferStatus.accepted
        self.save()

    @staticmethod
    def get_lowest_price_for(order: OrderModel) -> int:
        offers = order.offers.filter(status=OrderOfferStatus.none)
        if offers.exists():
            return offers.order_by('price').first().price
        return order.start_price
