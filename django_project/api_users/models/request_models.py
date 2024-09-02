import string
import random
from django.db import models
from .profiles import DriverProfile


class DriverRegisterRequest(models.Model):
    phone_number = models.CharField(unique=True, max_length=17)
    confirmation_code = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now=True)

    def generate_code(self):
        self.confirmation_code = ''.join(random.choices(string.digits, k=4))
        self.save()


class PhoneNumberChangeRequest(models.Model):
    driver = models.OneToOneField(DriverProfile, on_delete=models.CASCADE)
    new_phone_number = models.CharField(max_length=17)
    confirmation_code = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now=True)

    def generate_code(self):
        self.confirmation_code = ''.join(random.choices(string.digits, k=4))
        self.save()
