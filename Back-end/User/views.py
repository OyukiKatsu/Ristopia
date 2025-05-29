from django.shortcuts import render, redirect, get_object_or_404
from core.models import CategoryElement, Profile, Worker, TableOrder, Restaurante, Category, Menu, Map, Table, Bar, TableCell, BarCell
from django.contrib.auth.models import User
from django.views.generic import TemplateView, View
from django.urls import reverse
from django.utils.timezone import now, timedelta
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Sum
from datetime import datetime, timedelta
from django.db.models.functions import TruncHour, TruncDay, TruncDate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.template.loader import render_to_string
import random
import string
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
import json
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from core.utils import generate_table_qr
# ========================================================================== #
# ====== Dysplay Pages ====== #
# ========================================================================== #


# ====== User Control ====== #
class RegisterView(TemplateView):
    template_name = 'User/register.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        profile_pic = request.FILES.get('profile_picture')
        restaurant_name = request.POST.get('restaurant_name')
        restaurant_icon = request.FILES.get('restaurant_icon')


        if not all([username, email, password1, password2]):
            messages.error(request, 'Error|All fields are required.')
            return render(request, self.template_name)

        if password1 != password2:
            messages.error(request, 'Error|Passwords do not match.')
            return render(request, self.template_name)

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Error|Username already taken.')
            return render(request, self.template_name)

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Error|Email is already registered.')
            return render(request, self.template_name)

        try:
            user = User.objects.create_user(username=username, email=email, password=password1)

            profile = Profile.objects.create(user=user, email=email, profile_picture=profile_pic)

            restaurante = Restaurante.objects.create(name=restaurant_name, icon=restaurant_icon, owner=profile)

            messages.success(request, 'Succes|User created successfully. Login to continue!')
            html_content = render_to_string("core/emails/emailbase.html", {
                "title": "Welcome to Ristòpia, " + username,
                "message": "Thank you for joining our platform! We're excited to have you."
                })
            send_mail("Welcome to Ristòpia", "", "ristopia123@gmail.com", [email], html_message=html_content)
                        
        except Exception as e:
            messages.error(request, f'Error|An error occurred: {str(e)}')
            return render(request, self.template_name)
        return redirect('custom_login')
class LoginView(TemplateView):
    template_name = 'User/login.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        login_type = request.POST.get('login_type')

        if login_type == 'owner':
            username = request.POST.get('username')
            password = request.POST.get('password')

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)

                try:
                    profile = user.get_User_Profile  
                    return redirect('owner_dashboard', owner_id=profile.id)
                except Profile.DoesNotExist:
                    messages.error(request, "Error|User profile not found.")
            else:
                messages.error(request, "Error|Invalid username or password.")

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
                    messages.error(request, "Error|Unknown worker type.")
            except Worker.DoesNotExist:
                messages.error(request, "Error|Invalid or inactive login code.")

        return render(request, self.template_name)
class ResetPasswordView(TemplateView):
    template_name = 'User/reset-password.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)     
class ResetPasswordTokenView(TemplateView):
    template_name = 'User/reset-password-confirm.html'

    def get(self, request, uidb64=None, token=None, *args, **kwargs):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            return render(request, self.template_name, {'validlink': True, 'uidb64': uidb64, 'token': token})
        else:
            messages.error(request, 'The reset link is invalid or has expired.')
            return render(request, self.template_name, {'validlink': False})

    def post(self, request, uidb64=None, token=None, *args, **kwargs):
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return redirect(request.path)

        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            messages.error(request, 'Invalid user.')
            return redirect(request.path)

        if user is not None and default_token_generator.check_token(user, token):
            user.set_password(password1)
            user.save()
            messages.success(request, 'Password reset successfully. You can now log in.')
            return redirect('custom_login')
        else:
            messages.error(request, 'Invalid or expired link.')
            return redirect(request.path)

