from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.urls import reverse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from core.utils import generate_table_qr
from core.models import CategoryElement, Profile, Worker, TableOrder, Restaurante, Category, Menu, Map, Table, Bar, TableCell, BarCell, Allergen
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
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
import json, io
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from core.utils import generate_table_qr


# ========================================================================== #
# ====== Dysplay Pages ====== #
# ========================================================================== #


# ====== User Control ====== #
class RegisterView(TemplateView):
    """
    RegisterView
    ------------
    Handles user registration: displays the form on GET and processes registration
    data on POST, including user/profile/restaurant creation and welcome email.
    """
    template_name = 'User/register.html'

    def get(self, request, *args, **kwargs):
        """
        Renders the registration page.
        """
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        """
        - Reads form fields: username, email, password1, password2, profile and restaurant files.
        - Validates required fields, password match, uniqueness.
        - Creates User, Profile and Restaurante objects on success.
        - Sends a welcome email.
        - Redirects to login on success or re‐renders with error messages.
        """
        # Extract form data
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        profile_pic = request.FILES.get('profile_picture')
        restaurant_name = request.POST.get('restaurant_name')
        restaurant_icon = request.FILES.get('restaurant_icon')

        # Validate mandatory fields
        if not all([username, email, password1, password2]):
            messages.error(request, 'Error|All fields are required.')
            return render(request, self.template_name)

        # Validate password match
        if password1 != password2:
            messages.error(request, 'Error|Passwords do not match.')
            return render(request, self.template_name)

        # Check username/email uniqueness
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Error|Username already taken.')
            return render(request, self.template_name)
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Error|Email is already registered.')
            return render(request, self.template_name)

        # Attempt creation
        try:
            user = User.objects.create_user(username=username, email=email, password=password1)
            profile = Profile.objects.create(user=user, email=email, profile_picture=profile_pic)
            restaurante = Restaurante.objects.create(
                name=restaurant_name,
                icon=restaurant_icon,
                owner=profile
            )

            # Success message and welcome email
            messages.success(request, 'Succes|User created successfully. Login to continue!')
            html_content = render_to_string(
                "core/emails/emailbase.html",
                {
                    "title": f"Welcome to Ristòpia, {username}",
                    "message": "Thank you for joining our platform! We're excited to have you."
                }
            )
            send_mail(
                "Welcome to Ristòpia", "", "ristopia123@gmail.com", [email],
                html_message=html_content
            )
        except Exception as e:
            # Handle any creation errors
            messages.error(request, f'Error|An error occurred: {str(e)}')
            return render(request, self.template_name)

        # Redirect to custom login on success
        return redirect('custom_login')
class LoginView(TemplateView):
    """
    LoginView
    ---------
    Handles both owner and worker logins. On GET, displays the login form;
    on POST, authenticates either by username/password (owner) or login code (worker).
    """
    template_name = 'User/login.html'

    def get(self, request):
        """
        Renders the login page.
        """
        return render(request, self.template_name)

    def post(self, request):
        """
        - Determines login_type ('owner' or 'worker').
        - For owners: authenticate via username/password.
        - For workers: lookup active Worker by login_code.
        - On success, logs in user and redirects to appropriate dashboard.
        - On failure, adds error message and re‐renders login form.
        """
        login_type = request.POST.get('login_type')

        if login_type == 'owner':
            # Owner login flow
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
            # Worker login flow
            login_code = request.POST.get('login_code')
            try:
                worker = Worker.objects.get(login_code=login_code, active=True)
                user = worker.user.user  # Profile → User
                login(request, user)
                # Redirect based on worker type
                if worker.type == 'Chef':
                    return redirect('chef_dashboard', chef_id=worker.id)
                elif worker.type == 'Waiter':
                    return redirect('waiter_dashboard', waiter_id=worker.id)
                else:
                    messages.error(request, "Error|Unknown worker type.")
            except Worker.DoesNotExist:
                messages.error(request, "Error|Invalid or inactive login code.")

        # On any error, re‐render login page
        return render(request, self.template_name)
class ResetPasswordView(TemplateView):
    """
    ResetPasswordView
    -----------------
    Displays the password reset request form (enter username).
    """
    template_name = 'User/reset-password.html'

    def get(self, request, *args, **kwargs):
        """
        Renders the password reset request page.
        """
        return render(request, self.template_name)
