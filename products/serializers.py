from rest_framework import serializers


class QuoteSerializer(serializers.Serializer):
    content = serializers.CharField()
    author = serializers.CharField()