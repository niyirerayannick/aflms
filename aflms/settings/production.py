import logging
import secrets

import dj_database_url
from decouple import config
from decouple import Csv
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from .base import *  # noqa: F403,F401

_logger = logging.getLogger("aflms.settings")

def _env_bool(value, default=False):
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "t", "yes", "y", "on", "debug", "dev"}:
        return True
    if normalized in {"0", "false", "f", "no", "n", "off", "release", "prod", "production"}:
        return False
    return default


DEBUG = _env_bool(config("DEBUG", default=False), default=False)

# ── SECRET_KEY ────────────────────────────────────────────────────
# Auto-generate if missing so the container can always boot.
# A warning is logged — set a persistent key in production.
_secret = config("SECRET_KEY", default="")
if not _secret:
    _secret = secrets.token_urlsafe(64)
    _logger.warning(
        "SECRET_KEY not set — using auto-generated key. "
        "Sessions will be lost on restart. Set SECRET_KEY in env vars!"
    )
SECRET_KEY = _secret

# ── Hosts / CSRF ─────────────────────────────────────────────────
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="*", cast=Csv())  # noqa: F405
# Always allow localhost for Docker healthcheck
for _h in ("localhost", "127.0.0.1"):
    if _h not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(_h)
CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default="https://localhost",
    cast=Csv(),
)  # noqa: F405

# ── Database ──────────────────────────────────────────────────────
DATABASE_URL = config("DATABASE_URL", default="sqlite:///app/db.sqlite3")
_db_ssl = config("DATABASE_SSL_REQUIRE", default=False, cast=bool)
DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=_db_ssl)}  # noqa: F405

# ── Reverse Proxy (Coolify / Traefik) ─────────────────────────────
# Coolify terminates SSL at the proxy and forwards HTTP to Django.
# These headers let Django reconstruct the correct public URL.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=False, cast=bool)
SESSION_COOKIE_SECURE = config("SESSION_COOKIE_SECURE", default=True, cast=bool)
CSRF_COOKIE_SECURE = config("CSRF_COOKIE_SECURE", default=True, cast=bool)
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = (
    "'self'",
    "'unsafe-inline'",
    "https://cdn.jsdelivr.net",
    "https://cdn.tailwindcss.com",
)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://fonts.googleapis.com")
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com", "data:")
CSP_IMG_SRC = (
    "'self'",
    "data:",
    "blob:",
    "res.cloudinary.com",
)
CSP_CONNECT_SRC = ("'self'", "wss:", "https:")
CSP_FRAME_ANCESTORS = ("'none'",)

if USE_CLOUDINARY:  # noqa: F405
    DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"
    MEDIA_URL = f"https://res.cloudinary.com/{CLOUDINARY_STORAGE['CLOUD_NAME']}/"  # noqa: F405

sentry_dsn = config("SENTRY_DSN", default="")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[DjangoIntegration()],
        traces_sample_rate=config("SENTRY_TRACES_SAMPLE_RATE", default=0.1, cast=float),
        send_default_pii=config("SENTRY_SEND_PII", default=False, cast=bool),
    )

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s"
        },
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(name)s %(module)s %(process)d %(thread)d %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        }
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
        "celery": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "channels": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

# Email configuration (read from environment variables in production).
# Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in Coolify / environment secrets.
from decouple import config as _config

EMAIL_HOST = _config("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = _config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = _config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_HOST_USER = _config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = _config("EMAIL_HOST_PASSWORD", default="")

if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    DEFAULT_FROM_EMAIL = _config("DEFAULT_FROM_EMAIL", default=EMAIL_HOST_USER)
else:
    # fallback to console backend so the app still boots without secrets
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

