import json
from urllib.parse import urljoin
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from core.models import *
from django.views.generic import TemplateView, View
from django.http import JsonResponse
from core.models import TableOrder, Restaurante, Table, Category, CategoryElement
from TFG import settings
from django.core.exceptions import SuspiciousOperation
from django.core import signing
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone

class TableView(TemplateView):
    template_name = 'restaurant/table.html'

    def get(self, request, token, *args, **kwargs):
        try:
            data = signing.loads(
                token,
                key=settings.SECRET_KEY,
                salt='table-token',
                serializer=signing.JSONSerializer
            )
            rest_id  = data['restaurant_id']
            table_id = data['table_id']
        except signing.BadSignature:
            raise SuspiciousOperation("Invalid table link")

        restaurant = get_object_or_404(Restaurante, pk=rest_id)
        table      = get_object_or_404(Table, pk=table_id, map__restaurant=restaurant)
        menu = Menu.objects.filter(restaurant=restaurant).first()

        if menu:
            categories = list(
                menu.get_Menu_Categories
                    .filter(active=True)
                    .values('id', 'name')
            )
        else:
            categories = []

        return render(request, self.template_name, {
            'table':       table,
            'restaurant':  restaurant,
            'menu':        menu,
            'categories':  categories,
        })

# ====== Orders ====== #
class PendingOrdersView(LoginRequiredMixin, View):
    def get(self, request, restaurant_id, *args, **kwargs):
        worker = request.user.get_User_Profile.get_Profile_Workers.first()
        restaurant = get_object_or_404(Restaurante, pk=restaurant_id)
        if worker.type != 'Chef' or worker.restaurant != restaurant or worker.active == False:
            return JsonResponse({'error': 'Access denied.'}, status=403)
        
        pendingOrders = []
        restaurant_table_orders = TableOrder.objects.filter(table__map__restaurant=restaurant, active=True).order_by('date')

        
        for tableOrder in restaurant_table_orders:
            order_state = tableOrder.get_TableOrder_OrderStates.first()
            if order_state.state == 'Waiting to be cooked':
                image_url = tableOrder.category_element.icon.url
                pendingOrders.append({
                    'id': tableOrder.id,
                    'table_name': tableOrder.table.name,
                    'element_name': tableOrder.category_element.name,
                    'image_url': image_url,
                    'ordered_at': tableOrder.date.isoformat(),
                })
        return JsonResponse({'orders': pendingOrders})
class CompleteOrderView(LoginRequiredMixin, View):
    def post(self, request, restaurant_id, pk, *args, **kwargs):
        worker = request.user.get_User_Profile.get_Profile_Workers.first()
        restaurant = get_object_or_404(Restaurante, pk=restaurant_id)
        if worker.type != 'Chef' or worker.restaurant != restaurant or worker.active == False:
            return JsonResponse({'error': 'Access denied.'}, status=403)        
        try:
            tableOrder = TableOrder.objects.get(pk=pk, active=True)
        except TableOrder.DoesNotExist:
            return JsonResponse({'error': 'Order not found.'}, status=404)
        
        orderState = tableOrder.get_TableOrder_OrderStates.first()
        if orderState.state != 'Waiting to be cooked':
            return JsonResponse({'error': 'Order not in "Waiting to be cooked".'}, status=400)
        
        orderState.state = 'Waiting to be served'
        orderState.save()
        
        return JsonResponse({'success': True})
    



class AuthCodeView(View):
    """
    POST /restaurant/table/<token>/authenticate/
    Body JSON: { "code": "<5-char code>" }
    """
    def post(self, request, token, *args, **kwargs):
        import json
        try:
            data = json.loads(request.body)
            code = data.get('code','').strip()
        except:
            return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

        try:
            payload = signing.loads(
                token,
                key=settings.SECRET_KEY,
                salt='table-token',
                serializer=signing.JSONSerializer
            )
            rest_id  = payload['restaurant_id']
            table_id = payload['table_id']
        except signing.BadSignature:
            return JsonResponse({'ok': False, 'error': 'Bad token'}, status=400)

        table = get_object_or_404(Table, pk=table_id, map__restaurant_id=rest_id)
        if table.authentication_code != code:
            return JsonResponse({'ok': False, 'error': 'The submitted code is incorrect'}, status=400)

        return JsonResponse({
            'ok':         True,
            'table_name': table.name,
            'code':       code
        })