# ====== Owner Dashboards ====== #
class OwnerView(TemplateView):
    template_name = 'User/owner.html'

    def get(self, request, owner_id, *args, **kwargs):
        try:
            owner_profile = Profile.objects.get(id=owner_id)
        except Profile.DoesNotExist:
            raise PermissionDenied("403 Forbidden: You don't have access to this owner's dashboard.")

        if request.user != owner_profile.user:
            raise PermissionDenied("403 Forbidden: You don't have access to this owner's dashboard.")

        


        context = self.get_context_data(**kwargs)
        return render(request, self.template_name, context)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        owner_id = self.kwargs.get('owner_id')
        profile = Profile.objects.get(id=owner_id)

        today = datetime.now().date()
        orders_today = TableOrder.objects.filter(
            table__map__restaurant__owner=profile,
            date__date=today,
            active=True
        )

        profit = orders_today.aggregate(total_profit=Sum('category_element__price'))['total_profit'] or 0
        cost = orders_today.aggregate(total_cost=Sum('category_element__cost'))['total_cost'] or 0

        top_dish = (orders_today
            .values('category_element__name')
            .annotate(count=Count('id'))
            .order_by('-count')
            .first()
        )

        context['stats'] = { 
            'Today_Profit': round(profit, 2),
            'Today_Cost': round(cost, 2),
            'Top_Dish_Today': top_dish['category_element__name'] if top_dish else "N/A",
        }
        context['owner_id'] = owner_id
        return context

# === Menu ==== #  
class MenuView(TemplateView):
    template_name = 'User/menu.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.request.user.get_User_Profile
        restaurant = profile.get_Profile_Restaurantes.first()
        menu = Menu.objects.filter(restaurant=restaurant).first()

        context['profile'] = profile
        context['restaurant'] = restaurant
        context['menu'] = menu
        return context
    
    def get(self, request, owner_id, *args, **kwargs):
        try:
            owner_profile = Profile.objects.get(id=owner_id)
        except Profile.DoesNotExist:
            raise PermissionDenied("403 Forbidden: You don't have access to this owner's dashboard.")

        if request.user != owner_profile.user:
            raise PermissionDenied("403 Forbidden: You don't have access to this owner's dashboard.")
    
        return render(request, self.template_name, self.get_context_data(**kwargs))

# === Worker ==== #
class WorkersView(TemplateView):
    template_name = 'User/workers.html'
            
    def get(self, request, owner_id, *args, **kwargs):
        try:
            owner_profile = Profile.objects.get(id=owner_id)
        except Profile.DoesNotExist:
            raise PermissionDenied("403 Forbidden: You don't have access to this owner's dashboard.")

        if request.user != owner_profile.user:
            raise PermissionDenied("403 Forbidden: You don't have access to this owner's dashboard.")

        profile = Profile.objects.get(id=owner_id)
        restaurant = profile.get_Profile_Restaurantes.first()
        workers = restaurant.get_Restaurante_Workers.all()
        context = {
            'restaurant': restaurant,
            'workers': workers,
            'profile': profile,
            }

        return render(request, self.template_name, context)

# ====== Worker Dashboards ====== #
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
            'role': 'Chef',
            'restaurantID': worker.restaurant.id
        }
        return render(request, self.template_name, context)
  
# === Map Creator ==== #
class MapCreatorView(TemplateView):
    template_name = 'User/map.html'

    def get(self, request, owner_id, *args, **kwargs):
        profile = get_object_or_404(Profile, id=owner_id)
        if request.user != profile.user:
            raise PermissionDenied

        restaurant = profile.get_Profile_Restaurantes.first()
        all_maps = Map.objects.filter(restaurant=restaurant)

        maps_payload = []
        for m in all_maps:
            maps_payload.append({
                'id': m.id,
                'name': m.name,
                'w': m.dimension_x,
                'h': m.dimension_y,
                'tables': [
                    {
                    'id': tbl.id,
                        'name': tbl.name,
                        'cells': list(tbl.cells.values('x','y'))
                    }
                    for tbl in m.get_Map_Tables.all()
                ],
                'bars': [
                    {
                    'id': bar.id,
                        'cells': list(bar.cells.values('x','y'))
                    }
                    for bar in m.get_Map_Bars.all()
                ]
            })

        context = {
            'profile': profile,
            'restaurant': restaurant,
            'maps_json': json.dumps(maps_payload, cls=DjangoJSONEncoder),
        }
        return render(request, self.template_name, context)
    
# ========================================================================== #
# ========== "APIs" =========== #
# ========================================================================== #


