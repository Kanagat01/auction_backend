from django.utils import timezone
from django.db import models
from rest_framework.exceptions import ValidationError

from api_users.models import CustomerManager, TransporterManager, CustomerCompany, DriverProfile
from api_auction.models import order_transport


def get_unix_time():
    return int(timezone.now().timestamp())


class OrderStatus:
    unpublished = 'unpublished'
    cancelled = 'cancelled'
    in_auction = 'in_auction'
    in_bidding = 'in_bidding'
    in_direct = 'in_direct'
    being_executed = 'being_executed'
    completed = 'completed'

    @classmethod
    def choices(cls):
        return (
            (cls.unpublished, 'Не опубликован'),
            (cls.cancelled, 'Отменен'),
            (cls.in_auction, 'В аукционе'),
            (cls.in_bidding, 'В торгах'),
            (cls.in_direct, 'В напрямую'),
            (cls.being_executed, 'Выполняется'),
            (cls.completed, 'Завершен'),
        )

    @classmethod
    def publish_to_choices(cls):
        return cls.in_auction, cls.in_bidding, cls.in_direct


class _OrderMake:
    """
    Класс для выполнения действий над заказом
    """

    def __init__(self, order: 'OrderModel'):
        self.order = order

    def cancelled(self):
        """
        Отменить заказ
        Если заказ уже завершен - нельзя отменить

        ВНИМАНИЕ: удаляет все предложения перевозчиков

        :return:
        """
        if self.order.status == OrderStatus.completed:
            raise ValidationError('order_is_completed')

        for i in self.order.offers.all():
            i.delete()

        self.order.transporter_manager = None
        self.order.status = OrderStatus.cancelled
        self.order.save()

    def unpublished(self):
        """
        Снять заказ с публикации (вернуть в заказы)
        Если заказ уже в "заказах" или закончен - нельзя снять с публикации

        ВНИМАНИЕ: отклоняет все предложения перевозчиков

        :return:
        """
        if self.order.status in [OrderStatus.completed, OrderStatus.unpublished]:
            raise ValidationError('order_is_completed_or_unpublished')

        self.order.transporter_manager = None
        self.order.driver = None
        self.order.status = OrderStatus.unpublished
        self.order.offers.all().delete()
        self.order.save()

    def published_to(self, order_type: str):
        """
        Опубликовать заказ в аукционе, торгах или напрямую
        Если заказ не в заказах - нельзя опубликовать
        :param order_type:
        :return:
        """
        if self.order.status != OrderStatus.unpublished:
            raise ValidationError('order_is_not_unpublished')
        if order_type not in OrderStatus.publish_to_choices():
            raise ValidationError('invalid_order_type')

        self.order.status = order_type
        self.order.save()

    def offer_accepted(self, offer):
        """
        Принять предложение перевозчика
        Если заказ не в аукционе, торгах или напрямую - нельзя принять предложение
        :param offer:
        :return:
        """
        if self.order.status not in OrderStatus.publish_to_choices():
            raise ValidationError('order_is_not_in_auction_bidding_direct')

        try:
            self.order.application_type.status = self.order.status
            self.order.application_type.save()
        except OrderApplicationType.DoesNotExist:
            OrderApplicationType.objects.create(
                order=self.order, status=self.order.status)

        self.order.transporter_manager = offer.transporter_manager
        self.order.status = OrderStatus.being_executed
        self.order.save()

    def completed(self):
        """
        Завершить заказ
        Если заказ не выполняется - нельзя завершить
        :return:
        """
        if self.order.status != OrderStatus.being_executed:
            raise ValidationError('order_is_not_being_executed')

        self.order.status = OrderStatus.completed
        self.order.save()

    def cancel_completion(self):
        """
        Отменить завершение заказа
        Если заказ не завершен - нельзя отменить завершение
        :return:
        """
        if self.order.status != OrderStatus.completed:
            raise ValidationError('order_is_not_completed')

        self.order.status = OrderStatus.being_executed
        self.order.save()


