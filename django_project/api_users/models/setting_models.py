from django.db import models
from django.core.exceptions import ValidationError
from .profiles import PhoneNumberValidator


class Settings(models.Model):
    email = models.EmailField(max_length=300,
                              verbose_name='Почта поддержки')
    phone_number = models.CharField(
        max_length=100, validators=[PhoneNumberValidator()], verbose_name="Телефон поддержки")
    address = models.CharField(max_length=5000, verbose_name='Адрес')

    def clean(self):
        if Settings.objects.exists() and not self.pk:
            raise ValidationError("Нельзя создать больше одной записи.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super(Settings, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Настройка"
        verbose_name_plural = "Настройки"

    def __str__(self):
        return self.phone_number
