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
import random
import string

# ====== Dysplay Pages ====== #

# ====== Tables ====== #
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
        try:
            restaurant = Restaurante.objects.get(pk=rest_id)
            table      = Table.objects.get(pk=table_id, map__restaurant=restaurant)
        except:
            raise SuspiciousOperation("Invalid table link")

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


# ========== "APIs" =========== #

# ====== Tables ====== #
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
class TableCallWaiterView(View):
    def post(self, request, token, *args, **kwargs):
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

        table.calling_waiter = True
        table.save()

        return JsonResponse({'ok': True})
class TableIsOpenView(View):
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

        table = get_object_or_404(Table, pk=table_id, map__restaurant_id=rest_id)
        return JsonResponse({'open': table.open})

# ====== Menu ====== #
class CategoryElementsView(View):
    def get(self, request, restaurant_id, category_id, *args, **kwargs):
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
        element_list = list(qs)
        element_ids = [el['id'] for el in element_list]

        if not element_ids:
            return JsonResponse({'elements': []})

        through = CategoryElement.allergens.through
        rel_qs = through.objects.filter(
            categoryelement_id__in=element_ids
        ).values('categoryelement_id', 'allergen_id')

        element_to_allergen_ids = {}
        for row in rel_qs:
            elem_id = row['categoryelement_id']
            alg_id = row['allergen_id']
            element_to_allergen_ids.setdefault(elem_id, []).append(alg_id)

        all_allergen_ids = {row['allergen_id'] for row in rel_qs}
        allergen_qs = Allergen.objects.filter(
            id__in=all_allergen_ids
        ).values('id', 'name', 'icon')

        allergen_lookup = {}
        for alg in allergen_qs:
            icon_url = alg['icon'] and urljoin(settings.MEDIA_URL, alg['icon']) or None
            allergen_lookup[alg['id']] = {
                'name':     alg['name'],
                'icon_url': icon_url
            }

        elements = []
        for el in element_list:
            icon_path = el.get('icon')
            icon_url = icon_path and urljoin(settings.MEDIA_URL, icon_path) or None

            raw_ids = element_to_allergen_ids.get(el['id'], [])
            allergens = [
                allergen_lookup[a_id]
                for a_id in raw_ids
                if a_id in allergen_lookup
            ]

            elements.append({
                "id":          el["id"],
                "name":        el["name"],
                "description": el["description"],
                "price":       str(el["price"]),
                "icon_url":    icon_url,
                "allergens":   allergens,
            })

        return JsonResponse({'elements': elements})
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

# ====== Orders ====== #
class PendingCookingOrdersView(LoginRequiredMixin, View):
    def get(self, request, restaurant_id, *args, **kwargs):
        worker = request.user.get_User_Profile.get_Profile_Workers.first()
        restaurant = get_object_or_404(Restaurante, pk=restaurant_id)
        if worker.restaurant != restaurant or worker.active == False:
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
    
# ====== Chef ====== #
class MapsListView(LoginRequiredMixin, View):
    def get(self, request, restaurant_id, *args, **kwargs):
        worker = request.user.get_User_Profile.get_Profile_Workers.first()
        restaurant = get_object_or_404(Restaurante, pk=restaurant_id)
        if not (worker and worker.restaurant_id == restaurant.id and worker.active):
            return JsonResponse({"error": "Access denied."}, status=403)

        qs = Map.objects.filter(restaurant=restaurant).values("id", "name")
        return JsonResponse({"maps": list(qs)})


class TablesOnMapView(LoginRequiredMixin, View):
    def get(self, request, restaurant_id, map_id, *args, **kwargs):
        worker = request.user.get_User_Profile.get_Profile_Workers.first()
        restaurant = get_object_or_404(Restaurante, pk=restaurant_id)
        if not (worker and worker.type == "Chef" and worker.restaurant_id == restaurant.id and worker.active):
            return JsonResponse({"error": "Access denied."}, status=403)

        floor = get_object_or_404(Map, pk=map_id, restaurant=restaurant)

        qs = Table.objects.filter(map=floor, open=True).values("id", "name")
        return JsonResponse({"tables": list(qs)})


