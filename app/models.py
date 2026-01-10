from django.db import models
from django.core.validators import MinValueValidator, RegexValidator


class Aircraft(models.Model):
    """Profil Samolotu"""
    manufacturer = models.CharField(max_length=255, verbose_name="Producent samolotu")
    aircraft_type = models.CharField(max_length=255, verbose_name="Typ samolotu")
    serial_number = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="S/N samolotu"
    )
    registration_marks = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Znaki rejestracyjne"
    )
    photo = models.ImageField(
        upload_to='aircraft_photos/',
        null=True,
        blank=True,
        verbose_name="Zdjęcie samolotu"
    )
    base_flight_hours = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Bazowa liczba godzin nalotu",
        help_text="Wartość początkowa godzin nalotu"
    )
    base_landings = models.PositiveIntegerField(
        default=0,
        verbose_name="Bazowa liczba lądowań",
        help_text="Wartość początkowa liczby lądowań"
    )
    next_service_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data następnej obsługi"
    )
    next_service_hours = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name="Ilość nalotu następnej obsługi"
    )
    arc_valid_until = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data ważności ARC"
    )
    insurance_valid_until = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data ważności OC"
    )
    is_active = models.BooleanField(default=True, verbose_name="Aktywny")

    @staticmethod
    def _decimal_hours_to_timedelta(decimal_hours):
        """Convert decimal hours in GGG.MM format (e.g. 123.30 = 123h 30min) to timedelta.
        The decimal part represents minutes directly, not a fraction of an hour."""
        from datetime import timedelta
        hours_value = float(decimal_hours)
        hours_int = int(hours_value)
        # Decimal part is minutes (e.g. .30 = 30 minutes, .05 = 5 minutes)
        minutes = int(round((hours_value - hours_int) * 100))
        return timedelta(hours=hours_int, minutes=minutes)

    @staticmethod
    def format_hours_as_hhhmm(decimal_hours):
        """Format decimal hours (GGG.MM format) as GGG:MM string."""
        hours_value = float(decimal_hours)
        hours_int = int(hours_value)
        minutes = int(round((hours_value - hours_int) * 100))
        return f'{hours_int}:{minutes:02d}'

    def get_base_flight_hours_formatted(self):
        """Return base_flight_hours formatted as GGG:MM."""
        return self.format_hours_as_hhhmm(self.base_flight_hours)

    def get_next_service_hours_formatted(self):
        """Return next_service_hours formatted as GGG:MM."""
        if self.next_service_hours:
            return self.format_hours_as_hhhmm(self.next_service_hours)
        return None

    def get_total_flight_hours(self):
        """Sum of base hours + all flight_time from related flight operations.
        Returns formatted string as GGG:MM (hours:minutes)."""
        from datetime import timedelta

        # Get sum of all flight durations
        total_duration = FlightOperation.objects.filter(
            pdt_page__aircraft=self
        ).aggregate(total=models.Sum('flight_time'))['total'] or timedelta(0)

        # Convert base_flight_hours (decimal in GGG.MM format) to timedelta
        base_duration = self._decimal_hours_to_timedelta(self.base_flight_hours)

        # Total duration
        total = base_duration + total_duration

        # Format as GGG:MM
        total_seconds = int(total.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60

        return f'{hours}:{minutes:02d}'

    def get_total_landings(self):
        """Sum of base landings + all landings from related flight operations"""
        total = FlightOperation.objects.filter(
            pdt_page__aircraft=self
        ).aggregate(total=models.Sum('number_of_landings'))['total']
        return self.base_landings + (total or 0)

    def get_max_engine_hours(self):
        """Highest engine_hours_after_flight value"""
        max_hours = FlightOperation.objects.filter(
            pdt_page__aircraft=self
        ).aggregate(max_hours=models.Max('engine_hours_after_flight'))['max_hours']
        return max_hours or 0.00

    def get_date_status(self, date_value):
        """Return 'success'/>3mo, 'warning'/3-1mo, 'danger'/<1mo, or None"""
        if not date_value:
            return None
        from datetime import date
        from dateutil.relativedelta import relativedelta
        today = date.today()
        three_months = today + relativedelta(months=3)
        one_month = today + relativedelta(months=1)
        if date_value >= three_months:
            return 'success'
        elif date_value >= one_month:
            return 'warning'
        else:
            return 'danger'

    def __str__(self):
        return f"{self.registration_marks} ({self.manufacturer} {self.aircraft_type})"

    class Meta:
        verbose_name = "Samolot"
        verbose_name_plural = "Samoloty"
        ordering = ['registration_marks']


class Pilot(models.Model):
    """Profil Użytkownika (pilota)"""
    user = models.OneToOneField(
        'auth.User',
        on_delete=models.PROTECT,
        related_name='pilot_profile',
        verbose_name="Użytkownik"
    )
    license_number = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nr. Licencji"
    )
    phone_number = models.CharField(
        max_length=20,
        verbose_name="Nr. Telefonu"
    )
    sepl_valid_until = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data ważności SEPL(A)"
    )
    medical_valid_until = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data ważności badań MED."
    )
    is_active = models.BooleanField(default=True, verbose_name="Aktywny")

    def get_date_status(self, date_value):
        """Return 'success'/>3mo, 'warning'/3-1mo, 'danger'/<1mo, or None"""
        if not date_value:
            return None
        from datetime import date
        from dateutil.relativedelta import relativedelta
        today = date.today()
        three_months = today + relativedelta(months=3)
        one_month = today + relativedelta(months=1)
        if date_value >= three_months:
            return 'success'
        elif date_value >= one_month:
            return 'warning'
        else:
            return 'danger'

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.license_number})"

    class Meta:
        verbose_name = "Pilot"
        verbose_name_plural = "Piloci"
        ordering = ['user__last_name', 'user__first_name']


