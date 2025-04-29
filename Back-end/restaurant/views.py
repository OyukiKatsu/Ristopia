from django.shortcuts import render
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from core.models import Profile
from core.models import Restaurante
from core.models import Menu
from core.models import Category
from core.models import CategoryElement
# Create your views here.

@method_decorator(csrf_exempt, name='dispatch')
class CreateRestaurante(TemplateView):
    def post(self, request, *args, **kwargs):
        try:
            name = request.POST['name']
            owner_id = request.POST['owner_id']
            icon = request.FILES.get('icon')  # Optional

            try:
                owner = Profile.objects.get(id=owner_id)
            except Profile.DoesNotExist:
                return JsonResponse({'error': 'Owner not found'}, status=404)

            restaurante = Restaurante.objects.create(
                name=name,
                owner=owner,
                icon=icon  # Can be None
            )

            return JsonResponse({'message': 'Restaurante created successfully', 'restaurante_id': restaurante.id}, status=200)

        except KeyError as e:
            return JsonResponse({'error': f'Missing field: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
        
@method_decorator(csrf_exempt, name='dispatch')
class CreateMenu(TemplateView):
    def post(self, request, *args, **kwargs):
        try:
            restaurant_id = request.POST['restaurant_id']
            restaurant = Restaurante.objects.get(id=restaurant_id)
            menu = Menu.objects.create(restaurant=restaurant)
            return JsonResponse({'message': 'Menu created successfully', 'menu_id': menu.id}, status=200)
        except Restaurante.DoesNotExist:
            return JsonResponse({'error': 'Restaurant not found'}, status=404)
        except KeyError as e:
            return JsonResponse({'error': f'Missing field: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class CreateCategory(TemplateView):
    def post(self, request, *args, **kwargs):
        try:
            menu_id = request.POST['menu_id']
            name = request.POST['name']
            active = request.POST.get('active', 'true').lower() == 'true'

            menu = Menu.objects.get(id=menu_id)
            category = Category.objects.create(menu=menu, name=name, active=active)

            return JsonResponse({'message': 'Category created successfully', 'category_id': category.id}, status=200)
        except Menu.DoesNotExist:
            return JsonResponse({'error': 'Menu not found'}, status=404)
        except KeyError as e:
            return JsonResponse({'error': f'Missing field: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class CreateCategoryElement(TemplateView):
    def post(self, request, *args, **kwargs):
        try:
            category_id = request.POST['category_id']
            name = request.POST['name']
            description = request.POST['description']
            price = request.POST['price']
            cost = request.POST['cost']
            active = request.POST.get('active', 'true').lower() == 'true'

            category = Category.objects.get(id=category_id)
            element = CategoryElement.objects.create(
                category=category,
                name=name,
                description=description,
                price=price,
                cost=cost,
                active=active
            )

            return JsonResponse({'message': 'Category element created successfully', 'element_id': element.id}, status=200)
        except Category.DoesNotExist:
            return JsonResponse({'error': 'Category not found'}, status=404)
        except KeyError as e:
            return JsonResponse({'error': f'Missing field: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
