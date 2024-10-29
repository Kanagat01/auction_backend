import string
import random
from django.db import models
from .profiles import DriverProfile, PhoneNumberValidator


class DriverAuthRequest(models.Model):
    phone_number = models.CharField(unique=True, max_length=17)
    confirmation_code = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now=True)

    def generate_code(self):
        self.confirmation_code = '1234'
        # self.confirmation_code = ''.join(random.choices(string.digits, k=4))
        self.save()


class PhoneNumberChangeRequest(models.Model):
    driver = models.OneToOneField(DriverProfile, on_delete=models.CASCADE)
    new_phone_number = models.CharField(max_length=17)
    confirmation_code = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now=True)

    def generate_code(self):
        self.confirmation_code = '1234'
        # self.confirmation_code = ''.join(random.choices(string.digits, k=4))
        self.save()


class ApplicationForRegistration(models.Model):
    full_name = models.CharField(max_length=200, verbose_name='Имя')
    email = models.EmailField(max_length=300, verbose_name='Email')
    phone_number = models.CharField(
        max_length=17, validators=[PhoneNumberValidator()], verbose_name='Телефон')

    class Meta:
        verbose_name = "Заявка на регистрацию"
        verbose_name_plural = "Заявки на регистрацию"

    def __str__(self):
        return f"Заявка #{self.pk}"