class PDTPage(models.Model):
    """Plik (strona) PDT"""
    aircraft = models.ForeignKey(
        'Aircraft',
        on_delete=models.PROTECT,
        related_name='pdt_pages',
        verbose_name="Samolot"
    )
    pdt_date = models.DateField(verbose_name="Data PDT")
    page_number = models.CharField(
        max_length=50,
        verbose_name="Nr. Strony PDT"
    )
    photo = models.ImageField(
        upload_to='pdt_photos/',
        null=True,
        blank=True,
        verbose_name="Zdjęcie PDT"
    )
    persons_on_board = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Ilość osób na pokładzie"
    )
    fuel_added = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Paliwo dodane"
    )
    fuel_at_start = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Paliwo do startu"
    )
    oil_added = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Olej dodany"
    )
    oil_at_start = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Olej do startu"
    )
    last_operation_notes = models.TextField(
        blank=True,
        default='',
        verbose_name="Uwagi do ostatniej operacji lotniczej"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data utworzenia")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data aktualizacji")

    def __str__(self):
        return f"PDT {self.page_number} - {self.aircraft.registration_marks} ({self.pdt_date})"

    class Meta:
        verbose_name = "Strona PDT"
        verbose_name_plural = "Strony PDT"
        ordering = ['-pdt_date', '-page_number']
        constraints = [
            models.UniqueConstraint(
                fields=['aircraft', 'page_number'],
                name='unique_aircraft_pdt_page'
            ),
        ]


class FlightOperation(models.Model):
    """Operacja lotnicza"""
    pdt_page = models.ForeignKey(
        'PDTPage',
        on_delete=models.PROTECT,
        related_name='flight_operations',
        verbose_name="Strona PDT"
    )
    pilot = models.ForeignKey(
        'Pilot',
        on_delete=models.PROTECT,
        related_name='flight_operations',
        verbose_name="Pilot"
    )
    departure_time = models.TimeField(verbose_name="Czas startu")
    departure_location = models.CharField(
        max_length=10,
        validators=[
            RegexValidator(
                regex=r'^[A-Z]{4}$',
                message='Kod ICAO miejsca startu musi składać się z 4 wielkich liter'
            )
        ],
        verbose_name="Miejsce startu (ICAO)"
    )
    landing_time = models.TimeField(verbose_name="Czas lądowania")
    landing_location = models.CharField(
        max_length=10,
        validators=[
            RegexValidator(
                regex=r'^[A-Z]{4}$',
                message='Kod ICAO miejsca lądowania musi składać się z 4 wielkich liter'
            )
        ],
        verbose_name="Miejsce lądowania (ICAO)"
    )
    number_of_landings = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Ilość lądowań"
    )
    flight_time = models.DurationField(
        verbose_name="Czas lotu",
        help_text="Obliczany automatycznie jako różnica między czasem lądowania a czasem startu"
    )
    engine_hours_after_flight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Licznik motogodzin po locie"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data utworzenia")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data aktualizacji")

    def get_flight_time_formatted(self):
        """Return flight_time formatted as GGG:MM (hours:minutes)."""
        if not self.flight_time:
            return '0:00'
        total_seconds = int(self.flight_time.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f'{hours}:{minutes:02d}'

    def __str__(self):
        return (
            f"{self.pilot.user.last_name} - "
            f"{self.departure_location} → {self.landing_location} "
            f"({self.pdt_page.pdt_date})"
        )

    def save(self, *args, **kwargs):
        # Zawsze obliczaj czas lotu na podstawie czasów startu i lądowania
        from datetime import datetime, timedelta
        departure = datetime.combine(datetime.today(), self.departure_time)
        landing = datetime.combine(datetime.today(), self.landing_time)

        # Obsługa przypadku gdy lądowanie jest następnego dnia
        if landing < departure:
            landing += timedelta(days=1)

        self.flight_time = landing - departure

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Operacja lotnicza"
        verbose_name_plural = "Operacje lotnicze"
        ordering = ['-pdt_page__pdt_date', 'departure_time']
        constraints = [
            models.CheckConstraint(
                check=models.Q(number_of_landings__gte=1),
                name='min_one_landing'
            ),
        ]