# accounts/serializers.py
from rest_framework import serializers
from .models import User, Profile

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            "display_name", "bio", "date_of_birth", "timezone",
            "language", "avatar", "website", "twitter", "instagram",
            "preferences",
        ]

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = User
        # Add username to the serialized fields (Optional)
        fields = ["id", "email", "first_name", "last_name", "is_verified", "profile"]
        read_only_fields = ["id", "is_verified"]
