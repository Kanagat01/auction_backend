from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from api_auction.models import get_unix_time
from api_users.models import CustomerCompany


class OrderStageCouple(models.Model):
    order = models.ForeignKey(
        'OrderModel', on_delete=models.CASCADE, verbose_name='Заказ', related_name='stages')
    created_at = models.DateTimeField(
        default=timezone.now, verbose_name='Время создания')
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name='Время обновления')
    order_stage_number = models.IntegerField(
        default=get_unix_time, verbose_name='Номер поставки')
    cargo = models.CharField(
        max_length=300, verbose_name='Груз')  # Maybe Foreign Key!
    weight = models.FloatField(verbose_name='Вес', validators=[
                               MinValueValidator(0.0)])
    volume = models.FloatField(verbose_name='Объем',  validators=[
                               MinValueValidator(0.0)])

    # relation fields
    # load_stage = models.OneToOneField('OrderLoadStage', on_delete=models.CASCADE, verbose_name='Этап загрузки')
    # unload_stage = models.OneToOneField('OrderUnloadStage', on_delete=models.CASCADE, verbose_name='Этап выгрузки')

    def save(self, *args, **kwargs):
        try:
            load_stage = self.load_stage
            unload_stage = self.unload_stage
        except self.RelatedObjectDoesNotExist:
            raise ValueError("Load stage and unload stage must be set")
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Поставки заказа'
        verbose_name_plural = 'Поставки заказов'

    def __str__(self):
        return f'{self.id} Поставка заказа - [{self.order}]'

    @staticmethod
    def check_stage_number(number: int, company: CustomerCompany, pk: int = None):
        if not number or type(number) != int:
            raise ValueError('Number must be int')
        if not company:
            raise ValueError('Company must be set')
        query = OrderStageCouple.objects.filter(
            order_stage_number=number, order__customer_manager__company=company)
        if pk:
            query = query.exclude(pk=pk)
        return query.exists()


class OrderStages(models.Model):
    """
    Абстрактная модель для поставки (Этапы заказа)
    """

    date = models.DateField(verbose_name='Дата')
    time_start = models.TimeField(verbose_name='Время начала')
    time_end = models.TimeField(verbose_name='Время окончания')

    company = models.CharField(
        max_length=300, verbose_name='Компания')  # Maybe Foreign Key!
    postal_code = models.CharField(
        max_length=20, verbose_name='Почтовый индекс')
    city = models.CharField(max_length=100, verbose_name='Город')
    address = models.CharField(max_length=5000, verbose_name='Адрес')
    contact_person = models.CharField(
        max_length=300, verbose_name='Контактное лицо')  # Maybe Foreign Key!

    comments = models.TextField(null=True, blank=True,
                                max_length=20_000, verbose_name='Комментарии к поставке')
    completed = models.BooleanField(default=False, verbose_name="Завершено")

    class Meta:
        verbose_name = 'Этап заказа'
        verbose_name_plural = 'Этапы заказа'
        abstract = True


class OrderLoadStage(OrderStages):
    """
    Модель для загрузки поставки (Этапы заказа)
    """

    order_couple = models.OneToOneField(OrderStageCouple, on_delete=models.CASCADE, verbose_name='Поставка',
                                        related_name='load_stage')

    class Meta:
        verbose_name = 'Этап загрузки поставки'
        verbose_name_plural = 'Этапы загрузки поставки'

    def __str__(self):
        return f'{self.id} Этап заказа загрузки - [{self.order_couple}]'


class OrderUnloadStage(OrderStages):
    """
    Модель для разгрузки поставки (Этапы заказа)
    """
    order_couple = models.OneToOneField(OrderStageCouple, on_delete=models.CASCADE, verbose_name='Поставка',
                                        related_name='unload_stage')

    class Meta:
        verbose_name = 'Этап выгрузки поставки'
        verbose_name_plural = 'Этапы выгрузки поставки'

    def __str__(self):
        return f'{self.id} Этап разгрузки поставки - [{self.order_couple}]'
