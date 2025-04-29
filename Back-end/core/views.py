from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Profile
from .serializers import ProfileSerializer  # Import the serializer
from django.shortcuts import render

class ProfileListView(APIView):
    def get(self, request):
        profiles = Profile.objects.all()  # Get all profiles
        serializer = ProfileSerializer(profiles, many=True)  # Serialize the profiles
        return Response(serializer.data)  # Return the serialized data as JSON

def Index(request):
    return render(request, 'index.html')