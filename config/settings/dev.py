from .base import *

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')
# Default DB is SQLite via base.py; 
# Override to Postgres for dev environment and Docker setup

INSTALLED_APPS += [
    'storages'
]  # for S3/MinIO storage backend

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

# The ACCESS_KEY and SECRET_KEY are deprecated in favor of MINIO_ROOT_USER and MINIO_ROOT_PASSWORD

AWS_S3_ACCESS_KEY_ID = config("AWS_S3_ACCESS_KEY_ID", default="minioadmin")
AWS_S3_SECRET_ACCESS_KEY = config("AWS_S3_SECRET_ACCESS_KEY", default="minioadmin")
AWS_S3_ENDPOINT_URL = config("MINIO_ENDPOINT_INTERNAL", default="http://minio:9000")
AWS_STORAGE_BUCKET_NAME = config("MINIO_BUCKET_NAME", default="somebucket")
AWS_S3_URL_PROTOCOL = config("AWS_S3_URL_PROTOCOL", default="http:") # http (dev only) or https
AWS_S3_ADDRESSING_STYLE = config("AWS_S3_ADDRESSING_STYLE", default="path")  # path or virtual http://bucketname/...
AWS_S3_USE_SSL = config("AWS_S3_USE_SSL", default=False, cast=bool)
AWS_S3_VERIFY = config("AWS_S3_VERIFY", default=False, cast=bool)  # Whether to verify SSL certificates
AWS_QUERYSTRING_AUTH = config("AWS_QUERYSTRING_AUTH", default=True, cast=bool) # (False) Public read access; no signed URLs
AWS_S3_REGION_NAME = config("AWS_S3_REGION_NAME", default="eu-west-1")  # arbitrary but consistent

# Media files served from MinIO (Optional; uncomment if needed)

# AWS_S3_CUSTOM_DOMAIN = f"{config('MINIO_PUBLIC_URL')}/{config('MINIO_BUCKET_NAME')}"  # Public URL for accessing media files
# MEDIA_URL = f"{AWS_S3_URL_PROTOCOL}//{AWS_S3_CUSTOM_DOMAIN}/"