class ResetPasswordTokenView(TemplateView):
    """
    ResetPasswordTokenView
    ----------------------
    Validates and processes a password reset token link.
    """
    template_name = 'User/reset-password-confirm.html'

    def get(self, request, uidb64=None, token=None, *args, **kwargs):
        """
        - Decodes UID and verifies token.
        - If valid, renders form to enter new password.
        - Otherwise, shows invalid‐link message.
        """
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user and default_token_generator.check_token(user, token):
            return render(request, self.template_name, {
                'validlink': True,
                'uidb64': uidb64,
                'token': token
            })
        else:
            messages.error(request, 'The reset link is invalid or has expired.')
            return render(request, self.template_name, {'validlink': False})

    def post(self, request, uidb64=None, token=None, *args, **kwargs):
        """
        - Validates matching passwords.
        - Resets user password if token still valid.
        - Redirects to login on success; otherwise re‐renders.
        """
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # Ensure passwords match
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return redirect(request.path)

        # Decode UID
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            messages.error(request, 'Invalid user.')
            return redirect(request.path)

        # Final token check
        if user and default_token_generator.check_token(user, token):
            user.set_password(password1)
            user.save()
            messages.success(request, 'Password reset successfully. You can now log in.')
            return redirect('custom_login')
        else:
            messages.error(request, 'Invalid or expired link.')
            return redirect(request.path)

# ====== Owner Dashboards ====== #

class OwnerView(LoginRequiredMixin, TemplateView):
    """
    OwnerView
    ---------
    Displays the owner dashboard, showing today’s stats for orders, profit, cost, and top dish.
    """
    template_name = 'User/owner.html'

    def get(self, request, owner_id, *args, **kwargs):
        """
        - Ensures the logged‐in user matches the requested owner.
        - Renders the dashboard template with stats context.
        """
        # Authorization check
        try:
            owner_profile = Profile.objects.get(id=owner_id)
        except Profile.DoesNotExist:
            raise PermissionDenied("403 Forbidden: You don't have access to this owner's dashboard.")
        if request.user != owner_profile.user:
            raise PermissionDenied("403 Forbidden: You don't have access to this owner's dashboard.")

        context = self.get_context_data(**kwargs)
        return render(request, self.template_name, context)

    def get_context_data(self, **kwargs):
        """
        Build context dict including:
        - Today's profit & cost aggregated from orders.
        - Top ordered dish today.
        """
        context = super().get_context_data(**kwargs)
        owner_id = self.kwargs.get('owner_id')
        profile = Profile.objects.get(id=owner_id)

        # Compute today’s date and filter today's active orders
        today = datetime.now().date()
        orders_today = TableOrder.objects.filter(
            table__map__restaurant__owner=profile,
            date__date=today,
            active=True
        )

        # Aggregate profit and cost
        profit = orders_today.aggregate(total_profit=Sum('category_element__price'))['total_profit'] or 0
        cost = orders_today.aggregate(total_cost=Sum('category_element__cost'))['total_cost'] or 0

        # Determine the top dish
        top_dish = (
            orders_today
            .values('category_element__name')
            .annotate(count=Count('id'))
            .order_by('-count')
            .first()
        )

        # Populate stats
        context['stats'] = {
            'Today_Profit': round(profit, 2),
            'Today_Cost': round(cost, 2),
            'Top_Dish_Today': top_dish['category_element__name'] if top_dish else "N/A",
        }
        context['owner_id'] = owner_id
        return context


# === Menu ==== #
class MenuView(LoginRequiredMixin, TemplateView):
    """
    MenuView
    --------
    Shows the current menu for the owner's restaurant.
    """
    template_name = 'User/menu.html'

    def get_context_data(self, **kwargs):
        """
        Adds profile, restaurant and menu objects to context.
        """
        context = super().get_context_data(**kwargs)
        profile = self.request.user.get_User_Profile
        restaurant = profile.get_Profile_Restaurantes.first()
        menu = Menu.objects.filter(restaurant=restaurant).first()
        allergens = Allergen.objects.all()
        context.update({
            'profile': profile,
            'restaurant': restaurant,
            'menu': menu,
            'allergens': allergens
        })
        return context

    def get(self, request, owner_id, *args, **kwargs):
        """
        - Authorization check same as OwnerView.
        - Renders the menu page with context.
        """
        try:
            owner_profile = Profile.objects.get(id=owner_id)
        except Profile.DoesNotExist:
            raise PermissionDenied("403 Forbidden: You don't have access to this owner's dashboard.")
        if request.user != owner_profile.user:
            raise PermissionDenied("403 Forbidden: You don't have access to this owner's dashboard.")
        return render(request, self.template_name, self.get_context_data(**kwargs))

