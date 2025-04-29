from django.shortcuts import render
from requests import Response
from core.models import Profile
from django.contrib.auth.models import User
from django.views import View
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json


# Create your views here.
@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(View):
    def post(self, request, *args, **kwargs):
        try:
            username = request.POST['username']
            email = request.POST['email']
            password = request.POST['password']
            profile_pic = request.FILES.get('profile_picture')  # get the uploaded image

            user = User.objects.create_user(username=username, email=email, password=password)
            profile = Profile.objects.create(user=user, email=email, profile_picture=profile_pic)

            return JsonResponse({'message': 'User created successfully'}, status=200)

        except KeyError as e:
            return JsonResponse({'error': f'Missing field: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)




