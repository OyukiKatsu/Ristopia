from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from core.models import *
from django.views.generic import TemplateView, View
from django.http import JsonResponse
from core.models import TableOrder, Restaurante
from TFG import settings
from django.core.exceptions import SuspiciousOperation


# ====== Tables ====== #
from django.core import signing
from django.shortcuts import get_object_or_404, render
from core.models import Restaurante, Table

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
            raise SuspiciousOperation("The url decryption was not successful")

        restaurant = get_object_or_404(Restaurante, pk=rest_id)
        table      = get_object_or_404(Table, pk=table_id, map__restaurant=restaurant)
        context = {
            'table': table,
            'restaurant': restaurant
        }

        return render(request, self.template_name, context)



# ====== Orders ====== #
class PendingOrdersView(View):
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
class CompleteOrderView(View):
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
        
        orderState.state = 'Waiting to be delivered'
        orderState.save()
        
        return JsonResponse({'success': True})