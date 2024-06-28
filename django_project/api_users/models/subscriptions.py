class CustomerSubscriptions:
    FREE = 'customer_unpaid'
    PAID = 'customer_paid'

    @classmethod
    def choices(cls):
        return (
            (cls.FREE, 'Заказчик НЕоплаченный'),
            (cls.PAID, 'Заказчик оплаченный'),
        )


class TransporterSubscriptions:
    FREE = 'transporter_unpaid'
    PAID = 'transporter_paid'

    @classmethod
    def choices(cls):
        return (
            (cls.FREE, 'Перевозчик НЕоплаченный'),
            (cls.PAID, 'Перевозчик оплаченный'),
        )
