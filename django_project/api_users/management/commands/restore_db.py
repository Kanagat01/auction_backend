import subprocess
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Восстановление базы данных из резервной копии'

    def add_arguments(self, parser):
        parser.add_argument(
            'backup_file',
            type=str,
            help='Путь к файлу резервной копии'
        )

    def handle(self, *args, **options):
        backup_file = options['backup_file']
        db_name = settings.DATABASES['default']['NAME']
        db_user = settings.DATABASES['default']['USER']
        db_password = settings.DATABASES['default']['PASSWORD']
        db_host = settings.DATABASES['default']['HOST']
        db_port = settings.DATABASES['default']['PORT']

        command = f'PGPASSWORD={db_password} psql -U {db_user} -h {db_host} -p {db_port} -d {db_name} -f {backup_file}'

        try:
            subprocess.run(command, shell=True, check=True)
            self.stdout.write(self.style.SUCCESS(
                f'База данных успешно восстановлена из файла: {backup_file}'))
        except subprocess.CalledProcessError as e:
            self.stderr.write(self.style.ERROR(
                f'Ошибка при восстановлении базы данных: {str(e)}'))
