from storages.backends.s3boto3 import S3Boto3Storage
from decouple import config

class MinioStaticStorageTesting(S3Boto3Storage):
    """
    Static files stored in MinIO 'static' bucket.
    Django will use this for staticfiles in dev.
    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("bucket_name", config('MINIO_STATIC_BUCKET_NAME', default='static'))
        super().__init__(*args, **kwargs)
    location = ""
    default_acl = "public-read" # or "private" if you want to restrict access
    file_overwrite = True  # hashed filenames anyway
    custom_domain = config('MINIO_PUBLIC_DOMAIN') + '/' + config('MINIO_STATIC_BUCKET_NAME') # localhost:9000/static
    querystring_auth = False  # public read, no need for query params. Set to (True) for private files
    url_protocol = "http:" # MinIO in dev uses HTTP


class MinioMediaStorageTesting(S3Boto3Storage):
    """
    Media files stored in MinIO 'pubmedia' bucket.
    Django will use this for media files in dev.
    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("bucket_name", config("MINIO_MEDIA_BUCKET_NAME", default="pubmedia"))
        super().__init__(*args, **kwargs)
    location = ""
    default_acl = "public-read" # or "private" if you want to restrict access
    file_overwrite = False  # keep originals by default
    custom_domain = None    # we’ll use endpoint URL in MEDIA_URL
    querystring_auth = False  # public read, no need for query params. Set to (True) for private files
    
class MinioMediaStoragePrivateTesting(S3Boto3Storage):
    """
    Private media files stored in MinIO 'prvmedia' bucket.
    Django will use this for private media files in dev.
    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("bucket_name", config("MINIO_PRIVATE_MEDIA_BUCKET_NAME", default="prvmedia"))
        super().__init__(*args, **kwargs)
    location = ""
    default_acl = "private" # or "private" if you want to restrict access
    file_overwrite = False  # keep originals by default
    custom_domain = None    # we’ll use endpoint URL in MEDIA_URL
    querystring_auth = True  # public read, no need for query params. Set to (True) for private files