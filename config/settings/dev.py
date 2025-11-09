from .base import *

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')
# Default DB is SQLite via base.py; 
# Override to Postgres for dev environment and Docker setup

DATABASES = {
    'default': {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("POSTGRES_DB", "language_app_dev"),
        "USER": config("POSTGRES_USER", "language_app_user"),
        "PASSWORD": config("POSTGRES_PASSWORD", "changeme"),
        "HOST": config("POSTGRES_HOST", "db"),  # Docker service name
        "PORT": config("POSTGRES_PORT", "5432"),
    }
}