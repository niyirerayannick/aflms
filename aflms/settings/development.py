from .base import *  # noqa: F403,F401
import os

DEBUG = True

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Email configuration: default to console backend for development.
# To enable real Gmail SMTP, set the environment variables
# EMAIL_HOST_USER and EMAIL_HOST_PASSWORD (use an App Password if your account
# has 2FA enabled). When both are present, the SMTP backend will be used.
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")

if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = "smtp.gmail.com"
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = EMAIL_HOST_USER
    EMAIL_HOST_PASSWORD = EMAIL_HOST_PASSWORD
    DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)
else:
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
