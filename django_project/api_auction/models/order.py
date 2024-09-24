from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from api_users.models import CustomerManager, TransporterManager, CustomerCompany, DriverProfile, UserTypes
from api_auction.models import order_transport
from api_notification.models import Notification, NotificationType


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

    @classmethod
    def get_status_list(cls, user_type: UserTypes):
        status_lst = [cls.cancelled, cls.in_auction, cls.in_bidding,
                      cls.in_direct, cls.being_executed]
        if user_type in [UserTypes.CUSTOMER_COMPANY, UserTypes.CUSTOMER_MANAGER]:
            status_lst.append(cls.unpublished)
        return status_lst


class _OrderMake:
    """
    Класс для выполнения действий над заказом
    """

    def __init__(self, order: 'OrderModel'):
        self.order = order
        self.channel_layer = get_channel_layer()

    def remove_order(self, user_id: int, order_status: str):
        """
        Удаляет заказ в режиме реального времени через сокет
        """
        async_to_sync(self.channel_layer.group_send)(f"user_{user_id}", {
            "type": "remove_order",
            "order_id": self.order.pk,
            "order_status": order_status
        })

    def add_or_update_order(self, exclude: list = None):
        """
        Обновляет заказ в режиме реального времени через сокет
        """
        user_ids = self.order.get_user_ids()
        if exclude:
            user_ids = [x for x in user_ids if x not in exclude]
        for user_id in user_ids:
            async_to_sync(self.channel_layer.group_send)(f"user_{user_id}", {
                "type": "add_or_update_order",
                "order_id": self.order.pk,
            })

    def cancelled(self, offer):
        """
        Отменить заказ
        Если заказ уже завершен - нельзя отменить

        :return:
        """
        if self.order.status == OrderStatus.completed:
            raise ValidationError('order_is_completed')

        if self.order.status == OrderStatus.being_executed:
            Notification.objects.create(
                user=self.order.transporter_manager.user,
                title=f"Заказ отменен",
                description=f"Транспортировка №{self.order.transportation_number} была отменена заказчиком",
                type=NotificationType.ORDER_CANCELLED
            )
            if (self.order.application_type.status != OrderStatus.in_direct):
                company = self.order.transporter_manager.company
                company.balance += offer.price * company.subscription.win_percentage_fee / 100
                company.save()

        for user_id in self.order.get_user_ids():
            self.remove_order(user_id=user_id, order_status=self.order.status)
        self.order.status = OrderStatus.cancelled
        self.order.save()
        self.add_or_update_order()

    def unpublished(self):
        """
        Снять заказ с публикации (вернуть в заказы)
        Если заказ уже в "заказах" или закончен - нельзя снять с публикации

        ВНИМАНИЕ: удаляет все предложения перевозчиков

        :return:
        """
        if self.order.status in [OrderStatus.completed, OrderStatus.unpublished]:
            raise ValidationError('order_is_completed_or_unpublished')

        for user_id in self.order.get_user_ids():
            self.remove_order(user_id=user_id, order_status=self.order.status)

        self.order.transporter_manager = None
        self.order.driver = None
        self.order.status = OrderStatus.unpublished
        self.order.offers.all().delete()
        self.order.save()
        self.add_or_update_order()

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

        for user_id in self.order.get_user_ids():
            self.remove_order(user_id=user_id, order_status=self.order.status)

        self.order.status = order_type
        self.order.save()
        self.add_or_update_order()

        if order_type == OrderStatus.in_direct:
            offer = self.order.offers.first()
            Notification.objects.create(
                user=offer.transporter_manager.user,
                title=f"Вам назначен заказ",
                description=(
                    f"Вам назначена транспортировка №{self.order.transportation_number} "
                    f"заказчиком {self.order.customer_manager.company.company_name}. "
                    "Вы можете принять или отклонить предложение"
                ),
                type=NotificationType.NEW_ORDER_IN_DIRECT
            )
        else:
            companies = self.order.customer_manager.company.allowed_transporter_companies.all()
            for company in companies:
                for manager in company.managers.all():
                    Notification.objects.create(
                        user=manager.user,
                        title=f"Новый заказ в {'в аукционе' if order_type == OrderStatus.in_auction else 'в торгах'}",
                        description=(
                            f"Транспортировка №{self.order.transportation_number} добавлена "
                            f"{'в аукцион' if order_type == OrderStatus.in_auction else 'в торги'}"
                        ),
                        type=(
                            NotificationType.NEW_ORDER_IN_AUCTION
                            if order_type == OrderStatus.in_auction
                            else NotificationType.NEW_ORDER_IN_BIDDING
                        )
                    )

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

        for user_id in self.order.get_user_ids():
            self.remove_order(user_id=user_id, order_status=self.order.status)

        self.order.transporter_manager = offer.transporter_manager
        self.order.status = OrderStatus.being_executed
        self.order.save()
        self.add_or_update_order()

    def completed(self):
        """
        Завершить заказ
        Если заказ не выполняется - нельзя завершить
        :return:
        """
        if self.order.status != OrderStatus.being_executed:
            raise ValidationError(f'order_status_is:{self.order.status}')

        self.order.status = OrderStatus.completed
        self.order.save()
        self.add_or_update_order()

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
        self.add_or_update_order()


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
        auto_now_add=True, verbose_name='Время создания')
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name='Время обновления')

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
        null=True, blank=True, verbose_name='ADR')
    transport_body_width = models.FloatField(
        null=True, blank=True, verbose_name='Ширина кузова', validators=[MinValueValidator(0.0)])
    transport_body_length = models.FloatField(
        null=True, blank=True, verbose_name='Длина кузова', validators=[MinValueValidator(0.0)])
    transport_body_height = models.FloatField(
        null=True, blank=True, verbose_name='Высота кузова', validators=[MinValueValidator(0.0)])

    # relationships fields:
    # stages
    # tracking
    # documents
    # offers
    # application_type

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ["-transportation_number"]

    def __str__(self):
        return f'{self.id} Заказ'

    def clean(self):
        if self.check_transportation_number(self.transportation_number, self.customer_manager.company, self.pk):
            raise DjangoValidationError({
                'transportation_number': 'Должен быть уникальным для компании',
            })

    def save(self, *args, **kwargs):
        is_new_order = not self.pk
        self.clean()
        super().save(*args, **kwargs)

        if is_new_order and self.pk:
            self.make.add_or_update_order()

    @property
    def make(self):
        return _OrderMake(self)

    def is_transporter_manager_allowed(self, transporter_manager: TransporterManager):
        return self.customer_manager.company.is_transporter_company_allowed(transporter_manager.company)

    def get_user_ids(self):
        '''
        Возвращает список id всех пользователей, которые имеют доступ к этому заказу
        '''
        user_ids = [self.customer_manager.company.user.pk]
        for m in self.customer_manager.company.managers.all():
            user_ids.append(m.user.pk)
        if self.transporter_manager:
            user_ids.append(self.transporter_manager.company.user.pk)
            user_ids.extend(
                [m.user.pk for m in self.transporter_manager.company.managers.all()])
        return user_ids

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
