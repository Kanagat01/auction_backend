from django.utils import timezone
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django_q.tasks import schedule, Schedule


@receiver(post_migrate)
def schedule_monthly_task(sender, **kwargs):
    if sender.name == 'api_users':
        today = timezone.now()
        if today.day == 1:
            next_run = today
        else:
            year = today.year + 1 if today.month == 12 else today.year
            month = 1 if today.month == 12 else today.month + 1
            next_run = timezone.datetime(
                year=year, month=month, day=1, hour=0, minute=0, tzinfo=timezone.get_current_timezone())
        Schedule.objects.filter(
            func='api_users.tasks.monthly_deduct_subscription_fee').delete()
        schedule(
            'api_users.tasks.monthly_deduct_subscription_fee',
            schedule_type=Schedule.MONTHLY,
            next_run=next_run,
            repeats=-1
        )