# ====== User Control ====== #
class ResetPasswordEmailView(View):
    def post(self, request, *args, **kwargs):
        username = request.POST.get('username')
        user = User.objects.filter(username=username).first()
        if user:

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            reset_url = request.build_absolute_uri(
                reverse('custom_password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
            )

            if user:                        
                html_content = render_to_string("core/emails/email_password_reset.html", {
                    "title": "Reset Your Password",
                    "message": "Click the button below to reset your password. If you didn’t request this, you can safely ignore this email.",
                    "reset_url": reset_url
                })
                send_mail("Reset Your Password", "", "ristopia123@gmail.com", [user.get_User_Profile.email], html_message=html_content)
        return HttpResponse(status=200)

# ====== Owner Dashboards ====== #
class DashboardChartData(View):
    def get(self, request, *args, **kwargs):
        chart_type = request.GET.get('type')
        time_range = request.GET.get('range')
        owner_id = request.GET.get('owner_id')
        if request.user.get_User_Profile.id != int(owner_id):
            return JsonResponse({'error': "Permission denied."}, status=403)
        profile = Profile.objects.get(id=owner_id)
        now_time = now()
        data = {}
        label = ""
        queryset = TableOrder.objects.filter(table__map__restaurant__owner=profile)

        if time_range == '1d':
            start = now_time.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
            truncate = TruncHour('date')
            label_format = "%H:%M"
        elif time_range == '1w':
            start = now_time - timedelta(days=now_time.weekday())
            end = start + timedelta(days=7)
            truncate = TruncDay('date')
            label_format = "%A"
        elif time_range == '1m':
            start = now_time.replace(day=1)
            end = (start + timedelta(days=32)).replace(day=1)
            truncate = TruncDate('date')
            label_format = "%d %b"
        else:
            return JsonResponse({'error': 'Invalid range'}, status=400)

        queryset = queryset.filter(date__range=(start, end))

        if chart_type in ['profit', 'cost']:
            values_field = 'category_element__price' if chart_type == 'profit' else 'category_element__cost'
            grouped = queryset.annotate(period=truncate).values('period').annotate(
                total=Sum(values_field)).order_by('period')
            data['labels'] = [entry['period'].strftime(label_format) for entry in grouped]
            data['data'] = [float(entry['total']) for entry in grouped]

        elif chart_type == 'most_ordered':
            grouped = queryset.values('category_element__name').annotate(
                count=Count('id')).order_by('-count')[:5]
            data['labels'] = [entry['category_element__name'] for entry in grouped]
            data['data'] = [entry['count'] for entry in grouped]

        else:
            return JsonResponse({'error': 'Invalid chart type'}, status=400)

        return JsonResponse(data)

# === Menu ==== #
class CreateMenuView(LoginRequiredMixin, View):
    def post(self, request, owner_id,*args, **kwargs):
        if request.user.get_User_Profile.id != int(owner_id):
            return JsonResponse({'error': "Permission denied."}, status=403)
        profile = request.user.get_User_Profile
        restaurant = profile.get_Profile_Restaurantes.first()
        if not Menu.objects.filter(restaurant=restaurant).exists():
            Menu.objects.create(restaurant=restaurant)
            messages.success(request, 'Success|Menu created successfully.')
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'exists'})

# === Category ==== #
class CreateCategoryView(LoginRequiredMixin, View):
    def post(self, request, owner_id, *args, **kwargs):
        if request.user.get_User_Profile.id != int(owner_id):
            return JsonResponse({'error': "Permission denied."}, status=403)
        menu_id = request.POST.get('menu_id')
        name = request.POST.get('name')

        menu = get_object_or_404(Menu, id=menu_id)

        category = Category.objects.create(menu=menu, name=name)
        messages.success(request, f'Success|Category "{name}" added.')

        return JsonResponse({
            'status': 'success',
            'category_id': category.id,
            'category_name': category.name
        })
class ToggleCategoryActiveView(LoginRequiredMixin, View):
    def post(self, request, owner_id, pk):
        category = get_object_or_404(Category, pk=pk, menu__restaurant__owner__id=owner_id)
        if request.user.get_User_Profile.id != int(owner_id):
            return JsonResponse({'error': "Permission denied."}, status=403)
        
        category.active = not category.active
        category.save()
        return JsonResponse({'status': 'success', 'active': category.active})
