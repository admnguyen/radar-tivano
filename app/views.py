import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db import models
from django.http import FileResponse, Http404
from .models import PDTPage, FlightOperation, Aircraft, Pilot, AircraftReservation
from .forms import PDTPageForm, FlightOperationFormSet, AircraftForm, PilotForm, UserForm, AircraftReservationForm


def _pilot_profile(user):
    """Zwraca profil pilota dla niezalogowanych jako staff użytkowników, inaczej None."""
    if user.is_authenticated and not user.is_staff:
        return getattr(user, 'pilot_profile', None)
    return None


def _staff_only(request):
    """Dla non-staff zwraca redirect do własnego profilu lub home. Dla staff zwraca None."""
    if request.user.is_staff:
        return None
    pilot = _pilot_profile(request.user)
    if pilot:
        return redirect('pilot_detail', pk=pilot.pk)
    return redirect('home')


def home(request):
    """Strona główna: landing dla niezalogowanych, dashboard dla admina, profil dla pilota"""
    if not request.user.is_authenticated:
        return render(request, 'landing.html')

    if not request.user.is_staff:
        pilot = getattr(request.user, 'pilot_profile', None)
        if pilot:
            return redirect('pilot_detail', pk=pilot.pk)
        # Zalogowany non-staff bez profilu pilota — pokaż landing zamiast tworzyć pętlę
        return render(request, 'landing.html')

    # Statystyki
    stats = {
        'total_pdt': PDTPage.objects.count(),
        'total_aircraft': Aircraft.objects.filter(is_active=True).count(),
        'total_pilots': Pilot.objects.filter(is_active=True).count(),
        'total_operations': FlightOperation.objects.count(),
    }

    # Ostatnie strony PDT
    recent_pdt = PDTPage.objects.select_related('aircraft').order_by('-created_at')[:5]

    # Aktywne samoloty
    active_aircraft = Aircraft.objects.filter(is_active=True).order_by('registration_marks')[:5]

    context = {
        'stats': stats,
        'recent_pdt': recent_pdt,
        'active_aircraft': active_aircraft,
    }

    return render(request, 'home.html', context)


@login_required
def create_pdt_page(request):
    pilot = _pilot_profile(request.user)

    if request.method == 'POST':
        form = PDTPageForm(request.POST, request.FILES)
        formset = FlightOperationFormSet(request.POST, prefix='flight_operations')

        # Pilot może przypisać tylko siebie do operacji lotniczej
        if pilot:
            for flight_form in formset.forms:
                flight_form.fields['pilot'].queryset = Pilot.objects.filter(pk=pilot.pk)

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    pdt_page = form.save()

                    instances = formset.save(commit=False)
                    for instance in instances:
                        instance.pdt_page = pdt_page
                        instance.save()

                    for obj in formset.deleted_objects:
                        obj.delete()

                    messages.success(request, f'PDT {pdt_page.page_number} utworzona!')
                    return redirect('pdt_detail', pk=pdt_page.pk)

            except Exception as e:
                messages.error(request, f'Błąd: {str(e)}')
        else:
            if not form.is_valid():
                messages.error(request, 'Błąd w formularzu PDT.')
            if not formset.is_valid():
                messages.error(request, f'Błąd w operacjach: {formset.errors}')
    else:
        # Auto-fill today's date
        from datetime import date
        initial_data = {'pdt_date': date.today()}
        form = PDTPageForm(initial=initial_data)
        formset = FlightOperationFormSet(
            queryset=FlightOperation.objects.none(),
            prefix='flight_operations'
        )

        # Pilot może przypisać tylko siebie do operacji lotniczej
        if pilot:
            for flight_form in formset.forms:
                flight_form.fields['pilot'].queryset = Pilot.objects.filter(pk=pilot.pk)
                flight_form.fields['pilot'].initial = pilot

    return render(request, 'pdt/create_pdt_page.html', {
        'form': form,
        'formset': formset,
        'title': 'Nowa strona PDT',
    })


