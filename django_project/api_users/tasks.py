from celery import shared_task
from .models import TransporterCompany, CustomerCompany


@shared_task
def monthly_deduct_subscription_fee():
    t_companies = TransporterCompany.objects.filter(subscription__isnull=False)
    c_companies = CustomerCompany.objects.filter(subscription__isnull=False)

    for company in [*t_companies, *c_companies]:
        subscription_price = company.subscription.price
        print(company, subscription_price)
        if company.balance < subscription_price:
            # TODO: Здесь можно отправить уведомление о нехватке средств
            company.user.is_active = False
            company.user.save()
        else:
            company.balance -= subscription_price
            company.save()
