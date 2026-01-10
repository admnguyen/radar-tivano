from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db import models
from .models import PDTPage, FlightOperation, Aircraft, Pilot
from .forms import PDTPageForm, FlightOperationFormSet, AircraftForm, PilotForm, UserForm


def home(request):
    """Strona główna z dashboardem"""

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
    if request.method == 'POST':
        form = PDTPageForm(request.POST, request.FILES)
        formset = FlightOperationFormSet(request.POST, prefix='flight_operations')

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
    flight_operations = pdt_page.flight_operations.select_related('pilot__user').all()

    context = {
        'pdt_page': pdt_page,
        'flight_operations': flight_operations,
    }

    return render(request, 'pdt/pdt_detail.html', context)


@login_required
def pdt_list(request):
    """Lista wszystkich stron PDT z filtrowaniem"""

    pdt_pages = PDTPage.objects.select_related('aircraft').prefetch_related('flight_operations__pilot__user').order_by('-pdt_date', '-page_number')

    # Filtrowanie po samolocie
    aircraft_id = request.GET.get('aircraft')
    if aircraft_id:
        pdt_pages = pdt_pages.filter(aircraft_id=aircraft_id)

    # Filtrowanie po zakresie dat
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        pdt_pages = pdt_pages.filter(pdt_date__gte=date_from)
    if date_to:
        pdt_pages = pdt_pages.filter(pdt_date__lte=date_to)

    # Lista samolotów do filtra
    aircraft_list = Aircraft.objects.filter(is_active=True).order_by('registration_marks')

    context = {
        'pdt_pages': pdt_pages,
        'aircraft_list': aircraft_list,
        'selected_aircraft': aircraft_id,
        'date_from': date_from or '',
        'date_to': date_to or '',
    }

    return render(request, 'pdt/pdt_list.html', context)


@login_required
def aircraft_list(request):
    """Lista wszystkich samolotów"""

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
    """Tworzenie nowego samolotu"""

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
    """Edycja istniejącego samolotu"""

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
    """Szczegóły samolotu"""

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
    """Lista wszystkich pilotów"""

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
    """Tworzenie nowego pilota"""

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
    """Szczegóły pilota"""

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
        return redirect('home')

    if request.method == 'POST':
        from django.contrib.auth import authenticate, login
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Witaj, {user.get_full_name() or user.username}!')
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            messages.error(request, 'Nieprawidłowa nazwa użytkownika lub hasło.')

    return render(request, 'auth/login.html', {'title': 'Logowanie'})


def logout_view(request):
    """Widok wylogowania"""
    from django.contrib.auth import logout
    logout(request)
    messages.success(request, 'Zostałeś wylogowany.')
    return redirect('login')
