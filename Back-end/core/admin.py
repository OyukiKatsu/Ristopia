from django.contrib import admin
from . import models
# Register your models here.


admin.site.register(models.Profile)
admin.site.register(models.Restaurante)
admin.site.register(models.Worker)
admin.site.register(models.Menu)
admin.site.register(models.Category)
admin.site.register(models.CategoryElement)
admin.site.register(models.Table)
admin.site.register(models.Map)
admin.site.register(models.Bar)
admin.site.register(models.TableOrder)
admin.site.register(models.OrderState)