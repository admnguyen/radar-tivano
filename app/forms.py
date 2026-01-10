from django import forms
from django.forms import inlineformset_factory
from django.contrib.auth.models import User
from .models import PDTPage, FlightOperation, Aircraft, Pilot


class PDTPageForm(forms.ModelForm):
    """Formularz główny dla strony PDT"""

    class Meta:
        model = PDTPage
        fields = [
            'aircraft',
            'pdt_date',
            'page_number',
            'photo',
            'persons_on_board',
            'fuel_added',
            'fuel_at_start',
            'oil_added',
            'oil_at_start',
            'last_operation_notes',
        ]
        widgets = {
            'aircraft': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }),
            'pdt_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True,
            }),
            'page_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nr. strony PDT',
                'required': True,
            }),
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            }),
            'persons_on_board': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'PAX',
                'min': '1',
                'required': True,
            }),
            'fuel_added': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Dolane',
                'min': '0',
                'step': '0.01',
                'required': True,
            }),
            'fuel_at_start': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Do startu',
                'min': '0',
                'step': '0.01',
                'required': True,
            }),
            'oil_added': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Dolany',
                'min': '0',
                'step': '0.01',
                'required': True,
            }),
            'oil_at_start': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Do startu',
                'min': '0',
                'step': '0.01',
                'required': True,
            }),
            'last_operation_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Uwagi',
            }),
        }
        labels = {
            'aircraft': 'Samolot (Producent | Znaki rejestracyjne)',
            'pdt_date': 'Data wypisania PDT',
            'page_number': 'Nr. strony',
            'photo': 'Zdjęcie',
            'persons_on_board': 'Liczba osób na pokładzie',
            'fuel_added': 'Dolane [Litry]',
            'fuel_at_start': 'Do startu [Litry]',
            'oil_added': 'Dolany [Litry]',
            'oil_at_start': 'Do startu [Litry]',
            'last_operation_notes': 'Uwagi i usterki',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tylko aktywne samoloty
        self.fields['aircraft'].queryset = Aircraft.objects.filter(is_active=True)
        self.fields['aircraft'].label_from_instance = lambda obj: f"{obj.manufacturer} | {obj.registration_marks}"


class FlightOperationForm(forms.ModelForm):
    """Formularz dla pojedynczej operacji lotniczej"""

    class Meta:
        model = FlightOperation
        fields = [
            'pilot',
            'departure_time',
            'departure_location',
            'landing_time',
            'landing_location',
            'number_of_landings',
            'engine_hours_after_flight',
        ]
        widgets = {
            'pilot': forms.Select(attrs={
                'class': 'form-select form-select-sm',
                'required': True,
            }),
            'departure_time': forms.TimeInput(attrs={
                'class': 'form-control form-control-sm',
                'type': 'time',
                'placeholder': 'Czas',
                'required': True,
            }),
            'departure_location': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'ICAO',
                'maxlength': '4',
                'style': 'text-transform: uppercase;',
                'required': True,
            }),
            'landing_time': forms.TimeInput(attrs={
                'class': 'form-control form-control-sm',
                'type': 'time',
                'placeholder': 'Czas',
                'required': True,
            }),
            'landing_location': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'ICAO',
                'maxlength': '4',
                'style': 'text-transform: uppercase;',
                'required': True,
            }),
            'number_of_landings': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Ilość',
                'min': '1',
                'required': True,
            }),
            'engine_hours_after_flight': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Motogodziny',
                'min': '0',
                'step': '0.1',
                'required': True,
            }),
        }
        labels = {
            'pilot': 'Pilot',
            'departure_time': 'Czas',
            'departure_location': 'Lotnisko',
            'landing_time': 'Czas',
            'landing_location': 'Lotnisko',
            'number_of_landings': 'Ilość lądowań',
            'engine_hours_after_flight': 'Licznik motogodzin',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tylko aktywni piloci
        self.fields['pilot'].queryset = Pilot.objects.filter(is_active=True).select_related('user')
        self.fields['pilot'].label_from_instance = lambda obj: f"{obj.user.last_name} {obj.user.first_name}"


# Formset dla operacji lotniczych
FlightOperationFormSet = inlineformset_factory(
    PDTPage,
    FlightOperation,
    form=FlightOperationForm,
    extra=0,  # Domyślnie 1 pusty formularz
    can_delete=True,
    min_num=1,  # Minimum 1 operacja lotnicza
    validate_min=True,
)


class AircraftForm(forms.ModelForm):
    """Formularz dla samolotu"""

    class Meta:
        model = Aircraft
        fields = [
            'manufacturer',
            'aircraft_type',
            'serial_number',
            'registration_marks',
            'photo',
            'base_flight_hours',
            'base_landings',
            'next_service_date',
            'next_service_hours',
            'arc_valid_until',
            'insurance_valid_until',
            'is_active',
        ]
        widgets = {
            'manufacturer': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'np. GOGETAIR',
                'required': True,
            }),
            'aircraft_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'np. G 750',
                'required': True,
            }),
            'serial_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'S/N',
                'required': True,
            }),
            'registration_marks': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'np. S5-MMB',
                'style': 'text-transform: uppercase;',
                'required': True,
            }),
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            }),
            'base_flight_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'np. 123.30 = 123h 30min',
                'min': '0',
                'step': '0.01',
            }),
            'base_landings': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0',
                'min': '0',
            }),
            'next_service_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'next_service_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'np. 500.00 = 500h 00min',
                'min': '0',
                'step': '0.01',
            }),
            'arc_valid_until': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'insurance_valid_until': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
        labels = {
            'manufacturer': 'Producent samolotu',
            'aircraft_type': 'Typ samolotu',
            'serial_number': 'S/N samolotu',
            'registration_marks': 'Znaki rejestracyjne',
            'photo': 'Zdjęcie samolotu',
            'base_flight_hours': 'Bazowa liczba godzin nalotu [GGG.MM]',
            'base_landings': 'Bazowa liczba lądowań',
            'next_service_date': 'Data następnej obsługi',
            'next_service_hours': 'Nalot dla następnej obsługi [GGG.MM]',
            'arc_valid_until': 'Data ważności ARC',
            'insurance_valid_until': 'Data ważności OC',
            'is_active': 'Aktywny',
        }


class UserForm(forms.ModelForm):
    """Formularz dla użytkownika Django (do tworzenia pilota)"""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username', 'is_staff']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Imię',
                'required': True,
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nazwisko',
                'required': True,
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'adres@email.com',
            }),
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nazwa użytkownika',
                'required': True,
            }),
            'is_staff': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
        labels = {
            'first_name': 'Imię',
            'last_name': 'Nazwisko',
            'email': 'Email',
            'username': 'Nazwa użytkownika',
            'is_staff': 'Administrator (dostęp do panelu admina i edycji)',
        }


class PilotForm(forms.ModelForm):
    """Formularz dla pilota"""

    class Meta:
        model = Pilot
        fields = [
            'license_number',
            'phone_number',
            'sepl_valid_until',
            'medical_valid_until',
            'is_active',
        ]
        widgets = {
            'license_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'np. PL.FCL.42752.PPL(A)',
                'required': True,
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+48 608 163 560',
                'required': True,
            }),
            'sepl_valid_until': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'medical_valid_until': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
        labels = {
            'license_number': 'Nr. Licencji',
            'phone_number': 'Nr. Telefonu',
            'sepl_valid_until': 'Data ważności SEPL(A)',
            'medical_valid_until': 'Data ważności badań MED.',
            'is_active': 'Aktywny',
        }
