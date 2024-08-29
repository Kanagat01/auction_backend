from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

app = Celery('backend')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'deduct_subscription_fee_monthly': {
        'task': 'api_users.tasks.monthly_deduct_subscription_fee',
        # 'schedule': crontab(day_of_month='1', hour=0, minute=0),
        'schedule': crontab(minute='*'),
    },
}
