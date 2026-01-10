# Wdrożenie aplikacji Tivano na Railway

Ten dokument opisuje kroki potrzebne do wdrożenia aplikacji Django Tivano na platformie Railway.

## Przygotowanie projektu (✅ Gotowe)

Następujące pliki zostały już utworzone i skonfigurowane:

- ✅ `requirements.txt` - Lista zależności Python
- ✅ `Procfile` - Komendy startowe dla Railway
- ✅ `runtime.txt` - Wersja Python (3.13.1)
- ✅ `nixpacks.toml` - Konfiguracja build dla Railway
- ✅ `railway.json` - Konfiguracja deploymentu
- ✅ `.gitignore` - Pliki do ignorowania w git
- ✅ `.env.example` - Przykład zmiennych środowiskowych
- ✅ `settings.py` - Zaktualizowany do użycia zmiennych środowiskowych i whitenoise

## Kroki wdrożenia na Railway

### 1. Utwórz konto na Railway

1. Przejdź do https://railway.app/
2. Zarejestruj się używając GitHub (zalecane) lub email

### 2. Utwórz nowy projekt

1. Kliknij "New Project"
2. Wybierz "Deploy from GitHub repo"
3. Autoryzuj Railway do dostępu do swoich repozytoriów GitHub
4. Wybierz repozytorium z projektem Tivano

### 3. Dodaj bazę danych PostgreSQL

1. W projekcie Railway kliknij "+ New"
2. Wybierz "Database" → "Add PostgreSQL"
3. Railway automatycznie utworzy bazę danych i ustawi zmienną `DATABASE_URL`

### 4. Skonfiguruj zmienne środowiskowe

W zakładce "Variables" swojego serwisu dodaj następujące zmienne:

```
SECRET_KEY=your-secret-key-here-generate-new-one
DEBUG=False
ALLOWED_HOSTS=yourdomain.railway.app,.railway.app
```

**Generowanie SECRET_KEY:**
```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Ważne:** Zmienna `DATABASE_URL` jest automatycznie dodawana przez Railway po dodaniu PostgreSQL.

### 5. Dodaj domenę (opcjonalnie)

1. W zakładce "Settings" znajdź sekcję "Domains"
2. Railway automatycznie generuje domenę `.railway.app`
3. Możesz dodać własną domenę niestandardową

### 6. Deploy aplikacji

Railway automatycznie wykryje zmiany w repozytorium i rozpocznie deployment:

1. Instalacja zależności z `requirements.txt`
2. Uruchomienie `python manage.py collectstatic --noinput`
3. Uruchomienie migracji `python manage.py migrate`
4. Uruchomienie serwera `gunicorn tivano.wsgi`

### 7. Utwórz superusera (pierwsza konfiguracja)

Po pierwszym deploymencie musisz utworzyć konto administratora:

1. W Railway przejdź do zakładki swojego serwisu
2. Kliknij zakładkę "Settings" → "Service Variables"
3. Otwórz terminal (ikona ">_" w prawym górnym rogu)
4. Uruchom: `python manage.py createsuperuser`
5. Postępuj zgodnie z instrukcjami

**Alternatywnie** możesz użyć Railway CLI:
```bash
railway login
railway link
railway run python manage.py createsuperuser
```

## Aktualizacje aplikacji

Railway automatycznie deployuje zmiany gdy pushesz do brancha głównego:

```bash
git add .
git commit -m "Twoja wiadomość commit"
git push origin main
```

## Monitorowanie

W Railway możesz:
- Sprawdzać logi w zakładce "Deployments"
- Monitorować użycie zasobów w "Metrics"
- Przeglądać zmienne środowiskowe w "Variables"

## Lokalne testowanie z ustawieniami produkcyjnymi

Aby przetestować aplikację lokalnie z ustawieniami produkcyjnymi:

1. Utwórz plik `.env` (skopiuj z `.env.example`):
```bash
cp .env.example .env
```

2. Edytuj `.env` i ustaw:
```
SECRET_KEY=your-local-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=tivano
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

3. Uruchom serwer:
```bash
python manage.py runserver
```

## Troubleshooting

### Błąd "DisallowedHost"
- Dodaj domenę Railway do zmiennej `ALLOWED_HOSTS` w Railway Variables

### Pliki statyczne nie ładują się
- Sprawdź czy `collectstatic` został uruchomiony w logach build
- Upewnij się że whitenoise jest w MIDDLEWARE w settings.py

### Błąd połączenia z bazą danych
- Sprawdź czy PostgreSQL został dodany do projektu
- Sprawdź czy zmienna `DATABASE_URL` jest ustawiona

### Brak migracji
- Railway automatycznie uruchamia migracje przy starcie
- Możesz uruchomić ręcznie przez terminal Railway: `python manage.py migrate`

## Bezpieczeństwo

✅ **Gotowe zabezpieczenia:**
- SECRET_KEY z zmiennej środowiskowej
- DEBUG=False w produkcji
- ALLOWED_HOSTS ograniczone do konkretnych domen
- HTTPS redirect (SECURE_SSL_REDIRECT)
- Secure cookies (SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE)
- HSTS headers
- XSS protection
- WhiteNoise dla bezpiecznej obsługi plików statycznych

## Wsparcie

- Railway Documentation: https://docs.railway.app/
- Django Deployment Checklist: https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/
- WhiteNoise Documentation: http://whitenoise.evans.io/
