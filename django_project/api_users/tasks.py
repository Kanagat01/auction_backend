from datetime import timedelta
from django.utils import timezone
from django_q.tasks import schedule, Schedule
from api_notification.models import Notification, NotificationType
from api_users.models import UserModel, TransporterCompany, CustomerCompany


def monthly_deduct_subscription_fee():
    t_companies = TransporterCompany.objects.filter(subscription__isnull=False)
    c_companies = CustomerCompany.objects.filter(subscription__isnull=False)

    for company in [*t_companies, *c_companies]:
        subscription_price = company.subscription.price
        today = timezone.now()

        if company.balance < subscription_price:
            company.subscription_paid = False
            company.user.save()

            next_run = today + \
                timedelta(days=company.subscription.days_without_payment)
            Notification.objects.create(
                user=company.user,
                title="Недостаточно средств",
                description=(
                    "На вашем балансе недостаточно средств для оплаты тарифа за этот месяц. "
                    f"Пожалуйста, пополните баланс до {next_run.strftime('%d.%m.%Y')}, "
                    "иначе функционал будет ограничен только просмотром информации и переходом по разделам."
                ),
                type=NotificationType.POPUP_NOTIFICATION
            )
            schedule(
                'api_users.tasks.check_payment_status',
                user_id=company.user.id,
                schedule_type=Schedule.ONCE,
                next_run=next_run
            )
        else:
            company.balance -= subscription_price
            company.save()


def check_payment_status(user_id):
    user = UserModel.objects.get(id=user_id)
    if hasattr(user, 'customer_company'):
        company = user.customer_company
    elif hasattr(user, 'transporter_company'):
        company = user.transporter_company
    else:
        return

    if not company.subscription_paid:
        Notification.objects.create(
            user=company.user,
            title="Функционал заблокирован",
            description=(
                "На вашем балансе недостаточно средств для оплаты тарифа за этот месяц. "
                "Ваш функционал будет ограничен просмотром информации и переходом по разделам сайта. "
                "Для снятия ограничения пополните баланс и оплатите тариф"
            ),
            type=NotificationType.POPUP_NOTIFICATION
        )
