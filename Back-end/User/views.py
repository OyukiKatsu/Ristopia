from django.shortcuts import render, redirect, get_object_or_404
from core.models import CategoryElement, Profile, Worker, TableOrder, Restaurante, Category, Menu
from django.contrib.auth.models import User
from django.views.generic import TemplateView, View
from django.utils.timezone import now, timedelta
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Sum
from django.utils.timezone import now, timedelta
from calendar import day_name
from datetime import datetime, timedelta
from django.db.models.functions import TruncHour, TruncDay, TruncDate
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.template.loader import render_to_string


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


class WorkersView(TemplateView):
    template_name = 'User/workers.html'
    def get(self, request, owner_id, *args, **kwargs):
        try:
            owner_profile = Profile.objects.get(id=owner_id)
        except Profile.DoesNotExist:
            raise PermissionDenied("403 Forbidden: You don't have access to this owner's dashboard.")

        if request.user != owner_profile.user:
            raise PermissionDenied("403 Forbidden: You don't have access to this owner's dashboard.")
    
        return render(request, self.template_name)






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


























# ========== API CALLS ========== #
class DashboardChartData(View):
    def get(self, request, *args, **kwargs):
        chart_type = request.GET.get('type')
        time_range = request.GET.get('range')
        owner_id = request.GET.get('owner_id')

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















class CreateMenuView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        profile = request.user.get_User_Profile
        restaurant = profile.get_Profile_Restaurantes.first()
        if not Menu.objects.filter(restaurant=restaurant).exists():
            Menu.objects.create(restaurant=restaurant)
            messages.success(request, 'Success|Menu created successfully.')
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'exists'})


class CreateCategoryView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
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


class CreateCategoryElementView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        category_id = request.POST.get('category_id')
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        cost = request.POST.get('cost')
        icon = request.FILES.get('icon') 

        category = get_object_or_404(Category, id=category_id)

        element = CategoryElement.objects.create(
            category=category,
            name=name,
            description=description,
            price=price,
            cost=cost,
            icon=icon  
        )

        messages.success(request, f'Success|Item "{name}" added to category "{category.name}".')
        return JsonResponse({
            'status': 'success',
            'element_id': element.id,
            'element_name': element.name,
            'icon_url': element.icon.url if element.icon else ''
        })
    
class CategoryElementsView(LoginRequiredMixin, View):
    def get(self, request, owner_id, category_id):
        elements = CategoryElement.objects.filter(category_id=category_id, active=True)
        data = []
        for el in elements:
            data.append({
                'id': el.id,
                'name': el.name,
                'description': el.description,
                'price': str(el.price),
                'cost': str(el.cost),
                'icon_url': el.icon.url if el.icon else '',
            })
        return JsonResponse({'elements': data})