class UpdateCategoryView(LoginRequiredMixin, View):
    def post(self, request, owner_id, pk):
        category = get_object_or_404(Category, pk=pk, menu__restaurant__owner__id=owner_id)
        if request.user.get_User_Profile.id != int(owner_id):
            return JsonResponse({'error': "Permission denied."}, status=403)

        new_name = request.POST.get('name')
        if not new_name:
            return JsonResponse({'error': "Name is required."}, status=400)

        category.name = new_name
        category.save()
        return JsonResponse({'status': 'success', 'name': category.name})
class DeleteCategoryView(LoginRequiredMixin, View):
    def post(self, request, owner_id, pk):
        category = get_object_or_404(Category, pk=pk, menu__restaurant__owner__id=owner_id)
        if request.user.get_User_Profile.id != int(owner_id):
            return JsonResponse({'error': "Permission denied."}, status=403)
        category.delete()
        return JsonResponse({'status': 'success'})
class CategoryElementsView(LoginRequiredMixin, View):
    def get(self, request, owner_id, category_id):
        elements = CategoryElement.objects.filter(category_id=category_id)
        data = []
        for element in elements:
            data.append({
                'id': element.id,
                'name': element.name,
                'description': element.description,
                'price': str(element.price),
                'cost': str(element.cost),
                'icon_url': element.icon.url if element.icon else '',
                'active': element.active,
            })
        return JsonResponse({'elements': data})

# === Category Element ==== #
class CreateCategoryElementView(LoginRequiredMixin, View):
    def post(self, request, owner_id, *args, **kwargs):
        if request.user.get_User_Profile.id != int(owner_id):
            return JsonResponse({'error': "Permission denied."}, status=403)
        category_id = request.POST.get('category_id')
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        cost = request.POST.get('cost')
        icon = request.FILES.get('icon') 
        

        category = get_object_or_404(Category, id=category_id)
        if icon:
            element = CategoryElement.objects.create(
                category=category,
                name=name,
                description=description,
                price=price,
                cost=cost,
                icon=icon  
            )
        else:
            element = CategoryElement.objects.create(
                category=category,
                name=name,
                description=description,
                price=price,
                cost=cost
            )

        messages.success(request, f'Success|Item "{name}" added to category "{category.name}".')
        return JsonResponse({
            'status': 'success',
            'element_id': element.id,
            'element_name': element.name,
            'icon_url': element.icon.url if element.icon else ''
        }) 
class ToggleCategoryElementActiveView(LoginRequiredMixin, View):
    def post(self, request, owner_id, *args, **kwargs):
        element_id = request.POST.get('element_id')
        element = get_object_or_404(CategoryElement, id=element_id)
        # ownership check
        if element.category.menu.restaurant.owner.id != int(owner_id):
            return JsonResponse({'status':'error','msg':'Forbidden'}, status=403)
        element.active = not element.active
        element.save()
        return JsonResponse({'status':'success','element_id':element.id,'active':element.active})
class UpdateCategoryElementView(LoginRequiredMixin, View):
    def post(self, request, owner_id, *args, **kwargs):
        element_id = request.POST.get('element_id')
        element = get_object_or_404(CategoryElement, id=element_id)
        if element.category.menu.restaurant.owner.id != int(owner_id):
            return JsonResponse({'status':'error','msg':'Forbidden'}, status=403)
        # pull updated fields
        element.name        = request.POST.get('name', element.name)
        element.description = request.POST.get('description', element.description)
        element.price       = request.POST.get('price', element.price)
        element.cost        = request.POST.get('cost', element.cost)
        if request.FILES.get('icon'):
            element.icon     = request.FILES['icon']
        element.save()
        return JsonResponse({
            'status':'success',
            'element_id': element.id,
            'name': element.name,
            'description': element.description,
            'price': str(element.price),
            'cost': str(element.cost),
            'icon_url': element.icon.url if element.icon else ''
        })
class DeleteCategoryElementView(LoginRequiredMixin, View):
    def post(self, request, owner_id, *args, **kwargs):
        element_id = request.POST.get('element_id')
        element = get_object_or_404(CategoryElement, id=element_id)
        if element.category.menu.restaurant.owner.id != int(owner_id):
            return JsonResponse({'status':'error','msg':'Forbidden'}, status=403)
        element.delete()
        return JsonResponse({'status':'success','element_id': element_id})
    