@login_required
def edit_pdt_page(request, pk):
    """Edycja istniejącej strony PDT - TYLKO DLA ADMINA"""

    # Permission check: only staff/admin can edit PDT
    if not (request.user.is_authenticated and request.user.is_staff):
        messages.error(request, 'Nie masz uprawnień do edycji PDT.')
        return redirect('pdt_detail', pk=pk)

    pdt_page = get_object_or_404(PDTPage, pk=pk)

    if request.method == 'POST':
        form = PDTPageForm(request.POST, request.FILES, instance=pdt_page)
        formset = FlightOperationFormSet(request.POST, instance=pdt_page)
        print(form.is_valid())
        print(form.errors)
        print(formset.is_valid())
        print(formset.errors)
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                    formset.save()

                    messages.success(request, f'Strona PDT {pdt_page.page_number} została zaktualizowana!')
                    return redirect('pdt_detail', pk=pdt_page.pk)

            except Exception as e:
                messages.error(request, f'Błąd podczas zapisywania: {str(e)}')
        else:
            messages.error(request, 'Błąd w formularzu. Sprawdź wprowadzone dane.')
    else:
        form = PDTPageForm(instance=pdt_page)
        formset = FlightOperationFormSet(instance=pdt_page)

    context = {
        'form': form,
        'formset': formset,
        'pdt_page': pdt_page,
        'title': f'Edycja PDT {pdt_page.page_number}',
    }

    return render(request, 'pdt/create_pdt_page.html', context)


@login_required
def pdt_detail(request, pk):
    """Szczegóły strony PDT"""

    pdt_page = get_object_or_404(PDTPage.objects.select_related('aircraft'), pk=pk)

    # Pilot może zobaczyć tylko PDT, w którym uczestniczył
    pilot = _pilot_profile(request.user)
    if pilot and not pdt_page.flight_operations.filter(pilot=pilot).exists():
        messages.error(request, 'Nie masz dostępu do tej strony PDT.')
        return redirect('pdt_list')
    flight_operations = pdt_page.flight_operations.select_related('pilot__user').all()

    context = {
        'pdt_page': pdt_page,
        'flight_operations': flight_operations,
    }

    return render(request, 'pdt/pdt_detail.html', context)


@login_required
def pdt_list(request):
    """Lista stron PDT — pilot widzi tylko swoje, admin wszystkie"""

    pilot = _pilot_profile(request.user)

    if pilot:
        # Pilot widzi tylko PDT, w których uczestniczył
        pdt_pages = PDTPage.objects.filter(
            flight_operations__pilot=pilot
        ).distinct().select_related('aircraft').prefetch_related('flight_operations__pilot__user').order_by('-pdt_date', '-page_number')
        aircraft_list = None
        aircraft_id = None
    else:
        pdt_pages = PDTPage.objects.select_related('aircraft').prefetch_related('flight_operations__pilot__user').order_by('-pdt_date', '-page_number')
        aircraft_id = request.GET.get('aircraft')
        if aircraft_id:
            pdt_pages = pdt_pages.filter(aircraft_id=aircraft_id)
        aircraft_list = Aircraft.objects.filter(is_active=True).order_by('registration_marks')

    # Filtrowanie po zakresie dat (dostępne dla wszystkich)
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        pdt_pages = pdt_pages.filter(pdt_date__gte=date_from)
    if date_to:
        pdt_pages = pdt_pages.filter(pdt_date__lte=date_to)

    context = {
        'pdt_pages': pdt_pages,
        'aircraft_list': aircraft_list,
        'selected_aircraft': aircraft_id if not pilot else None,
        'date_from': date_from or '',
        'date_to': date_to or '',
    }

    return render(request, 'pdt/pdt_list.html', context)


@login_required
def aircraft_list(request):
    """Lista wszystkich samolotów — tylko dla admina"""
    redir = _staff_only(request)
    if redir:
        return redir

    aircraft_qs = Aircraft.objects.filter(is_active=True).order_by('registration_marks')

    # Prepare aircraft data with statistics and date statuses
    aircraft_data = []
    for craft in aircraft_qs:
        aircraft_data.append({
            'aircraft': craft,
            'total_flight_hours': craft.get_total_flight_hours(),
            'total_landings': craft.get_total_landings(),
            'max_engine_hours': craft.get_max_engine_hours(),
            'next_service_status': craft.get_date_status(craft.next_service_date),
            'arc_status': craft.get_date_status(craft.arc_valid_until),
            'insurance_status': craft.get_date_status(craft.insurance_valid_until),
        })

    context = {
        'aircraft_data': aircraft_data,
    }

    return render(request, 'aircraft/aircraft_list.html', context)


