from django.contrib import admin
from . import models
from .models import CategoryElement

# Register your models here.


admin.site.register(models.Profile)
admin.site.register(models.Restaurante)
admin.site.register(models.Worker)
admin.site.register(models.Menu)
admin.site.register(models.Category)
admin.site.register(models.Table)
admin.site.register(models.Map)
admin.site.register(models.Bar)
admin.site.register(models.TableOrder)
admin.site.register(models.OrderState)
admin.site.register(models.TableCell)
admin.site.register(models.BarCell)
admin.site.register(models.Allergen)

# To be able to multi select usen django admin for testing purposes.
@admin.register(CategoryElement)
class CategoryElementAdmin(admin.ModelAdmin):
    filter_horizontal = ('allergens',)