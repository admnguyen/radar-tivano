from django.contrib import admin
from .models import Aircraft, Pilot, PDTPage, FlightOperation


@admin.register(Aircraft)
class AircraftAdmin(admin.ModelAdmin):
    list_display = [
        'registration_marks',
        'manufacturer',
        'aircraft_type',
        'serial_number',
        'next_service_date',
        'is_active'
    ]
    list_filter = ['is_active', 'manufacturer', 'aircraft_type']
    search_fields = [
        'registration_marks',
        'serial_number',
        'manufacturer',
        'aircraft_type'
    ]
    readonly_fields = ['created_at', 'updated_at'] if hasattr(Aircraft, 'created_at') else []

    fieldsets = (
        ('Podstawowe informacje', {
            'fields': (
                'manufacturer',
                'aircraft_type',
                'serial_number',
                'registration_marks',
                'is_active',
            )
        }),
        ('Obsługa techniczna', {
            'fields': (
                'next_service_date',
                'next_service_hours',
                'arc_valid_until',
                'insurance_valid_until',
            )
        }),
    )


@admin.register(Pilot)
class PilotAdmin(admin.ModelAdmin):
    list_display = [
        'get_full_name',
        'license_number',
        'phone_number',
        'sepl_valid_until',
        'medical_valid_until',
        'is_active'
    ]
    list_filter = ['is_active', 'sepl_valid_until', 'medical_valid_until']
    search_fields = [
        'license_number',
        'user__first_name',
        'user__last_name',
        'phone_number'
    ]
    autocomplete_fields = ['user']

    fieldsets = (
        ('Użytkownik', {
            'fields': ('user',)
        }),
        ('Dane pilota', {
            'fields': (
                'license_number',
                'phone_number',
                'is_active',
            )
        }),
        ('Uprawnienia i ważności', {
            'fields': (
                'sepl_valid_until',
                'medical_valid_until',
            )
        }),
    )

    def get_full_name(self, obj):
        return f"{obj.user.last_name} {obj.user.first_name}"

    get_full_name.short_description = 'Pilot'
    get_full_name.admin_order_field = 'user__last_name'


class FlightOperationInline(admin.TabularInline):
    model = FlightOperation
    extra = 1
    fields = [
        'pilot',
        'departure_time',
        'departure_location',
        'landing_time',
        'landing_location',
        'number_of_landings',
        'flight_time',
        'engine_hours_after_flight',
    ]
    readonly_fields = ['flight_time']
    autocomplete_fields = ['pilot']


@admin.register(PDTPage)
class PDTPageAdmin(admin.ModelAdmin):
    list_display = [
        'page_number',
        'pdt_date',
        'get_aircraft_display',
        'persons_on_board',
        'fuel_at_start',
        'oil_at_start',
        'get_operations_count',
        'created_at',
    ]
    list_filter = ['pdt_date', 'aircraft']
    search_fields = [
        'page_number',
        'aircraft__registration_marks',
        'aircraft__manufacturer',
    ]
    date_hierarchy = 'pdt_date'
    autocomplete_fields = ['aircraft']
    inlines = [FlightOperationInline]

    fieldsets = (
        ('Podstawowe informacje', {
            'fields': (
                'aircraft',
                'pdt_date',
                'page_number',
                'persons_on_board',
            )
        }),
        ('Paliwo', {
            'fields': (
                'fuel_added',
                'fuel_at_start',
            )
        }),
        ('Olej', {
            'fields': (
                'oil_added',
                'oil_at_start',
            )
        }),
        ('Uwagi', {
            'fields': ('last_operation_notes',),
            'classes': ('collapse',),
        }),
        ('Metadane', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

    def get_aircraft_display(self, obj):
        return f"{obj.aircraft.registration_marks} ({obj.aircraft.manufacturer} {obj.aircraft.aircraft_type})"

    get_aircraft_display.short_description = 'Samolot'
    get_aircraft_display.admin_order_field = 'aircraft__registration_marks'

    def get_operations_count(self, obj):
        return obj.flight_operations.count()

    get_operations_count.short_description = 'Operacje'


@admin.register(FlightOperation)
class FlightOperationAdmin(admin.ModelAdmin):
    list_display = [
        'get_pdt_info',
        'get_pilot_name',
        'departure_time',
        'departure_location',
        'landing_time',
        'landing_location',
        'flight_time',
        'number_of_landings',
        'engine_hours_after_flight',
    ]
    list_filter = [
        'pdt_page__pdt_date',
        'pilot',
        'departure_location',
        'landing_location',
    ]
    search_fields = [
        'pdt_page__page_number',
        'pilot__user__last_name',
        'pilot__user__first_name',
        'departure_location',
        'landing_location',
    ]
    date_hierarchy = 'pdt_page__pdt_date'
    autocomplete_fields = ['pdt_page', 'pilot']

    fieldsets = (
        ('PDT i Pilot', {
            'fields': (
                'pdt_page',
                'pilot',
            )
        }),
        ('Start', {
            'fields': (
                'departure_time',
                'departure_location',
            )
        }),
        ('Lądowanie', {
            'fields': (
                'landing_time',
                'landing_location',
                'number_of_landings',
            )
        }),
        ('Podsumowanie', {
            'fields': (
                'flight_time',
                'engine_hours_after_flight',
            )
        }),
        ('Metadane', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = ['flight_time', 'created_at', 'updated_at']

    def get_pdt_info(self, obj):
        return f"PDT {obj.pdt_page.page_number} ({obj.pdt_page.pdt_date})"

    get_pdt_info.short_description = 'Strona PDT'
    get_pdt_info.admin_order_field = 'pdt_page__page_number'

    def get_pilot_name(self, obj):
        return f"{obj.pilot.user.last_name} {obj.pilot.user.first_name}"

    get_pilot_name.short_description = 'Pilot'
    get_pilot_name.admin_order_field = 'pilot__user__last_name'