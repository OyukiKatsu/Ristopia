from django.shortcuts import render, redirect
from rest_framework.response import Response
from core.models import Profile, Worker
from django.contrib.auth.models import User
from django.views import View
from django.views.generic import TemplateView
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.core.exceptions import PermissionDenied

# Create your views here.

class RegisterView(TemplateView):
    template_name = 'User/register.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
    
    def post(self, request, *args, **kwargs):
        try:
            username = request.POST['username']
            email = request.POST['email']
            password = request.POST['password']
            profile_pic = request.FILES.get('profile_picture')  

            user = User.objects.create_user(username=username, email=email, password=password)
            profile = Profile.objects.create(user=user, email=email, profile_picture=profile_pic)

            return JsonResponse({'message': 'User created successfully'}, status=200)

        except KeyError as e:
            return JsonResponse({'error': f'Missing field: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)



class LoginView(TemplateView):
    template_name = 'User/login.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        login_type = request.POST.get('login_type')

        if login_type == 'owner':
            username_or_email = request.POST.get('username')
            password = request.POST.get('password')

            # Support login with email or username
            try:
                user_obj = User.objects.get(email=username_or_email)
                username = user_obj.username
            except User.DoesNotExist:
                username = username_or_email

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)

                try:
                    profile = user.get_User_Profile  # OneToOne Profile
                    return redirect('owner_dashboard', owner_id=profile.id)
                except Profile.DoesNotExist:
                    messages.error(request, "User profile not found.")
            else:
                messages.error(request, "Invalid username or password.")

        elif login_type == 'worker':
            login_code = request.POST.get('login_code')

            try:
                worker = Worker.objects.get(login_code=login_code, active=True)
                user = worker.user.user  # Profile → User
                login(request, user)

                if worker.type == 'Chef':
                    return redirect('chef_dashboard', chef_id=worker.id)
                elif worker.type == 'Waiter':
                    return redirect('waiter_dashboard', waiter_id=worker.id)
                else:
                    messages.error(request, "Unknown worker type.")
            except Worker.DoesNotExist:
                messages.error(request, "Invalid or inactive login code.")

        return render(request, self.template_name)


class OwnerView(TemplateView):
    template_name = 'User/owner.html'

    def get(self, request, owner_id):
        user = request.user

        try:
            profile = Profile.objects.get(id=owner_id, user=user)
        except Profile.DoesNotExist:
            raise PermissionDenied("403 Forbidden: You don't have access to this owner's dashboard.")

        context = {
            'username': user.username,
            'role': 'Owner'
        }
        return render(request, self.template_name, context)


class ChefView(TemplateView):
    template_name = 'User/chef.html'

    def get(self, request, chef_id):
        user = request.user

        try:
            worker = Worker.objects.get(id=chef_id, user__user=user, type='Chef')
        except Worker.DoesNotExist:
            raise PermissionDenied("403 Forbidden: You don't have access to this chef dashboard.")

        context = {
            'username': user.username,
            'role': 'Chef'
        }
        return render(request, self.template_name, context)


class WaiterView(TemplateView):
    template_name = 'User/waiter.html'

    def get(self, request, waiter_id):
        user = request.user

        try:
            worker = Worker.objects.get(id=waiter_id, user__user=user, type='Waiter')
        except Worker.DoesNotExist:
            raise PermissionDenied("403 Forbidden: You don't have access to this waiter dashboard.")

        context = {
            'username': user.username,
            'role': 'Waiter'
        }
        return render(request, self.template_name, context)