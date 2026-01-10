# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Tivano is a Django-based aircraft flight log management system. The application tracks flight operations, aircraft maintenance, pilot certifications, and PDT (Pilot's Daily Timesheet) pages. The system is designed for Polish aviation operations with Polish field names and validation rules.

## Development Commands

### Environment Setup
```bash
# Install dependencies using Poetry
poetry install

# Activate virtual environment
poetry shell

# Or use existing .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Unix/Linux
```

### Database Operations
```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser for admin access
python manage.py createsuperuser
```

### Running the Application
```bash
# Run development server
python manage.py runserver

# Run on specific port
python manage.py runserver 8080
```

### Code Quality
```bash
# Run Ruff linter and formatter (auto-fixes enabled)
ruff check .
ruff format .
```

## Architecture

### Core Models (app/models.py)

The application has four main models with the following relationships:

1. **Aircraft** - Aircraft profiles with maintenance tracking
   - Stores manufacturer, type, registration marks, serial number
   - Tracks next service date/hours, ARC validity, insurance validity
   - One-to-many relationship with PDTPage

2. **Pilot** - Pilot profiles linked to Django User
   - One-to-one relationship with Django's User model (uses PROTECT on delete)
   - Stores license number, phone, SEPL(A) validity, medical validity
   - One-to-many relationship with FlightOperation

3. **PDTPage** - Daily flight log pages
   - Belongs to one Aircraft (PROTECT on delete)
   - Stores date, page number, fuel/oil levels, persons on board
   - Has unique constraint on (aircraft, page_number)
   - One-to-many relationship with FlightOperation

4. **FlightOperation** - Individual flight records
   - Belongs to one PDTPage and one Pilot (both PROTECT on delete)
   - Stores departure/landing times and ICAO codes, flight duration, landings
   - Automatically calculates flight_time in save() method if not provided
   - Validates ICAO codes must be 4 uppercase letters

### URL Structure (app/urls.py)

The application uses a hierarchical URL pattern:
- `/` - PDT list (home page)
- `/create/` - Create new PDT page
- `/<int:pk>/` - PDT detail
- `/<int:pk>/edit/` - Edit PDT page
- `/aircraft/` - Aircraft list
- `/aircraft/create/` - Create aircraft
- `/aircraft/<int:pk>/` - Aircraft detail
- `/aircraft/<int:pk>/edit/` - Edit aircraft
- `/pilots/` - Pilot list
- `/pilots/create/` - Create pilot
- `/pilots/<int:pk>/` - Pilot detail
- `/pilots/<int:pk>/edit/` - Edit pilot

### Forms and Formsets (app/forms.py)

The application uses Django forms and formsets extensively:
- **PDTPageForm** - Main PDT page form with Bootstrap styling
- **FlightOperationForm** - Individual flight operation form
- **FlightOperationFormSet** - Inline formset for managing multiple flight operations within a PDT page (uses inlineformset_factory)
- **AircraftForm** - Aircraft creation/editing
- **PilotForm** + **UserForm** - Two-form approach for pilot creation (creates Django User + Pilot profile)

### Views Pattern (app/views.py)

All views follow a consistent pattern:
- Currently use function-based views (not class-based views)
- Most views have `@login_required` decorator commented out (authentication not yet enforced)
- Use `transaction.atomic()` for complex multi-model operations
- Use Django messages framework for user feedback
- List views use `select_related()` for query optimization

### Templates (templates/)

Templates are organized by resource:
- `aircraft/` - Aircraft-related templates
- `pilot/` - Pilot-related templates
- `pdt/` - PDT page templates

Each resource typically has: list, create/edit (shared), and detail views.

### Configuration

- **Database**: PostgreSQL configured via `project_secrets.py` (not in version control)
- **Settings**: Standard Django settings in `tivano/settings.py`
- **Ruff**: Configured with line length 160, Django-specific linting rules, single quotes
- **Time Zone**: UTC (USE_TZ=True)

## Key Implementation Details

### Flight Time Calculation
FlightOperation.save() automatically calculates flight_time from departure_time and landing_time if not provided. Handles overnight flights (landing next day).

### Foreign Key Protection
All foreign keys use `on_delete=models.PROTECT` to prevent cascading deletions and maintain data integrity.

### Active Status Pattern
Aircraft and Pilot models use `is_active` boolean field for soft deletes. Forms filter to show only active records.

### ICAO Code Validation
Flight operations validate departure/landing locations as 4-character uppercase ICAO codes using RegexValidator.

### Formset Handling
PDT pages use Django's inline formset to manage multiple flight operations. The formset requires minimum 1 operation, allows deletion, and uses prefix='flight_operations'.

### Polish Language
All verbose names, labels, and user-facing text are in Polish. Field names are in English for developer convenience.
