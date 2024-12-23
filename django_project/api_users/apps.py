from django.apps import AppConfig


class ApiUsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api_users'
    verbose_name = 'Пользователи'

    def ready(self) -> None:
        import api_users.signals