# === Worker ==== #
class CreateWorkerView(View):

    def generate_unique_login_code(self):
        characters = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(random.choices(characters, k=5))
            if not Worker.objects.filter(login_code=code).exists():
                return code
        
    def post(self, request, owner_id):
        if request.user.get_User_Profile.id != int(owner_id):
            return JsonResponse({'error': "Permission denied."}, status=403)
        profile = get_object_or_404(Profile, id=owner_id)
        restaurant = profile.get_Profile_Restaurantes.first()

        username = request.POST.get('username')
        email = request.POST.get('email')
        worker_type = request.POST.get('type')
        picture = request.FILES.get('picture')

        if not username or not email or not worker_type:
            return JsonResponse({'status': 'error', 'message': 'Missing required fields.'})

        if User.objects.filter(username=username).exists():
            return JsonResponse({'status': 'error', 'message': 'Username already exists.'})
        if Profile.objects.filter(email=email).exists():
            return JsonResponse({'status': 'error', 'message': 'Email already in use.'})

        try:
            user = User.objects.create(username=username)
            user.set_unusable_password()
            user.save()
            if picture:
                worker_profile = Profile.objects.create(user=user, email=email, profile_picture=picture)
            else:
                worker_profile = Profile.objects.create(user=user, email=email)
            login_code = self.generate_unique_login_code()

            worker = Worker.objects.create(restaurant=restaurant, user=worker_profile, login_code=login_code, type=worker_type, active=True)
            
            html_content = render_to_string("core/emails/emailbase.html", {
                "title": "You have been registered as a " + worker_type + " at " + restaurant.name + ".",
                "message": "Your login code is: " + login_code
            })
            send_mail("Registered at "+ restaurant.name, "", "ristopia123@gmail.com", [email], html_message=html_content)            

            return JsonResponse({
                'status': 'success',
                'username': user.username,
                'worker_id': worker.id,
                'email': worker_profile.email,
                'type': worker_type,
                'login_code': worker.login_code,
                'profile_picture_url': worker_profile.profile_picture.url if worker_profile.profile_picture else ''
            })


        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
class ToggleWorkerActiveView(LoginRequiredMixin, View):
    def post(self, request, worker_id, *args, **kwargs):
        worker = get_object_or_404(Worker, id=worker_id)
        if worker not in request.user.get_User_Profile.get_Profile_Restaurantes.first().get_Restaurante_Workers.all():
            return JsonResponse({'status':'error','msg':'Forbidden'}, status=403)
        worker.active = not worker.active
        worker.save()
        return JsonResponse({'status':'success','message':'Worker disabled' if not worker.active else 'Worker enabled'})
class DeleteWorkerView(LoginRequiredMixin, View):
    def post(self, request, worker_id, *args, **kwargs):
        worker = get_object_or_404(Worker, id=worker_id)
        if worker not in request.user.get_User_Profile.get_Profile_Restaurantes.first().get_Restaurante_Workers.all():
            return JsonResponse({'status':'error','msg':'Forbidden'}, status=403)
        
        profile = worker.user
        user = profile.user
        worker.delete()
        profile.delete()
        user.delete()
        return JsonResponse({'status':'success'})
    

