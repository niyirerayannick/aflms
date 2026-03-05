from .base import *  # noqa: F403,F401

DEBUG = True

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

INTERNAL_IPS = ["127.0.0.1"]

# Allow ngrok tunnel for Twilio webhook development
ALLOWED_HOSTS = ["*"]
CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:8080",
    "http://localhost:8080",
    "https://poor-arlette-unnettled.ngrok-free.dev",
]

# Twilio status callback via ngrok
TWILIO_STATUS_CALLBACK_URL = "https://poor-arlette-unnettled.ngrok-free.dev/api/whatsapp/status/"
