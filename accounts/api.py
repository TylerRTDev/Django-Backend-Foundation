# accounts/api.py
from rest_framework import viewsets, permissions
from .models import User
from .serializers import UserSerializer

class MeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # limit to the requesting user only
        return User.objects.filter(pk=self.request.user.pk)