# === Worker ==== #
class WorkersView(LoginRequiredMixin, TemplateView):
    """
    WorkersView
    -----------
    Lists all workers for the owner’s restaurant.
    """
    template_name = 'User/workers.html'

    def get(self, request, owner_id, *args, **kwargs):
        """
        - Authorization check.
        - Fetches restaurant and its workers.
        - Renders workers listing.
        """
        try:
            owner_profile = Profile.objects.get(id=owner_id)
        except Profile.DoesNotExist:
            raise PermissionDenied("403 Forbidden: You don't have access to this owner's dashboard.")
        if request.user != owner_profile.user:
            raise PermissionDenied("403 Forbidden: You don't have access to this owner's dashboard.")

        restaurant = owner_profile.get_Profile_Restaurantes.first()
        workers = restaurant.get_Restaurante_Workers.all()
        context = {
            'restaurant': restaurant,
            'workers': workers,
            'profile': owner_profile,
        }
        return render(request, self.template_name, context)

# ====== Worker Dashboards ====== #
class WaiterView(LoginRequiredMixin, TemplateView):
    """
    Now purely returns an empty template; the Vue app will fetch all map/tables data via AJAX.
    """
    template_name = 'User/waiter.html'

    def get(self, request, waiter_id):
        user = request.user
        try:
            worker = Worker.objects.get(
                id=waiter_id,
                user__user=user,
                type='Waiter',
                active=True
            )
        except Worker.DoesNotExist:
            raise PermissionDenied("403 Forbidden: You don't have access to this waiter dashboard.")

        context = {
            'username': user.username,
            'role':     'Waiter',
            'restaurant': worker.restaurant
        }
        return render(request, self.template_name, context)
class ChefView(LoginRequiredMixin, TemplateView):
    """
    ChefView
    --------
    Displays a simple dashboard for chefs.
    """
    template_name = 'User/chef.html'

    def get(self, request, chef_id):
        """
        - Ensures the logged‐in user is the correct chef.
        - Renders the chef dashboard, including restaurant ID.
        """
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
class MapCreatorView(LoginRequiredMixin, TemplateView):
    """
    MapCreatorView
    --------------
    Provides the interface and payload for creating/editing restaurant floor maps.
    """
    template_name = 'User/map.html'

    def get(self, request, owner_id, *args, **kwargs):
        """
        - Authorization check.
        - Gathers all existing maps, tables, and bars into JSON payload.
        - Renders the map creation page.
        """
        try:
            owner_profile = Profile.objects.get(id=owner_id)
        except Profile.DoesNotExist:
            raise PermissionDenied("403 Forbidden: You don't have access to this owner's dashboard.")

        if request.user != owner_profile.user:
            raise PermissionDenied("403 Forbidden: You don't have access to this owner's dashboard.")

        restaurant = owner_profile.get_Profile_Restaurantes.first()
        all_maps = Map.objects.filter(restaurant=restaurant)

        # Build JSON payload with maps, tables, and bars
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
            'profile': owner_profile,
            'restaurant': restaurant,
            'maps_json': json.dumps(maps_payload, cls=DjangoJSONEncoder),
        }
        return render(request, self.template_name, context)
# ========================================================================== #
# ========== "APIs" =========== #
# ========================================================================== #

