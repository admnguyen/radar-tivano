import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Tworzy superusera z zmiennych środowiskowych (ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD)'

    def handle(self, *args, **kwargs):
        User = get_user_model()

        username = os.environ.get('ADMIN_USERNAME')
        email = os.environ.get('ADMIN_EMAIL')
        password = os.environ.get('ADMIN_PASSWORD')

        if not username or not email or not password:
            self.stdout.write(
                self.style.ERROR('Brak wymaganych zmiennych środowiskowych: ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD')
            )
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'Użytkownik "{username}" już istnieje'))
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f'Pomyślnie utworzono superusera: {username}'))
