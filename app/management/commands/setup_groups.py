from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from app.models import PDTPage, FlightOperation, Aircraft, Pilot


class Command(BaseCommand):
    help = 'Tworzy grupy użytkowników (Admin i Pilot) z odpowiednimi uprawnieniami'

    def handle(self, *args, **kwargs):
        # Usuń istniejące grupy jeśli istnieją
        Group.objects.filter(name__in=['Admin', 'Pilot']).delete()

        # Grupa Admin - wszystkie uprawnienia
        admin_group, created = Group.objects.get_or_create(name='Admin')
        if created:
            # Admin ma dostęp do wszystkiego
            all_permissions = Permission.objects.all()
            admin_group.permissions.set(all_permissions)
            self.stdout.write(self.style.SUCCESS('Utworzono grupę "Admin" ze wszystkimi uprawnieniami'))
        else:
            self.stdout.write(self.style.WARNING('Grupa "Admin" już istnieje'))

        # Grupa Pilot - ograniczone uprawnienia
        pilot_group, created = Group.objects.get_or_create(name='Pilot')
        if created:
            # Pilot może:
            # - Przeglądać wszystko
            # - Tworzyć PDT
            # - Dodawać operacje lotnicze
            # - Przeglądać samoloty i innych pilotów

            permissions_to_add = []

            # PDT - może dodawać, przeglądać
            pdt_ct = ContentType.objects.get_for_model(PDTPage)
            permissions_to_add.extend(
                Permission.objects.filter(
                    content_type=pdt_ct, codename__in=['add_pdtpage', 'view_pdtpage']
                )
            )

            # FlightOperation - może dodawać, przeglądać
            flight_ct = ContentType.objects.get_for_model(FlightOperation)
            permissions_to_add.extend(
                Permission.objects.filter(
                    content_type=flight_ct, codename__in=['add_flightoperation', 'view_flightoperation']
                )
            )

            # Aircraft - tylko przeglądanie
            aircraft_ct = ContentType.objects.get_for_model(Aircraft)
            permissions_to_add.extend(Permission.objects.filter(content_type=aircraft_ct, codename='view_aircraft'))

            # Pilot - tylko przeglądanie
            pilot_ct = ContentType.objects.get_for_model(Pilot)
            permissions_to_add.extend(Permission.objects.filter(content_type=pilot_ct, codename='view_pilot'))

            pilot_group.permissions.set(permissions_to_add)
            self.stdout.write(self.style.SUCCESS('Utworzono grupę "Pilot" z ograniczonymi uprawnieniami'))
        else:
            self.stdout.write(self.style.WARNING('Grupa "Pilot" już istnieje'))

        self.stdout.write(self.style.SUCCESS('\n=== Podsumowanie ==='))
        self.stdout.write(f'Grupa Admin: {admin_group.permissions.count()} uprawnień')
        self.stdout.write(f'Grupa Pilot: {pilot_group.permissions.count()} uprawnień')
        self.stdout.write(self.style.SUCCESS('\nGrupy zostały pomyślnie skonfigurowane!'))
