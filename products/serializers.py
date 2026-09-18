from rest_framework import serializers

from .models import Product


class QuoteSerializer(serializers.Serializer):
    content = serializers.CharField()
    author = serializers.CharField()


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "description", "price", "product_img",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]