class OrderModel(models.Model):
    """
    Модель заказа
    Создается менеджером заказчика (CustomerManager)
    """
    customer_manager = models.ForeignKey(CustomerManager, on_delete=models.CASCADE,
                                         verbose_name='Менеджер Заказчика', related_name='orders')
    transporter_manager = models.ForeignKey(TransporterManager, on_delete=models.SET_NULL,
                                            verbose_name='Менеджер Перевозчика', related_name='orders',
                                            null=True, blank=True)
    driver = models.ForeignKey(DriverProfile, on_delete=models.SET_NULL,
                               verbose_name='Водитель', related_name='orders',
                               null=True, blank=True)
    created_at = models.DateTimeField(
        default=timezone.now, verbose_name='Время создания')
    updated_at = models.DateTimeField(
        default=timezone.now, verbose_name='Время обновления')

    # status
    status = models.CharField(max_length=300, choices=OrderStatus.choices(), verbose_name='Статус заказа',
                              default=OrderStatus.unpublished)

    # must be unique within company (both two fields)
    transportation_number = models.IntegerField(
        default=get_unix_time, verbose_name='Номер транспортировки')

    # other stuff
    start_price = models.PositiveIntegerField(verbose_name='Стартовая цена')
    price_step = models.PositiveIntegerField(verbose_name='Шаг цены')
    comments_for_transporter = models.TextField(null=True, blank=True,
                                                max_length=20_000, verbose_name='Комментарии для перевозчика')
    additional_requirements = models.TextField(null=True, blank=True,
                                               max_length=20_000, verbose_name='Дополнительные требования')

    # requirements for transport
    transport_body_type = models.ForeignKey(order_transport.OrderTransportBodyType, on_delete=models.CASCADE,
                                            verbose_name='Тип кузова транспорта')
    transport_load_type = models.ForeignKey(order_transport.OrderTransportLoadType, on_delete=models.CASCADE,
                                            verbose_name='Тип загрузки транспорта')
    transport_unload_type = models.ForeignKey(order_transport.OrderTransportUnloadType, on_delete=models.CASCADE,
                                              verbose_name='Тип выгрузки транспорта')
    transport_volume = models.PositiveIntegerField(
        verbose_name='Объем ТС (м3)')
    temp_mode = models.CharField(null=True, blank=True,
                                 max_length=300, verbose_name='Температурный режим')
    adr = models.PositiveIntegerField(
        null=True, blank=True, verbose_name='ADR [шт.]')
    transport_body_width = models.PositiveIntegerField(null=True, blank=True,
                                                       verbose_name='Ширина кузова')
    transport_body_length = models.PositiveIntegerField(null=True, blank=True,
                                                        verbose_name='Длина кузова')
    transport_body_height = models.PositiveIntegerField(null=True, blank=True,
                                                        verbose_name='Высота кузова')

    # relationships fields:
    # stages
    # tracking
    # documents
    # offers

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f'{self.id} Заказ'

    @property
    def make(self):
        return _OrderMake(self)

    def is_transporter_manager_allowed(self, transporter_manager: TransporterManager):
        return self.customer_manager.company.is_transporter_company_allowed(transporter_manager.company)

    @staticmethod
    def check_transportation_number(number: int, company: CustomerCompany, pk: int = None):
        if not number or type(number) != int:
            raise ValueError('Number must be int')
        if not company:
            raise ValueError('Company must be set')
        query = OrderModel.objects.filter(
            transportation_number=number, customer_manager__company=company)
        if pk:
            query = query.exclude(pk=pk)
        return query.exists()


class OrderApplicationType(models.Model):
    order = models.OneToOneField(
        OrderModel, on_delete=models.CASCADE, verbose_name="Заказ", related_name="application_type")
    status = models.CharField(
        max_length=300, choices=[
            (OrderStatus.in_auction, 'Аукцион'),
            (OrderStatus.in_bidding, 'Торги'),
            (OrderStatus.in_direct, 'Прямой заказ')], verbose_name='Тип заявки')
