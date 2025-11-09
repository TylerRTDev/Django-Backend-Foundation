from .base import *
from decouple import config


DEBUG = False
ALLOWED_HOSTS = config("ALLOWED_HOSTS")  # e.g. yourdomain.com

# Security headers (enable when going live)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Later, enable Whitenoise
# MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
# STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# In prod you'll set DATABASE to Postgres
DATABASES = {
    'default': {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("POSTGRES_DB_PROD", "language_app_dev"),
        "USER": config("POSTGRES_USER_PROD", "language_app_user"),
        "PASSWORD": config("POSTGRES_PASSWORD_PROD", "changeme"),
        "HOST": config("POSTGRES_HOST_PROD", "db"),  # Docker service name
        "PORT": config("POSTGRES_PORT_PROD", "5432"),
    }
}
