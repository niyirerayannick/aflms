# ATMS - Afrilott Transport Management System

Production-ready Django 5 project scaffold for transport operations, fuel/maintenance intelligence, and profitability reporting.

## Stack

- Django 5.x
- PostgreSQL
- Redis (cache, Channels, Celery)
- Django Channels
- django-tailwind
- django-allauth
- Celery
- django-storages + Cloudinary
- WhiteNoise
- Gunicorn
- python-decouple

## Quick start

1. Copy .env.example to .env
2. Start services:

docker compose up --build

3. Run migrations and create superuser:

docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser

4. Seed demo data for end-to-end testing:

docker compose exec web python manage.py seed_demo_data --reset

For local virtualenv usage:

.venv\Scripts\python.exe manage.py seed_demo_data --reset

5. Visit:

- App: http://localhost:8000
- Admin: http://localhost:8000/admin/