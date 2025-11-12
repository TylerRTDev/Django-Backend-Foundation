from .base import *

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')
# Default DB is SQLite via base.py; 
# Override to Postgres for dev environment and Docker setup

INSTALLED_APPS += ['storages']  # for S3/MinIO storage backend

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

# Storage settings for MinIO (S3-compatible) backend
STORAGES = { 
    'default': {
        'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage',
    },
    
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        "OPTIONS": {},
    }
}

# AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID")
# AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY")
# AWS_S3_REGION_NAME = config("AWS_S3_REGION_NAME")
AWS_S3_ENDPOINT_URL = config("MINIO_ENDPOINT_INTERNAL", default="http://minio:9000")
AWS_STORAGE_BUCKET_NAME = config("MINIO_BUCKET_NAME", default="somebucket")

AWS_S3_CUSTOM_DOMAIN = f"{config('MINIO_PUBLIC_URL')}/{config('MINIO_BUCKET_NAME')}"  # Public URL for accessing media files
AWS_S3_URL_PROTOCOL = "http:"          # dev only
AWS_S3_ADDRESSING_STYLE = "path"       # http://host/bucket/key
AWS_S3_USE_SSL=False
AWS_S3_VERIFY=False
AWS_QUERYSTRING_AUTH=False


MEDIA_URL = f"{AWS_S3_URL_PROTOCOL}//{AWS_S3_CUSTOM_DOMAIN}/{AWS_STORAGE_BUCKET_NAME}/"
print("MEDIA_URL:", MEDIA_URL)