# AFLMS - Fleet & Logistics Management System

Production-ready Django 5 project scaffold for fleet operations, logistics workflows, live tracking, and reporting.

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

4. Visit:

- App: http://localhost:8000
- Admin: http://localhost:8000/admin/