from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django_q.tasks import schedule, Schedule


@receiver(post_migrate)
def schedule_monthly_task(sender, **kwargs):
    if sender.name == 'api_users':
        Schedule.objects.filter(
            func='api_users.tasks.monthly_deduct_subscription_fee').delete()
        schedule(
            'api_users.tasks.monthly_deduct_subscription_fee',
            schedule_type=Schedule.MONTHLY,
            day_of_month=1,
            repeats=-1
        )