class TableOrdersViewChef(LoginRequiredMixin, View):
    def get(self, request, restaurant_id, table_id, *args, **kwargs):
        worker = request.user.get_User_Profile.get_Profile_Workers.first()
        restaurant = get_object_or_404(Restaurante, pk=restaurant_id)
        if not (worker and worker.type == "Chef" and worker.restaurant_id == restaurant.id and worker.active):
            return JsonResponse({"error": "Access denied."}, status=403)

        table = get_object_or_404(Table, pk=table_id, map__restaurant=restaurant)

        qs = (
            TableOrder.objects
            .filter(table=table, active=True)
            .select_related("category_element")
            .prefetch_related("get_TableOrder_OrderStates")
            .order_by("date")
        )

        orders_list = []
        for to in qs:
            elem = to.category_element
            state_obj = to.get_TableOrder_OrderStates.first()
            state_key = state_obj.state

            if state_key == "Waiting to be cooked":
                state_display = "In the kitchen..."
            elif state_key == "Waiting to be served":
                state_display = "Waiter is on its way..."
            elif state_key == "Waiting to be send to cook":
                state_display = "Marching..."
            elif state_key == "Delivered, Enjoy your meal!":
                state_display = "Delivered, Enjoy!"
            else:
                state_display = state_key

            image_url = elem.icon.url if elem.icon else ""

            orders_list.append({
                "order_id":     to.id,
                "element_name": elem.name,
                "recipe":       elem.recipe,
                "image_url":    image_url,
                "state_key":    state_key,
                "state_display": state_display,
                "ordered_at":   to.date.isoformat(),
            })
        return JsonResponse({"orders": orders_list})
    

class MapDetailView(LoginRequiredMixin, View):
    """
    Returns JSON for a single floor (Map), including:
      - id, name, w, h
      - tables: [ { id, name, open, calling_waiter, cells: [{x,y},...] }, … ]
      - bars:   [ { id, cells: [{x,y}, …] }, … ]
    Only a Waiter or Chef belonging to this restaurant may fetch it.
    """

    def get(self, request, restaurant_id, map_id, *args, **kwargs):
        # 1) Verify the logged‐in user is a valid Worker for this restaurant
        user_profile = request.user.get_User_Profile
        worker_qs = user_profile.get_Profile_Workers.filter(
            restaurant_id=restaurant_id,
            active=True,
            type__in=['Waiter', 'Chef']
        )

        if not worker_qs.exists():
            return JsonResponse({"error": "Access denied."}, status=403)

        # 2) Ensure the restaurant exists
        restaurant = get_object_or_404(Restaurante, pk=restaurant_id)

        # 3) Ensure this Map (floor) exists under that restaurant
        floor = get_object_or_404(Map, pk=map_id, restaurant=restaurant)

        # 4) Build the payload
        payload = {
            "id":   floor.id,
            "name": floor.name,
            "w":    floor.dimension_x,
            "h":    floor.dimension_y,
            "tables": [],
            "bars":   []
        }

        # 5) Gather all Tables on this floor, including their “open” and “calling_waiter” flags, plus their cells
        tbl_qs = Table.objects.filter(map=floor)
        # We include both open and closed tables, since we need to render table‐images appropriately.
        for tbl in tbl_qs:
            cells = list(
                tbl.cells.values('x', 'y')
            )
            payload["tables"].append({
                "id":               tbl.id,
                "name":             tbl.name,
                "open":             tbl.open,
                "calling_waiter":   tbl.calling_waiter,
                "cells":            cells
            })

        # 6) Gather Bars on this floor
        bar_qs = Bar.objects.filter(map=floor)
        for bar in bar_qs:
            cells = list(
                bar.cells.values('x', 'y')
            )
            payload["bars"].append({
                "id":    bar.id,
                "cells": cells
            })

        return JsonResponse(payload, status=200, safe=True)
    
