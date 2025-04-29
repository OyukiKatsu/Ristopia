from django.contrib import admin
from . import models
# Register your models here.


admin.site.register(models.Profile)
admin.site.register(models.Restaurante)
admin.site.register(models.Worker)
admin.site.register(models.Menu)
admin.site.register(models.Category)
admin.site.register(models.CategoryElement)