from django.contrib import admin
from .models import Product


# Register your models here.
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "price", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "description")