class TableOrdersViewWaiter(LoginRequiredMixin, View):
    """
    GET /<restaurant_id>/maps/<map_id>/tables/<table_id>/orders_waiter/
    Returns JSON for all active orders on that table, including:
      - item name, price, date, icon_url, state_key, state_display
      - a running total if you need it (optional)
    Only active Waiter/Chef for the restaurant may fetch.
    """
    def get(self, request, restaurant_id, map_id, table_id, *args, **kwargs):
        user_profile = request.user.get_User_Profile
        worker_qs = user_profile.get_Profile_Workers.filter(
            restaurant_id=restaurant_id,
            active=True,
            type__in=['Waiter', 'Chef']
        )
        if not worker_qs.exists():
            return JsonResponse({"error": "Access denied."}, status=403)

        restaurant = get_object_or_404(Restaurante, pk=restaurant_id)

        floor = get_object_or_404(Map, pk=map_id, restaurant=restaurant)

        table = get_object_or_404(Table, pk=table_id, map=floor)

        qs = (
            TableOrder.objects
            .filter(table=table, active=True)
            .select_related("category_element")
            .prefetch_related("get_TableOrder_OrderStates")
            .order_by("date")
        )

        orders_list = []
        total_spent = 0.0

        for to in qs:
            elem = to.category_element
            price = float(elem.price)
            total_spent += price

            state_obj = to.get_TableOrder_OrderStates.first()
            state_key = state_obj.state if state_obj else ""
            if state_key == "Waiting to be cooked":
                state_display = "In the kitchen..."
            elif state_key == "Waiting to be served":
                state_display = "Waiter is on its way..."
            elif state_key == "Waiting to be send to cook":
                state_display = "Marching..."
            elif state_key == "Delivered, Enjoy your meal!":
                state_display = "Delivered, Enjoy!"
            else:
                state_display = state_key

            icon_url = ""
            if elem.icon:
                icon_url = urljoin(settings.MEDIA_URL, elem.icon.name)
            
            orders_list.append({
                "order_id":     to.id,
                "item_name":    elem.name,
                "price":        price,
                "date":         to.date.isoformat(),
                "icon_url":     icon_url,
                "state_key":    state_key,
                "type":         elem.type,
                "state_display": state_display,
            })

        return JsonResponse({
            "table_id":   table.id,
            "table_authCode":      table.authentication_code,
            "table_callWaiter":   table.calling_waiter,
            "table_name": table.name,
            "orders":     orders_list,
            "total":      round(total_spent, 2)
        }, status=200)

class ToDeliverOrdersView(LoginRequiredMixin, View):
    """
    Return JSON of every TableOrder whose latest state is "Waiting to be served".
    """
    def get(self, request, restaurant_id, *args, **kwargs):
        worker = request.user.get_User_Profile.get_Profile_Workers.first()
        restaurant = get_object_or_404(Restaurante, pk=restaurant_id)

        if worker.restaurant != restaurant or not worker.active:
            return JsonResponse({'error': 'Access denied.'}, status=403)

        to_deliver = []
        restaurant_table_orders = TableOrder.objects.filter(
            table__map__restaurant=restaurant,
            active=True
        ).order_by('date')

        for tableOrder in restaurant_table_orders:
            order_state = tableOrder.get_TableOrder_OrderStates.first()
            if order_state.state == 'Waiting to be served':
                image_url = tableOrder.category_element.icon.url if tableOrder.category_element.icon else None
                to_deliver.append({
                    'id':           tableOrder.id,
                    'table_name':   tableOrder.table.name,
                    'element_name': tableOrder.category_element.name,
                    'image_url':    image_url,
                    'ordered_at':   tableOrder.date.isoformat(),
                })

        return JsonResponse({'orders': to_deliver})
class DeliveredOrdersView(LoginRequiredMixin, View):
    """
    Mark a given TableOrder as delivered by creating a new OrderState.
    URL: /restaurant/<restaurant_id>/orders/<pk>/delivered
    """
    def post(self, request, restaurant_id, pk, *args, **kwargs):
        # 1) Verify worker belongs to this restaurant and is active
        worker = request.user.get_User_Profile.get_Profile_Workers.first()
        restaurant = get_object_or_404(Restaurante, pk=restaurant_id)
        if worker.restaurant != restaurant or not worker.active:
            return JsonResponse({'error': 'Access denied.'}, status=403)

        # 2) Retrieve the TableOrder (pk) and ensure it belongs to this restaurant
        table_order = get_object_or_404(TableOrder, pk=pk, table__map__restaurant=restaurant)

        # 3) Create a new OrderState with “Delivered, Enjoy your meal!”
        OrderState.objects.filter(
            table_order=table_order,
            state='Waiting to be served'
        ).update(state='Delivered, Enjoy your meal!')


        return JsonResponse({'success': True})