# === Map Creator === #
class SaveMapView(View):
    def post(self, request, owner_id):
        if request.user.get_User_Profile.id != int(owner_id):
            return JsonResponse({'error': "Permission denied."}, status=403)
        owner = get_object_or_404(Profile, id=owner_id)
        restaurant = get_object_or_404(Restaurante, owner=owner)
        try:
            payload = json.loads(request.body)
            maps_data = payload['maps']
        except (ValueError, KeyError):
            return HttpResponseBadRequest("Invalid JSON payload")

        with transaction.atomic():
            for m in maps_data:
                map_id = m.get('id')
                name   = m['name']
                w      = m.get('w') or m.get('dimension_x')
                h      = m.get('h') or m.get('dimension_y')
                tables = m.get('tables', [])
                bars   = m.get('bars', [])

                # Map
                if map_id:
                    map_obj = get_object_or_404(Map, pk=map_id, restaurant=restaurant)
                    map_obj.name = name
                    map_obj.dimension_x = w
                    map_obj.dimension_y = h
                    map_obj.save()
                else:
                    map_obj = Map.objects.create(
                        restaurant=restaurant,
                        name=name,
                        dimension_x=w,
                        dimension_y=h
                    )

                # Tables
                # Lookup of existing tables
                existing_tables = { t.id: t for t in map_obj.get_Map_Tables.all() }

                incoming_ids = set()
                for tbl in tables:
                    tbl_id   = tbl.get('id')
                    tbl_name = tbl['name']
                    cells    = tbl.get('cells', [])

                    if tbl_id and tbl_id in existing_tables:
                        # update name if changed
                        tbl_obj = existing_tables[tbl_id]
                        if tbl_obj.name != tbl_name:
                            tbl_obj.name = tbl_name
                            tbl_obj.save()
                    else:
                        tbl_obj = Table.objects.create(map=map_obj, name=tbl_name)
                        qr_path, qr_content = generate_table_qr(tbl_obj, request)
                        tbl_obj.qr_code.save(qr_path, qr_content, save=True)


                    incoming_ids.add(tbl_obj.id)

                    # --- diff cells ---
                    # existing cells set
                    existing_cells = set(
                        map(lambda c: (c.x, c.y), tbl_obj.cells.all())
                    )
                    new_cells = set((c['x'], c['y']) for c in cells)

                    # delete removed cells
                    to_delete = existing_cells - new_cells
                    if to_delete:
                        TableCell.objects.filter(
                            table=tbl_obj,
                            x__in=[x for x,y in to_delete],
                            y__in=[y for x,y in to_delete]
                        ).delete()

                    # insert new cells
                    to_add = new_cells - existing_cells
                    TableCell.objects.bulk_create([
                        TableCell(table=tbl_obj, x=x, y=y)
                        for x,y in to_add
                    ])

                to_remove = set(existing_tables.keys()) - incoming_ids
                Table.objects.filter(id__in=to_remove).delete()

                # Handle Bars
                existing_bars = { b.id: b for b in map_obj.get_Map_Bars.all() }
                incoming_bar_ids = set()

                for bar in bars:
                    bar_id = bar.get('id')
                    cells  = bar.get('cells', [])

                    if bar_id and bar_id in existing_bars:
                        bar_obj = existing_bars[bar_id]
                    else:
                        bar_obj = Bar.objects.create(map=map_obj)

                    incoming_bar_ids.add(bar_obj.id)

                    existing_cells = set(
                        map(lambda c: (c.x, c.y), bar_obj.cells.all())
                    )
                    new_cells = set((c['x'], c['y']) for c in cells)

                    # delete removed cells
                    to_delete = existing_cells - new_cells
                    if to_delete:
                        BarCell.objects.filter(
                            bar=bar_obj,
                            x__in=[x for x,y in to_delete],
                            y__in=[y for x,y in to_delete]
                        ).delete()

                    # insert new cells
                    to_add = new_cells - existing_cells
                    BarCell.objects.bulk_create([
                        BarCell(bar=bar_obj, x=x, y=y)
                        for x,y in to_add
                    ])

                to_remove = set(existing_bars.keys()) - incoming_bar_ids
                Bar.objects.filter(id__in=to_remove).delete()

        return JsonResponse({'status': 'ok'})   
class CreateFloorView(View):
    def post(self, request, owner_id):
        if request.user.get_User_Profile.id != int(owner_id):
            return JsonResponse({'error': "Permission denied."}, status=403)
        data = json.loads(request.body)
        name = data.get('name')
        w = data.get('w')
        h = data.get('h')

        if not (name and isinstance(w, int) and isinstance(h, int)):
            return JsonResponse({'error': 'Invalid data'}, status=400)

        restaurant = get_object_or_404(Restaurante, owner_id=owner_id)

        new_map = Map.objects.create(
            restaurant=restaurant,
            name=name,
            dimension_x=w,
            dimension_y=h
        )

        return JsonResponse({
            'id': new_map.id,
            'name': new_map.name,
            'w': new_map.dimension_x,
            'h': new_map.dimension_y,
            'tables': [],
            'bars': []
        })