@login_required
def create_aircraft(request):
    """Tworzenie nowego samolotu — tylko dla admina"""
    redir = _staff_only(request)
    if redir:
        return redir

    if request.method == 'POST':
        form = AircraftForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                aircraft = form.save()
                messages.success(request, f'Samolot {aircraft.registration_marks} został dodany pomyślnie!')
                return redirect('aircraft_list')
            except Exception as e:
                messages.error(request, f'Błąd podczas zapisywania: {str(e)}')
        else:
            messages.error(request, 'Błąd w formularzu. Sprawdź wprowadzone dane.')
    else:
        form = AircraftForm()

    context = {
        'form': form,
        'title': 'Nowy samolot',
    }

    return render(request, 'aircraft/create_aircraft.html', context)


@login_required
def edit_aircraft(request, pk):
    """Edycja istniejącego samolotu — tylko dla admina"""
    if not (request.user.is_authenticated and request.user.is_staff):
        messages.error(request, 'Nie masz uprawnień do edycji samolotu.')
        return redirect('aircraft_detail', pk=pk)

    aircraft = get_object_or_404(Aircraft, pk=pk)

    if request.method == 'POST':
        form = AircraftForm(request.POST, request.FILES, instance=aircraft)

        if form.is_valid():
            try:
                aircraft = form.save()
                messages.success(request, f'Samolot {aircraft.registration_marks} został zaktualizowany!')
                return redirect('aircraft_list')
            except Exception as e:
                messages.error(request, f'Błąd podczas zapisywania: {str(e)}')
        else:
            messages.error(request, 'Błąd w formularzu. Sprawdź wprowadzone dane.')
    else:
        form = AircraftForm(instance=aircraft)

    context = {
        'form': form,
        'aircraft': aircraft,
        'title': f'Edycja {aircraft.registration_marks}',
    }

    return render(request, 'aircraft/create_aircraft.html', context)


@login_required
def aircraft_detail(request, pk):
    """Szczegóły samolotu — tylko dla admina"""
    redir = _staff_only(request)
    if redir:
        return redir

    aircraft = get_object_or_404(Aircraft, pk=pk)

    # Get flight operations with optimized query
    flight_operations = FlightOperation.objects.filter(
        pdt_page__aircraft=aircraft
    ).select_related(
        'pilot__user',
        'pdt_page'
    ).order_by('-pdt_page__pdt_date', 'departure_time')[:20]

    # Calculate statistics using model methods
    total_flight_hours = aircraft.get_total_flight_hours()
    total_landings = aircraft.get_total_landings()
    max_engine_hours = aircraft.get_max_engine_hours()

    # Calculate date statuses for color coding
    next_service_status = aircraft.get_date_status(aircraft.next_service_date)
    arc_status = aircraft.get_date_status(aircraft.arc_valid_until)
    insurance_status = aircraft.get_date_status(aircraft.insurance_valid_until)

    # Check if user can edit
    can_edit = request.user.is_staff if request.user.is_authenticated else False

    context = {
        'aircraft': aircraft,
        'flight_operations': flight_operations,
        'total_flight_hours': total_flight_hours,
        'total_landings': total_landings,
        'max_engine_hours': max_engine_hours,
        'next_service_status': next_service_status,
        'arc_status': arc_status,
        'insurance_status': insurance_status,
        'can_edit': can_edit,
    }

    return render(request, 'aircraft/aircraft_detail.html', context)


@login_required
def pilot_list(request):
    """Lista wszystkich pilotów — tylko dla admina"""
    redir = _staff_only(request)
    if redir:
        return redir

    pilots_qs = Pilot.objects.filter(is_active=True).select_related('user').order_by('user__last_name')

    # Prepare pilot data with date statuses
    pilots_data = []
    for pilot in pilots_qs:
        pilots_data.append({
            'pilot': pilot,
            'sepl_status': pilot.get_date_status(pilot.sepl_valid_until),
            'medical_status': pilot.get_date_status(pilot.medical_valid_until),
        })

    context = {
        'pilots_data': pilots_data,
    }

    return render(request, 'pilot/pilot_list.html', context)