class OrderView(View):
    def post(self, request, token, *args, **kwargs):
        try:
            data = json.loads(request.body)
            items = data.get('items', [])
            if not isinstance(items, list):
                raise ValueError()
        except Exception:
            return JsonResponse({'ok': False, 'error': 'Invalid JSON or missing items'}, status=400)

        try:
            payload = signing.loads(
                token,
                key=settings.SECRET_KEY,
                salt='table-token',
                serializer=signing.JSONSerializer
            )
            rest_id  = payload['restaurant_id']
            table_id = payload['table_id']
        except signing.BadSignature:
            return JsonResponse({'ok': False, 'error': 'Bad token'}, status=400)

        table = get_object_or_404(Table, pk=table_id, map__restaurant_id=rest_id)

        now = timezone.now()
        created_any = False

        for entry in items:
            element_id = entry.get('element_id')
            qty        = entry.get('quantity')

            if not isinstance(element_id, int) or not isinstance(qty, int) or qty < 1:
                continue

            try:
                cat_el = CategoryElement.objects.get(
                    pk=element_id,
                    active=True,
                    category__menu__restaurant_id=rest_id
                )
            except CategoryElement.DoesNotExist:
                continue

            if cat_el.type == 'Drink':
                initial_state = 'Waiting to be served'
            elif cat_el.type in ['To share', 'First plate']:
                initial_state = 'Waiting to be cooked'
            elif cat_el.type in ['Second plate', 'Dessert']:
                initial_state = 'Waiting to be send to cook'


            for _ in range(qty):
                to = TableOrder.objects.create(
                    table=table,
                    category_element=cat_el,
                    date=now,
                    active=True
                )
                OrderState.objects.create(
                    table_order=to,
                    state=initial_state
                )
                created_any = True

        if not created_any:
            return JsonResponse({'ok': False, 'error': 'No valid items to order.'}, status=400)

        return JsonResponse({'ok': True})

class CategoriesView(View):
    """
    GET /api/restaurants/<restaurant_id>/menu/categories/
    Returns JSON { categories: [{id, name}, …] }
    """
    def get(self, request, restaurant_id, *args, **kwargs):
        qs = Category.objects.filter(
            menu__restaurant_id=restaurant_id,
            active=True
        ).values('id', 'name')

        return JsonResponse({'categories': list(qs)})


class TableOrdersView(View):
    def get(self, request, token, *args, **kwargs):
        try:
            payload = signing.loads(
                token,
                key=settings.SECRET_KEY,
                salt='table-token',
                serializer=signing.JSONSerializer
            )
            rest_id  = payload['restaurant_id']
            table_id = payload['table_id']
        except signing.BadSignature:
            return JsonResponse({'error': 'Invalid token'}, status=400)

        table = get_object_or_404(Table, pk=table_id, map__restaurant_id=rest_id)

        qs = (
            TableOrder.objects
            .filter(table=table, active=True)
            .select_related('category_element')
            .prefetch_related('get_TableOrder_OrderStates')
            .order_by('date')
        )

        orders_list = []
        for to in qs:
            elem = to.category_element
            icon_url = elem.icon.url if elem.icon else ''
            state_obj = to.get_TableOrder_OrderStates.first()
            state_key = state_obj.state
            if state_key == 'Waiting to be cooked':
                state_display = 'In the kitchen...'
            elif state_key == 'Waiting to be served':
                state_display = 'Waiter is on its way...'
            elif state_key == 'Waiting to be send to cook':
                state_display = 'Marching...'
            elif state_key == 'Delivered, Enjoy your meal!':
                state_display = 'Delivered, Enjoy!'
            else:
                state_display = state_key

            orders_list.append({
                'order_id':     to.id,
                'item_name':    elem.name,
                'price':        str(elem.price),
                'state_key':    state_key,
                'state_display': state_display,
                'icon_url':     icon_url,
            })

        return JsonResponse({'orders': orders_list})

class CategoryElementsView(View):
    """
    GET /api/restaurants/<restaurant_id>/menu/categories/<category_id>/elements/
    Returns JSON { elements: [{id, name, description, price, icon_url}, …] }
    """
    def get(self, request, restaurant_id, category_id, *args, **kwargs):
        # ensure category is active and belongs to that restaurant
        get_object_or_404(
            Category,
            pk=category_id,
            menu__restaurant_id=restaurant_id,
            active=True
        )

        qs = CategoryElement.objects.filter(
            category_id=category_id,
            active=True
        ).values('id', 'name', 'description', 'price', 'icon')

        elements = []
        for el in qs:
            icon_path = el.get('icon')
            icon_url = icon_path and urljoin(settings.MEDIA_URL, icon_path)
            elements.append({
                'id': el['id'],
                'name': el['name'],
                'description': el['description'],
                'price': str(el['price']),
                'icon_url': icon_url,
            })

        return JsonResponse({'elements': elements})