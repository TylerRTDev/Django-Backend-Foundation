from .base import *

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')
# Default DB is SQLite via base.py Override to Postgres for dev environment and Docker setup

CSRF_TRUSTED_ORIGINS = ['https://festive-lowell-leguminous.ngrok-free.dev']

INSTALLED_APPS += [
    'storages',
]  # for S3/MinIO storage backend

DATABASES = {
    'default': {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("POSTGRES_DB", "django_test_db"),
        "USER": config("POSTGRES_USER"),
        "PASSWORD": config("POSTGRES_PASSWORD", "changeme"),
        "HOST": config("POSTGRES_HOST", "db"),  # Docker service name
        "PORT": config("POSTGRES_PORT", "5432"),
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.memcached.PyMemcacheCache",
        "LOCATION": "memcached:11211",
        "OPTIONS": {
            "connect_timeout": 1,  # fail fast if memcached is not available
            "timeout": 1,          # short timeout for operations
            "ignore_exc": True,     # don't raise exceptions if memcached is down
        },
    }
}

# Storage settings for MinIO (S3-compatible) backend (Single Bucket) & Whitenoise for static files
#
# 
#
# STORAGES = { 
#     'default': {
#         'BACKEND': 'config.storage_backends.MinioMediaStorageTesting',
#     },

#     "staticfiles": {
#         "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
#         "OPTIONS": {},
#     }
# }

# Storage configuration to include multiple bucket storage with MinIO and bucket configurations

STORAGES = { 
    "default": {
        "BACKEND": "config.storage_backends.MinioMediaStorageTesting",
    },
    
    "staticfiles": {
        "BACKEND": "config.storage_backends.MinioStaticStorageTesting",
        "OPTIONS": {},
    },
    
    "privatefiles": {
        "BACKEND": "config.storage_backends.MinioMediaStoragePrivateTesting",
        "OPTIONS": {},
    }
}

# MinIO specific settings

MINIO_ENDPOINT_INTERNAL = config("MINIO_ENDPOINT_INTERNAL")
MINIO_PUBLIC_DOMAIN = config("MINIO_PUBLIC_DOMAIN")

# The ACCESS_KEY and SECRET_KEY are deprecated in favor of MINIO_ROOT_USER and MINIO_ROOT_PASSWORD

AWS_S3_ENDPOINT_URL = MINIO_ENDPOINT_INTERNAL
AWS_S3_CUSTOM_DOMAIN = MINIO_PUBLIC_DOMAIN
AWS_S3_ACCESS_KEY_ID = config("AWS_S3_ACCESS_KEY_ID", default="minioadmin")
AWS_S3_SECRET_ACCESS_KEY = config("AWS_S3_SECRET_ACCESS_KEY", default="minioadmin")
AWS_ADDRESSING_STYLE = config("AWS_ADDRESSING_STYLE", default="path")  # 'path' or 'virtual'
AWS_S3_USE_SSL = False # MinIO in dev uses HTTP
AWS_S3_VERIFY = False  # Whether to verify SSL certificates
AWS_S3_REGION_NAME = config("AWS_S3_REGION_NAME", default="eu-west-1")  # arbitrary but consistent
