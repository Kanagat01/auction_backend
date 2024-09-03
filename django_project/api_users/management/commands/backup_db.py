import subprocess
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Создание резервной копии базы данных'

    def handle(self, *args, **options):
        db_name = settings.DATABASES['default']['NAME']
        db_user = settings.DATABASES['default']['USER']
        db_password = settings.DATABASES['default']['PASSWORD']
        db_host = settings.DATABASES['default']['HOST']
        db_port = settings.DATABASES['default']['PORT']

        backup_file = f"{db_name}_backup.sql"
        command = f'PGPASSWORD={db_password} pg_dump -U {db_user} -h {db_host} -p {db_port} {db_name} > {backup_file}'

        try:
            subprocess.run(command, shell=True, check=True)
            self.stdout.write(self.style.SUCCESS(
                f'Резервная копия успешно создана: {backup_file}'))
        except subprocess.CalledProcessError as e:
            self.stderr.write(self.style.ERROR(
                f'Ошибка при создании резервной копии: {str(e)}'))