@login_required
def create_pilot(request):
    """Tworzenie nowego pilota — tylko dla admina"""
    redir = _staff_only(request)
    if redir:
        return redir

    if request.method == 'POST':
        user_form = UserForm(request.POST)
        pilot_form = PilotForm(request.POST)

        if user_form.is_valid() and pilot_form.is_valid():
            try:
                with transaction.atomic():
                    # Utwórz użytkownika
                    user = user_form.save(commit=False)
                    # Ustaw losowe hasło (powinno być zmienione przez użytkownika)
                    user.set_password('changeme123')
                    user.save()

                    # Utwórz pilota
                    pilot = pilot_form.save(commit=False)
                    pilot.user = user
                    pilot.save()

                    # Przypisz użytkownika do grupy Pilot
                    from django.contrib.auth.models import Group
                    pilot_group = Group.objects.get(name='Pilot')
                    user.groups.add(pilot_group)

                    messages.success(
                        request,
                        f'Pilot {user.get_full_name()} został dodany pomyślnie! '
                        f'Hasło tymczasowe: changeme123'
                    )
                    return redirect('pilot_list')
            except Exception as e:
                messages.error(request, f'Błąd podczas zapisywania: {str(e)}')
        else:
            messages.error(request, 'Błąd w formularzu. Sprawdź wprowadzone dane.')
    else:
        user_form = UserForm()
        pilot_form = PilotForm()

    context = {
        'user_form': user_form,
        'pilot_form': pilot_form,
        'title': 'Nowy pilot',
    }

    return render(request, 'pilot/create_pilot.html', context)


@login_required
def edit_pilot(request, pk):
    """Edycja istniejącego pilota - TYLKO DLA ADMINA"""

    # Permission check: only staff/admin can edit pilot
    if not (request.user.is_authenticated and request.user.is_staff):
        messages.error(request, 'Nie masz uprawnień do edycji profilu pilota.')
        return redirect('pilot_detail', pk=pk)

    pilot = get_object_or_404(Pilot.objects.select_related('user'), pk=pk)

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=pilot.user)
        pilot_form = PilotForm(request.POST, instance=pilot)

        if user_form.is_valid() and pilot_form.is_valid():
            try:
                with transaction.atomic():
                    user_form.save()
                    pilot_form.save()

                    messages.success(request, f'Pilot {pilot.user.get_full_name()} został zaktualizowany!')
                    return redirect('pilot_list')
            except Exception as e:
                messages.error(request, f'Błąd podczas zapisywania: {str(e)}')
        else:
            messages.error(request, 'Błąd w formularzu. Sprawdź wprowadzone dane.')
    else:
        user_form = UserForm(instance=pilot.user)
        pilot_form = PilotForm(instance=pilot)

    context = {
        'user_form': user_form,
        'pilot_form': pilot_form,
        'pilot': pilot,
        'title': f'Edycja {pilot.user.get_full_name()}',
    }

    return render(request, 'pilot/create_pilot.html', context)


@login_required
def pilot_detail(request, pk):
    """Szczegóły pilota — pilot widzi tylko własny profil"""
    requesting_pilot = _pilot_profile(request.user)
    if requesting_pilot and requesting_pilot.pk != pk:
        return redirect('pilot_detail', pk=requesting_pilot.pk)

    pilot = get_object_or_404(Pilot.objects.select_related('user'), pk=pk)
    flight_operations = pilot.flight_operations.select_related('pdt_page__aircraft').order_by('-pdt_page__pdt_date')[:20]

    # Statystyki
    total_flights = pilot.flight_operations.count()
    total_landings = pilot.flight_operations.aggregate(
        total=models.Sum('number_of_landings')
    )['total'] or 0

    # Check if current user can edit (admin or staff)
    can_edit = request.user.is_staff if request.user.is_authenticated else False

    # Check if viewing own profile
    is_own_profile = request.user.is_authenticated and hasattr(request.user, 'pilot_profile') and request.user.pilot_profile == pilot

    # Calculate date statuses for color coding
    sepl_status = pilot.get_date_status(pilot.sepl_valid_until)
    medical_status = pilot.get_date_status(pilot.medical_valid_until)

    context = {
        'pilot': pilot,
        'flight_operations': flight_operations,
        'total_flights': total_flights,
        'total_landings': total_landings,
        'can_edit': can_edit,
        'is_own_profile': is_own_profile,
        'sepl_status': sepl_status,
        'medical_status': medical_status,
    }

    return render(request, 'pilot/pilot_detail.html', context)


