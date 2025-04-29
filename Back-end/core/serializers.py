# serializers.py
from rest_framework import serializers
from .models import Profile

class ProfileSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username')  # Include the username from the user model

    class Meta:
        model = Profile
        fields = ['id', 'user_username']  # You can add other fields you want to include in the API response