# ====== User Control ====== #
class ResetPasswordEmailView(View):
    """
    ResetPasswordEmailView
    ----------------------
    Accepts a username via POST, generates a password‐reset token and UID,
    builds the reset URL, and emails it to the user’s registered address.
    """
    def post(self, request, *args, **kwargs):
        """
        - Reads 'username' from form data.
        - If user exists:
            • Encodes UID and generates token.
            • Constructs absolute URL for password reset confirmation.
            • Renders email template and sends reset email.
        - Always returns HTTP 200 to prevent username enumeration.
        """
        username = request.POST.get('username')
        user = User.objects.filter(username=username).first()
        if user:
            # Encode the user's primary key into URL‐safe base64
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            # Generate a one‐time use token
            token = default_token_generator.make_token(user)
            # Build the full reset link
            reset_url = request.build_absolute_uri(
                reverse('custom_password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
            )
            # Render and send the email
            html_content = render_to_string("core/emails/email_password_reset.html", {
                "title": "Reset Your Password",
                "message": (
                    "Click the button below to reset your password. "
                    "If you didn’t request this, you can safely ignore this email."
                ),
                "reset_url": reset_url
            })
            send_mail(
                "Reset Your Password",
                "",  # plain‐text fallback
                "ristopia123@gmail.com",
                [user.get_User_Profile.email],
                html_message=html_content
            )
        return HttpResponse(status=200)

# ====== Owner Dashboards ====== #
class DashboardChartData(View):
    """
    DashboardChartData
    ------------------
    Returns JSON time‐series or top‐items data for owner dashboards.
    Supports ranges: 1d, 1w, 1m and chart types: 'profit', 'cost', 'most_ordered'.
    """
    def get(self, request, *args, **kwargs):
        """
        - Validates that the requesting user matches the owner_id.
        - Filters TableOrder by the specified time range.
        - If type is 'profit' or 'cost', aggregates sums per period.
        - If type is 'most_ordered', returns top 5 ordered items.
        - Returns JSON with 'labels' and 'data' arrays or error.
        """
        chart_type = request.GET.get('type')
        time_range = request.GET.get('range')
        owner_id   = request.GET.get('owner_id')

        # Permission check: user must own this profile
        if request.user.get_User_Profile.id != int(owner_id):
            return JsonResponse({'error': "Permission denied."}, status=403)

        profile = Profile.objects.get(id=owner_id)
        now_time = now()
        queryset = TableOrder.objects.filter(
            table__map__restaurant__owner=profile
        )

        # Determine time window and truncation
        if time_range == '1d':
            start = now_time.replace(hour=0, minute=0, second=0, microsecond=0)
            end   = start + timedelta(days=1)
            truncate     = TruncHour('date')
            label_format = "%H:%M"
        elif time_range == '1w':
            start = now_time - timedelta(days=now_time.weekday())
            end   = start + timedelta(days=7)
            truncate     = TruncDay('date')
            label_format = "%A"
        elif time_range == '1m':
            start = now_time.replace(day=1)
            end   = (start + timedelta(days=32)).replace(day=1)
            truncate     = TruncDate('date')
            label_format = "%d %b"
        else:
            return JsonResponse({'error': 'Invalid range'}, status=400)

        # Filter orders to the chosen date range
        queryset = queryset.filter(date__range=(start, end))

        data = {}
        # Profit or cost chart
        if chart_type in ['profit', 'cost']:
            # Select field based on chart_type
            values_field = (
                'category_element__price' if chart_type == 'profit'
                else 'category_element__cost'
            )
            grouped = (
                queryset
                .annotate(period=truncate)
                .values('period')
                .annotate(total=Sum(values_field))
                .order_by('period')
            )
            data['labels'] = [entry['period'].strftime(label_format) for entry in grouped]
            data['data']   = [float(entry['total']) for entry in grouped]

        # Most‐ordered items chart
        elif chart_type == 'most_ordered':
            grouped = (
                queryset
                .values('category_element__name')
                .annotate(count=Count('id'))
                .order_by('-count')[:5]
            )
            data['labels'] = [entry['category_element__name'] for entry in grouped]
            data['data']   = [entry['count'] for entry in grouped]

        else:
            return JsonResponse({'error': 'Invalid chart type'}, status=400)

        return JsonResponse(data)

# === Menu ==== #
class CreateMenuView(LoginRequiredMixin, View):
    """
    CreateMenuView
    --------------
    Creates an empty Menu for the authenticated owner’s restaurant if none exists.
    """
    def post(self, request, owner_id, *args, **kwargs):
        """
        - Validates request user against owner_id.
        - If no Menu exists for this restaurant, creates one.
        - Returns JSON status: 'success' or 'exists'.
        """
        # Permission check
        if request.user.get_User_Profile.id != int(owner_id):
            return JsonResponse({'error': "Permission denied."}, status=403)

        profile    = request.user.get_User_Profile
        restaurant = profile.get_Profile_Restaurantes.first()

        if not Menu.objects.filter(restaurant=restaurant).exists():
            Menu.objects.create(restaurant=restaurant)
            messages.success(request, 'Success|Menu created successfully.')
            return JsonResponse({'status': 'success'})

        return JsonResponse({'status': 'exists'})

# === Category ==== #
class CreateCategoryView(LoginRequiredMixin, View):
    """
    CreateCategoryView
    ------------------
    Adds a new Category to an existing Menu.
    """
    def post(self, request, owner_id, *args, **kwargs):
        """
        - Checks owner_id matches authenticated user.
        - Reads 'menu_id' and 'name' from POST.
        - Creates Category and returns its id and name.
        """
        if request.user.get_User_Profile.id != int(owner_id):
            return JsonResponse({'error': "Permission denied."}, status=403)

        menu_id = request.POST.get('menu_id')
        name    = request.POST.get('name')
        menu    = get_object_or_404(Menu, id=menu_id)

        category = Category.objects.create(menu=menu, name=name)
        messages.success(request, f'Success|Category "{name}" added.')

        return JsonResponse({
            'status': 'success',
            'category_id': category.id,
            'category_name': category.name
        })
class ToggleCategoryActiveView(LoginRequiredMixin, View):
    """
    ToggleCategoryActiveView
    ------------------------
    Flips the 'active' flag on a Category.
    """
    def post(self, request, owner_id, pk):
        """
        - Verifies owner ownership of the Category.
        - Toggles 'active' and returns new state.
        """
        category = get_object_or_404(
            Category,
            pk=pk,
            menu__restaurant__owner__id=owner_id
        )
        if request.user.get_User_Profile.id != int(owner_id):
            return JsonResponse({'error': "Permission denied."}, status=403)

        category.active = not category.active
        category.save()
        return JsonResponse({'status': 'success', 'active': category.active})
class UpdateCategoryView(LoginRequiredMixin, View):
    """
    UpdateCategoryView
    ------------------
    Renames a Category.
    """
    def post(self, request, owner_id, pk):
        """
        - Checks ownership.
        - Requires non‐empty 'name' in POST.
        - Saves and returns new name.
        """
        category = get_object_or_404(
            Category,
            pk=pk,
            menu__restaurant__owner__id=owner_id
        )
        if request.user.get_User_Profile.id != int(owner_id):
            return JsonResponse({'error': "Permission denied."}, status=403)

        new_name = request.POST.get('name')
        if not new_name:
            return JsonResponse({'error': "Name is required."}, status=400)

        category.name = new_name
        category.save()
        return JsonResponse({'status': 'success', 'name': category.name})
class DeleteCategoryView(LoginRequiredMixin, View):
    """
    DeleteCategoryView
    ------------------
    Deletes a Category permanently.
    """
    def post(self, request, owner_id, pk):
        """
        - Ownership check.
        - Deletes the Category and returns success.
        """
        category = get_object_or_404(
            Category,
            pk=pk,
            menu__restaurant__owner__id=owner_id
        )
        if request.user.get_User_Profile.id != int(owner_id):
            return JsonResponse({'error': "Permission denied."}, status=403)

        category.delete()
        return JsonResponse({'status': 'success'})
class CategoryElementsView(LoginRequiredMixin, View):
    """
    CategoryElementsView
    --------------------
    Returns JSON list of all elements in a given Category, including each element’s allergens.
    """
    def get(self, request, owner_id, category_id):
        """
        - No ownership check needed beyond login.
        - Serializes each element’s fields into JSON, plus allergens.
        """
        if request.user.get_User_Profile.id != int(owner_id):
            return JsonResponse({'error': "Permission denied."}, status=403)
        
        elements = CategoryElement.objects.filter(category_id=category_id)

        data = []
        for element in elements:
            el_allergens = []
            for allergen in element.allergens.all():
                el_allergens.append({
                    'id': allergen.id,
                    'name': allergen.name,
                    'icon_url': allergen.icon.url if allergen.icon else ''
                })

            data.append({
                'id': element.id,
                'name': element.name,
                'description': element.description,
                'recipe': element.recipe,
                'price': str(element.price),
                'cost': str(element.cost),
                'icon_url': element.icon.url if element.icon else '',
                'type': element.type,
                'active': element.active,
                'allergens': el_allergens,      
            })

        return JsonResponse({'elements': data})

# === Category Element ==== #
class CreateCategoryElementView(LoginRequiredMixin, View):
    """
    CreateCategoryElementView
    -------------------------
    Adds a new item (CategoryElement) under a Category (and assigns allergens).
    """
    def post(self, request, owner_id, *args, **kwargs):
        """
        - Verifies owner.
        - Reads fields + optional 'icon' file.
        - Creates element and returns its details.
        """
        if request.user.get_User_Profile.id != int(owner_id):
            return JsonResponse({'error': "Permission denied."}, status=403)

        category_id = request.POST.get('category_id')
        name        = request.POST.get('name')
        description = request.POST.get('description')
        recipe      = request.POST.get('recipe', '') 
        price       = request.POST.get('price')
        cost        = request.POST.get('cost')
        plate_type  = request.POST.get('type')
        icon_file   = request.FILES.get('icon')

        category = get_object_or_404(Category, id=category_id)

        # Build kwargs for CategoryElement
        element_kwargs = {
            'category': category,
            'name': name,
            'description': description,
            'recipe': recipe,
            'price': price,
            'cost': cost,
            'type': plate_type,
        }
        if icon_file:
            element_kwargs['icon'] = icon_file

        element = CategoryElement.objects.create(**element_kwargs)

        allergens_json = request.POST.get('allergens', '[]')
        try:
            allergen_ids = json.loads(allergens_json)
        except json.JSONDecodeError:
            allergen_ids = []

        valid_allergens = Allergen.objects.filter(id__in=allergen_ids)
        element.allergens.set(valid_allergens)

        messages.success(
            request,
            f'Success|Item "{name}" added to category "{category.name}".'
        )
        return JsonResponse({
            'status': 'success',
            'element_id': element.id,
            'element_name': element.name,
            'icon_url': element.icon.url if element.icon else '',
            'type': element.type,
            'recipe': element.recipe,
            'allergens': [
                {
                    'id': a.id,
                    'name': a.name,
                    'icon_url': a.icon.url if a.icon else ''
                } for a in valid_allergens
            ]
        })
class ToggleCategoryElementActiveView(LoginRequiredMixin, View):
    """
    ToggleCategoryElementActiveView
    -------------------------------
    Flips the 'active' flag on a CategoryElement.
    """
    def post(self, request, owner_id, *args, **kwargs):
        """
        - Reads 'element_id' from POST.
        - Confirms that element belongs to this owner.
        - Toggles and returns new state.
        """
        element_id = request.POST.get('element_id')
        element    = get_object_or_404(CategoryElement, id=element_id)
        # Ownership check via restaurant owner
        if element.category.menu.restaurant.owner.id != int(owner_id):
            return JsonResponse({'status':'error','msg':'Forbidden'}, status=403)

        element.active = not element.active
        element.save()
        return JsonResponse({
            'status': 'success',
            'element_id': element.id,
            'active': element.active
        })
class UpdateCategoryElementView(LoginRequiredMixin, View):
    """
    UpdateCategoryElementView
    -------------------------
    Updates fields on an existing CategoryElement, including optional icon and allergens.
    """
    def post(self, request, owner_id, *args, **kwargs):
        """
        - Reads 'element_id' and any updated fields from POST.
        - Ownership check.
        - Saves and returns full updated object in JSON.
        """
        element_id = request.POST.get('element_id')
        element    = get_object_or_404(CategoryElement, id=element_id)

        if element.category.menu.restaurant.owner.id != int(owner_id):
            return JsonResponse({'status':'error','msg':'Forbidden'}, status=403)

        element.name        = request.POST.get('name', element.name)
        element.description = request.POST.get('description', element.description)
        element.recipe      = request.POST.get('recipe', element.recipe)
        element.price       = request.POST.get('price', element.price)
        element.cost        = request.POST.get('cost', element.cost)
        element.type        = request.POST.get('type', element.type)

        if request.FILES.get('icon'):
            element.icon = request.FILES['icon']

        element.save()

        allergens_json = request.POST.get('allergens', '[]')
        try:
            allergen_ids = json.loads(allergens_json)
        except json.JSONDecodeError:
            allergen_ids = []

        valid_allergens = Allergen.objects.filter(id__in=allergen_ids)
        element.allergens.set(valid_allergens)

        return JsonResponse({
            'status': 'success',
            'element_id': element.id,
            'name': element.name,
            'description': element.description,
            'recipe': element.recipe,
            'price': str(element.price),
            'cost': str(element.cost),
            'icon_url': element.icon.url if element.icon else '',
            'type': element.type,
            'allergens': [
                {
                    'id': a.id,
                    'name': a.name,
                    'icon_url': a.icon.url if a.icon else ''
                } for a in valid_allergens
            ]
        })
class DeleteCategoryElementView(LoginRequiredMixin, View):
    """
    DeleteCategoryElementView
    -------------------------
    Deletes a CategoryElement from the database.
    """
    def post(self, request, owner_id, *args, **kwargs):
        """
        - Reads 'element_id' and confirms ownership.
        - Deletes the element and returns success JSON.
        """
        element_id = request.POST.get('element_id')
        element    = get_object_or_404(CategoryElement, id=element_id)
        if element.category.menu.restaurant.owner.id != int(owner_id):
            return JsonResponse({'status':'error','msg':'Forbidden'}, status=403)

        element.delete()
        return JsonResponse({'status': 'success', 'element_id': element_id})

# === Worker ==== #
class CreateWorkerView(LoginRequiredMixin, View):
    """
    CreateWorkerView
    ----------------
    Registers a new Worker account under an owner’s restaurant,
    generates a unique login code, and emails it to the worker.
    """
    def generate_unique_login_code(self):
        """
        Generates a 5‐character alphanumeric code that is unique across Workers.
        """
        characters = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(random.choices(characters, k=5))
            if not Worker.objects.filter(login_code=code).exists():
                return code

    def post(self, request, owner_id):
        """
        - Checks required fields: username, email, type.
        - Ensures unique username/email.
        - Creates User with unusable password and Profile.
        - Generates login code and Worker record.
        - Emails the code to the worker.
        - Returns full worker info in JSON.
        """
        if request.user.get_User_Profile.id != int(owner_id):
            return JsonResponse({'error': "Permission denied."}, status=403)

        profile    = get_object_or_404(Profile, id=owner_id)
        restaurant = profile.get_Profile_Restaurantes.first()
        username   = request.POST.get('username')
        email      = request.POST.get('email')
        worker_type= request.POST.get('type')
        picture    = request.FILES.get('picture')

        # Validate mandatory fields
        if not username or not email or not worker_type:
            return JsonResponse({'status': 'error', 'message': 'Missing required fields.'})
        if User.objects.filter(username=username).exists():
            return JsonResponse({'status': 'error', 'message': 'Username already exists.'})
        if Profile.objects.filter(email=email).exists():
            return JsonResponse({'status': 'error', 'message': 'Email already in use.'})

        try:
            # Create a user without a password
            user = User.objects.create(username=username)
            user.set_unusable_password()
            user.save()

            # Create worker profile
            worker_profile = Profile.objects.create(
                user=user,
                email=email,
                profile_picture=picture if picture else None
            )

            # Generate and assign unique login code
            login_code = self.generate_unique_login_code()
            worker = Worker.objects.create(
                restaurant=restaurant,
                user=worker_profile,
                login_code=login_code,
                type=worker_type,
                active=True
            )

            # Notify the worker by email
            html_content = render_to_string("core/emails/emailbase.html", {
                "title": f"You have been registered as a {worker_type} at {restaurant.name}.",
                "message": f"Your login code is: {login_code}"
            })
            send_mail(
                f"Registered at {restaurant.name}",
                "",
                "ristopia123@gmail.com",
                [email],
                html_message=html_content
            )

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
    """
    ToggleWorkerActiveView
    ----------------------
    Enables or disables a Worker account.
    """
    def post(self, request, worker_id, *args, **kwargs):
        """
        - Checks that the worker belongs to the request user’s restaurant.
        - Flips the 'active' flag on the Worker.
        - Returns a success message indicating new state.
        """
        worker = get_object_or_404(Worker, id=worker_id)
        if worker not in request.user.get_User_Profile.get_Profile_Restaurantes.first().get_Restaurante_Workers.all():
            return JsonResponse({'status':'error','msg':'Forbidden'}, status=403)

        worker.active = not worker.active
        worker.save()
        message = 'Worker disabled' if not worker.active else 'Worker enabled'
        return JsonResponse({'status':'success','message': message})
class DeleteWorkerView(LoginRequiredMixin, View):
    """
    DeleteWorkerView
    ----------------
    Removes a Worker account and its associated User/Profile entirely.
    """
    def post(self, request, worker_id, *args, **kwargs):
        """
        - Verifies ownership.
        - Deletes Worker, Profile, and User records.
        - Returns success JSON.
        """
        worker = get_object_or_404(Worker, id=worker_id)
        if worker not in request.user.get_User_Profile.get_Profile_Restaurantes.first().get_Restaurante_Workers.all():
            return JsonResponse({'status':'error','msg':'Forbidden'}, status=403)

        profile = worker.user
        user    = profile.user
        worker.delete()
        profile.delete()
        user.delete()
        return JsonResponse({'status':'success'})

# === Map Creator === #
class SaveMapView(LoginRequiredMixin, View):
    """
    Persists floors (Map), their Tables (+TableCells) and Bars (+BarCells)
    from a JSON payload.  Does an upsert on Map, then diffs each table/bar’s
    cells so we never blindly delete orders or other related data.
    """
    def post(self, request, owner_id):
        if request.user.get_User_Profile.id != int(owner_id):
            return JsonResponse({'error': "Permission denied."}, status=403)

        owner      = get_object_or_404(Profile, id=owner_id)
        restaurant = get_object_or_404(Restaurante, owner=owner)

        try:
            payload   = json.loads(request.body)
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

                if map_id:
                    map_obj = get_object_or_404(Map, pk=map_id, restaurant=restaurant)
                    map_obj.name        = name
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

                existing_tables = { t.id: t for t in map_obj.get_Map_Tables.all() }
                incoming_ids     = set()

                for tbl in tables:
                    tbl_id   = tbl.get('id')            
                    tbl_name = tbl['name']
                    cells    = tbl.get('cells', [])

                    if tbl_id and tbl_id in existing_tables:
                        tbl_obj = existing_tables[tbl_id]
                    else:
                        tbl_obj = Table.objects.create(
                            map=map_obj,
                            name=tbl_name
                        )

                    incoming_ids.add(tbl_obj.id)

                    existing_cells = set(
                        map(lambda c: (c.x, c.y), tbl_obj.cells.all())
                    )
                    new_cells = set((c['x'], c['y']) for c in cells)

                    to_delete = existing_cells - new_cells
                    if to_delete:
                        for (dx, dy) in to_delete:
                            TableCell.objects.filter(
                                table=tbl_obj, x=dx, y=dy
                            ).delete()

                    to_add = new_cells - existing_cells
                    if to_add:
                        TableCell.objects.bulk_create([
                            TableCell(table=tbl_obj, x=dx, y=dy)
                            for (dx, dy) in to_add
                        ])

                to_remove_table_ids = set(existing_tables.keys()) - incoming_ids
                if to_remove_table_ids:
                    Table.objects.filter(id__in=to_remove_table_ids).delete()

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

                    to_delete = existing_cells - new_cells
                    if to_delete:
                        for (dx, dy) in to_delete:
                            BarCell.objects.filter(
                                bar=bar_obj, x=dx, y=dy
                            ).delete()

                    to_add = new_cells - existing_cells
                    if to_add:
                        BarCell.objects.bulk_create([
                            BarCell(bar=bar_obj, x=dx, y=dy)
                            for (dx, dy) in to_add
                        ])

                to_remove_bar_ids = set(existing_bars.keys()) - incoming_bar_ids
                if to_remove_bar_ids:
                    Bar.objects.filter(id__in=to_remove_bar_ids).delete()

        return JsonResponse({'status': 'ok'})
class CreateFloorView(LoginRequiredMixin, View):
    """
    CreateFloorView
    ---------------
    Creates a new Map record (i.e. a floor) with given name and dimensions.
    """
    def post(self, request, owner_id):
        """
        - Validates owner.
        - Parses JSON with 'name', 'w', 'h'.
        - Returns the newly created Map as JSON.
        """
        if request.user.get_User_Profile.id != int(owner_id):
            return JsonResponse({'error': "Permission denied."}, status=403)

        data = json.loads(request.body)
        name = data.get('name')
        w    = data.get('w')
        h    = data.get('h')

        # Validate input
        if not (name and isinstance(w, int) and isinstance(h, int)):
            return JsonResponse({'error': 'Invalid data'}, status=400)

        restaurant = get_object_or_404(Restaurante, owner_id=owner_id)
        new_map    = Map.objects.create(
            restaurant=restaurant,
            name=name,
            dimension_x=w,
            dimension_y=h
        )

        # Return the new floor/map
        return JsonResponse({
            'id': new_map.id,
            'name': new_map.name,
            'w': new_map.dimension_x,
            'h': new_map.dimension_y,
            'tables': [],
            'bars': []
        })
class GenerateQR(LoginRequiredMixin, View):
    """
    GenerateQR
    ----------
    Generates a multi‐page PDF of QR codes for selected tables across all floors.
    """
    def post(self, request, owner_id):
        """
        - Verifies owner.
        - Reads JSON body with 'tables': [table_id,…].
        - Groups tables by Map, iterates floors:
            • Adds title page per floor.
            • Adds one QR page per selected table.
        - Streams back a PDF attachment named "table_qrs.pdf".
        """
        if request.user.get_User_Profile.id != int(owner_id):
            return JsonResponse({'error': "Permission denied."}, status=403)

        try:
            data      = json.loads(request.body)
            table_ids = data.get('tables', [])
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        if not table_ids:
            return JsonResponse({'error': 'No tables selected'}, status=400)

        restaurant = get_object_or_404(Restaurante, owner__id=owner_id)
        tables     = get_list_or_404(Table, id__in=table_ids, map__restaurant=restaurant)

        # Organize tables per map/floor
        tables_by_map = {}
        for tbl in tables:
            tables_by_map.setdefault(tbl.map_id, []).append(tbl)

        # Prepare PDF buffer
        buffer = io.BytesIO()
        p      = canvas.Canvas(buffer, pagesize=letter)
        W, H   = letter

        # Loop floors and tables
        for floor in Map.objects.filter(restaurant=restaurant).order_by('id'):
            floor_tables = tables_by_map.get(floor.id)
            if not floor_tables:
                continue  # skip floors with no selected tables

            # Title page
            p.setFont("Helvetica-Bold", 20)
            p.drawCentredString(W/2, H/2, floor.name)
            p.showPage()

            # QR pages
            for tbl in floor_tables:
                p.setFont("Helvetica-Bold", 16)
                p.drawCentredString(W/2, H - 100, tbl.name)

                _, content_file = generate_table_qr(tbl, request)
                png_bytes       = content_file.read()
                img_reader      = ImageReader(io.BytesIO(png_bytes))

                # Draw QR code image
                size = 200
                p.drawImage(
                    img_reader,
                    (W - size) / 2,
                    H - 100 - size - 20,
                    width=size,
                    height=size
                )
                p.showPage()

        # Finalize and send PDF
        p.save()
        buffer.seek(0)
        return HttpResponse(
            buffer,
            content_type='application/pdf',
            headers={'Content-Disposition': 'attachment; filename="table_qrs.pdf"'}
        )