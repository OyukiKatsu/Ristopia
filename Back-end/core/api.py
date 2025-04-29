from rest_framework import serializers, viewsets
from .models import Profile

# Serializer to convert model data into JSON
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['id', 'user']

# ViewSet to handle requests for profiles
class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