class UpdateComandaView(View):
    """
    POST /<restaurant_id>/orders/<table_id>/update_comanda/
    Payload: { "updates": [ { order_id, new_state }, … ], "deletes": [ order_id, … ] }
    """

    def post(self, request, restaurant_id, table_id, *args, **kwargs):
        user_profile = request.user.get_User_Profile
        worker_qs = user_profile.get_Profile_Workers.filter(
            restaurant_id=restaurant_id,
            active=True,
            type__in=['Waiter', 'Chef']
        )
        if not worker_qs.exists():
            return JsonResponse({"error": "Access denied."}, status=403)

        try:
            data = json.loads(request.body)
            updates = data.get('updates', [])
            deletes = data.get('deletes', [])
        except ValueError:
            return JsonResponse({"error": "Invalid JSON."}, status=400)

        for u in updates:
            oid = u.get('order_id')
            new_state = u.get('new_state')
            table_order = get_object_or_404(TableOrder, pk=oid)
            if table_order.table.id != int(table_id) or table_order.table.map.restaurant.id != int(restaurant_id):
                return JsonResponse({"error": f"Order {oid} does not belong here."}, status=400)

            valid = [s[0] for s in OrderState._meta.get_field("state").choices]
            if new_state not in valid:
                return JsonResponse({"error": f"Unrecognized state '{new_state}'."}, status=400)

            state_obj = table_order.get_TableOrder_OrderStates.first()
            if not state_obj:
                state_obj = OrderState(table_order=table_order)

            state_obj.state = new_state
            state_obj.save()

        for oid in deletes:
            table_order = get_object_or_404(TableOrder, pk=oid)
            if table_order.table.id != int(table_id) or table_order.table.map.restaurant.id != int(restaurant_id):
                return JsonResponse({"error": f"Order {oid} does not belong here."}, status=400)
            table_order.active = False
            table_order.save()
            table_order.get_TableOrder_OrderStates.all().delete()

        return JsonResponse({"ok": True})
class TableOpenView(View):
    def post(self, request, restaurant_id, table_id, *args, **kwargs):
        if request.user.get_User_Profile.get_Profile_Workers.first().restaurant_id != restaurant_id:
            return JsonResponse({"error": "Access denied."}, status=403)

        table = get_object_or_404(Table, id=table_id)
        new_code = "".join(random.choices(string.digits, k=5))
        table.authentication_code = new_code
        table.open = True
        table.save()

        return JsonResponse({
            "status": "success",
            "authentication_code": new_code
        }, status=200)

class TableCloseView(View):
    def post(self, request, restaurant_id, table_id, *args, **kwargs):
        if request.user.get_User_Profile.get_Profile_Workers.first().restaurant_id != restaurant_id:
            return JsonResponse({"error": "Access denied."}, status=403)

        table = get_object_or_404(Table, id=table_id)
        table.open = False
        table.calling_waiter = False
        table.save()
        TableOrder.objects.filter(table=table).update(active=False)
        return JsonResponse({"status": "success"}, status=200)
    
class TableAttendedView(View):
    def post(self, request, restaurant_id, table_id, *args, **kwargs):
        if request.user.get_User_Profile.get_Profile_Workers.first().restaurant_id != restaurant_id:
            return JsonResponse({"error": "Access denied."}, status=403)

        table = get_object_or_404(Table, id=table_id)
        table.calling_waiter = False
        table.save()

        return JsonResponse({"status": "success"}, status=200)


"""
        tableClosedImg:     "/media/core/Table.png",
        tableOpenGreenImg:  "/media/core/Table_Green.png",
        tableCallOrangeImg: "/media/core/Table_Orange.png",
        barImg:             "/media/core/Bar.png",
        stoolImg:           "/media/core/Stool.png",

"""