from django.db import models
from django.core.validators import FileExtensionValidator
from config.storage_backends import MinioMediaStorageTesting

media_storage = MinioMediaStorageTesting()

def product_image_upload_to(instance: "Product", filename: str) -> str:
    return f"product/{instance.name}/{filename}"
class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    product_img = models.ImageField(
        storage=media_storage,
        upload_to=product_image_upload_to,
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "webp"])],
    )
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