@login_required
def change_password(request, pk):
    """Zmiana hasła - dla zalogowanego pilota lub admina"""

    pilot = get_object_or_404(Pilot.objects.select_related('user'), pk=pk)

    # Check permissions: user must be the pilot themselves OR admin
    if not request.user.is_authenticated:
        messages.error(request, 'Musisz być zalogowany, aby zmienić hasło.')
        return redirect('pilot_detail', pk=pk)

    is_own_profile = hasattr(request.user, 'pilot_profile') and request.user.pilot_profile == pilot
    is_admin = request.user.is_staff

    if not (is_own_profile or is_admin):
        messages.error(request, 'Nie masz uprawnień do zmiany tego hasła.')
        return redirect('pilot_detail', pk=pk)

    if request.method == 'POST':
        from django.contrib.auth.forms import PasswordChangeForm
        from django.contrib.auth import update_session_auth_hash
        form = PasswordChangeForm(pilot.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Keep user logged in after password change
            if is_own_profile:
                update_session_auth_hash(request, user)
            messages.success(request, 'Hasło zostało zmienione pomyślnie!')
            return redirect('pilot_detail', pk=pk)
        else:
            messages.error(request, 'Błąd podczas zmiany hasła. Sprawdź wprowadzone dane.')
    else:
        from django.contrib.auth.forms import PasswordChangeForm
        form = PasswordChangeForm(pilot.user)

    context = {
        'form': form,
        'pilot': pilot,
        'title': f'Zmiana hasła - {pilot.user.get_full_name()}',
    }

    return render(request, 'pilot/change_password.html', context)


# Authentication Views
def login_view(request):
    """Widok logowania"""
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('home')
        pilot = getattr(request.user, 'pilot_profile', None)
        if pilot:
            return redirect('pilot_detail', pk=pilot.pk)
        return render(request, 'landing.html')

    if request.method == 'POST':
        from django.contrib.auth import authenticate, login
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Witaj, {user.get_full_name() or user.username}!')
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            # Pilot → własny profil, admin → home
            pilot = getattr(user, 'pilot_profile', None)
            if pilot and not user.is_staff:
                return redirect('pilot_detail', pk=pilot.pk)
            return redirect('home')
        else:
            messages.error(request, 'Nieprawidłowa nazwa użytkownika lub hasło.')

    return render(request, 'auth/login.html', {'title': 'Logowanie'})


def logout_view(request):
    """Widok wylogowania"""
    from django.contrib.auth import logout
    logout(request)
    messages.success(request, 'Zostałeś wylogowany.')
    return redirect('login')


@login_required
def schedule_view(request):
    """Harmonogram rezerwacji samolotów — tylko do odczytu"""
    from datetime import date, timedelta, time, datetime
    from django.utils import timezone

    week_str = request.GET.get('week')
    if week_str:
        try:
            anchor = date.fromisoformat(week_str)
        except ValueError:
            anchor = date.today()
    else:
        anchor = date.today()

    week_start = anchor - timedelta(days=anchor.weekday())
    week_end = week_start + timedelta(days=6)
    today = date.today()

    aircraft_qs = list(Aircraft.objects.filter(is_active=True, show_in_schedule=True).order_by('registration_marks'))

    reservations = list(
        AircraftReservation.objects.filter(
            start_datetime__date__lte=week_end,
            end_datetime__date__gte=week_start,
        ).select_related('aircraft', 'pilot__user').order_by('start_datetime')
    )

    TIMELINE_START = 6
    TIMELINE_HOURS = 16

    # Assign stable color per pilot across this week
    pilot_color_map = {}
    color_idx = 0
    for res in reservations:
        if res.pilot_id not in pilot_color_map:
            pilot_color_map[res.pilot_id] = color_idx % 6
            color_idx += 1

    schedule = []
    for i in range(7):
        day = week_start + timedelta(days=i)
        day_rows = []
        for craft in aircraft_qs:
            day_reservations = []
            for res in reservations:
                if res.aircraft_id != craft.id:
                    continue
                res_start_local = timezone.localtime(res.start_datetime)
                res_end_local = timezone.localtime(res.end_datetime)
                if res_start_local.date() > day or res_end_local.date() < day:
                    continue

                day_start_dt = datetime.combine(day, time(TIMELINE_START, 0))
                day_end_dt = datetime.combine(day, time(TIMELINE_START + TIMELINE_HOURS, 0))

                block_start = max(res_start_local.replace(tzinfo=None), day_start_dt)
                block_end = min(res_end_local.replace(tzinfo=None), day_end_dt)

                if block_end <= block_start:
                    continue

                total_min = TIMELINE_HOURS * 60
                start_offset = (block_start - day_start_dt).total_seconds() / 60
                duration = (block_end - block_start).total_seconds() / 60

                day_reservations.append({
                    'reservation': res,
                    'start_str': res_start_local.strftime('%H:%M'),
                    'end_str': res_end_local.strftime('%H:%M'),
                    'left_pct': round((start_offset / total_min) * 100, 2),
                    'width_pct': max(round((duration / total_min) * 100, 2), 2),
                    'color_index': pilot_color_map.get(res.pilot_id, 0),
                })

            day_rows.append({'aircraft': craft, 'reservations': day_reservations})

        schedule.append({
            'day': day,
            'is_today': day == today,
            'rows': day_rows,
        })

    # Reshape for grid template (aircraft-major order)
    aircraft_schedule = []
    for i, craft in enumerate(aircraft_qs):
        craft_days = []
        for day_struct in schedule:
            craft_days.append({
                'date': day_struct['day'],
                'is_today': day_struct['is_today'],
                'reservations': day_struct['rows'][i]['reservations'],
            })
        aircraft_schedule.append({'aircraft': craft, 'days': craft_days})

    context = {
        'schedule': schedule,
        'aircraft_schedule': aircraft_schedule,
        'week_start': week_start,
        'week_end': week_end,
        'prev_week': (week_start - timedelta(days=7)).isoformat(),
        'next_week': (week_start + timedelta(days=7)).isoformat(),
        'today': today,
        'no_aircraft': len(aircraft_qs) == 0,
    }

    return render(request, 'schedule/schedule.html', context)


@login_required
def create_reservation(request):
    """Tworzenie nowej rezerwacji — tylko dla admina"""
    if not request.user.is_staff:
        messages.error(request, 'Nie masz uprawnień do tworzenia rezerwacji.')
        return redirect('schedule')

    if request.method == 'POST':
        form = AircraftReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save()
            messages.success(
                request,
                f'Rezerwacja dla {reservation.pilot.user.get_full_name()} '
                f'({reservation.aircraft.registration_marks}) została dodana.'
            )
            return redirect('schedule')
        else:
            messages.error(request, 'Błąd w formularzu. Sprawdź wprowadzone dane.')
    else:
        from datetime import date
        initial = {}
        week = request.GET.get('week')
        if week:
            try:
                initial['start_datetime'] = date.fromisoformat(week).strftime('%Y-%m-%dT08:00')
                initial['end_datetime'] = date.fromisoformat(week).strftime('%Y-%m-%dT16:00')
            except ValueError:
                pass
        form = AircraftReservationForm(initial=initial)

    return render(request, 'schedule/create_reservation.html', {
        'form': form,
        'title': 'Nowa rezerwacja',
    })


@login_required
def delete_reservation(request, pk):
    """Usuwanie rezerwacji — tylko dla admina"""
    if not request.user.is_staff:
        messages.error(request, 'Nie masz uprawnień do usuwania rezerwacji.')
        return redirect('schedule')

    reservation = get_object_or_404(AircraftReservation, pk=pk)

    if request.method == 'POST':
        pilot_name = reservation.pilot.user.get_full_name()
        reg = reservation.aircraft.registration_marks
        reservation.delete()
        messages.success(request, f'Rezerwacja {reg} — {pilot_name} została usunięta.')
        return redirect('schedule')

    return render(request, 'schedule/confirm_delete_reservation.html', {
        'reservation': reservation,
    })


@login_required
def download_pdt_photo(request, pk):
    """Pobieranie zdjęcia strony PDT"""
    pdt_page = get_object_or_404(PDTPage, pk=pk)
    if not pdt_page.photo:
        raise Http404
    try:
        return FileResponse(pdt_page.photo.open('rb'), as_attachment=True, filename=os.path.basename(pdt_page.photo.name))
    except (FileNotFoundError, OSError):
        raise Http404
