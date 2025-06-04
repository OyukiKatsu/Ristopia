from django.db import models
from django.contrib.auth.models import User
import os
from django.utils.text import slugify

# Profile
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='get_User_Profile')
    email = models.EmailField(unique=True, verbose_name='Email Address', db_column='email')
    profile_picture = models.ImageField(upload_to='profile/', verbose_name='Profile Picture', db_column='profile_image', blank=True, null=True, default='core/perfil_predeterminado.jpg')


    class Meta:
        db_table = 'Profile'
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'

    def __str__(self):
        return self.user.username   

# Restaurant
class Restaurante(models.Model):
    name = models.CharField(max_length=100)
    icon = models.ImageField(upload_to='restaurant_icons/', null=True, blank=True)
    owner = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='get_Profile_Restaurantes')

    class Meta:
        db_table = 'Restaurante'

    def __str__(self):
        return self.name

# Map
class Map(models.Model):
    restaurant = models.ForeignKey(Restaurante, on_delete=models.CASCADE, related_name='get_Restaurante_Maps')
    name = models.CharField(max_length=100)
    dimension_x = models.IntegerField()
    dimension_y = models.IntegerField()

    class Meta:
        db_table = 'Map'

    def __str__(self):
        return f"{self.name} - {self.restaurant.name}"

# Table
class Table(models.Model):
    map = models.ForeignKey(Map, on_delete=models.CASCADE, related_name='get_Map_Tables')
    name = models.CharField(max_length=100)
    open = models.BooleanField(default=False)
    authentication_code = models.CharField(max_length=5)
    calling_waiter = models.BooleanField(default=False)

    class Meta:
        db_table = 'Table'

    def __str__(self):
        return f"{self.name} - {self.map.name} - {self.map.restaurant.name}"

class TableCell(models.Model):
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='cells')
    x = models.IntegerField()
    y = models.IntegerField()

    class Meta:
        unique_together = ('x', 'y', 'table')
        db_table = 'TableCell'
    
    def __str__(self):
        return f"Cell for table - {self.table.name} - {self.x}, {self.y}"
    
# Bar
class Bar(models.Model):
    map = models.ForeignKey(Map, on_delete=models.CASCADE, related_name='get_Map_Bars')

    class Meta:
        db_table = 'Bar'
    
    def __str__(self):
        return f"Bar for - {self.map.restaurant.name}"

class BarCell(models.Model):    
    bar = models.ForeignKey(Bar, on_delete=models.CASCADE, related_name='cells')
    x = models.IntegerField()
    y = models.IntegerField()

    class Meta:
        unique_together = ('x', 'y', 'bar')
        db_table = 'BarCell'
    
    def __str__(self):
        return f"Cell for bar - {self.bar.map.restaurant.name} - {self.x}, {self.y}"
    
# Menu
class Menu(models.Model):
    restaurant = models.ForeignKey(Restaurante, on_delete=models.CASCADE, related_name='get_Restaurante_Menus')

    class Meta:
        db_table = 'Menu'
    
    def __str__(self):
        return f"Menu for - {self.restaurant.name}"

# Category
class Category(models.Model):
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name='get_Menu_Categories')
    name = models.CharField(max_length=100)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = 'Category'

    def __str__(self):
        return self.name

# Category Element
class CategoryElement(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='get_Category_Elements')
    icon = models.ImageField(upload_to='category_element_icons/', null=True, blank=True, default="core/elemento_predeterminado.jpg")
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    cost = models.DecimalField(max_digits=8, decimal_places=2)
    type = models.CharField(max_length=20, choices=[('To share', 'To share'),('First plate', 'First plate'), ('Second plate', 'Second plate'), ('Dessert', 'Dessert'), ('Drink', 'Drink')])
    allergens = models.ManyToManyField('Allergen', blank=True, related_name='get_Allergen_Category_Elements')
    recipe = models.TextField()
    active = models.BooleanField(default=True)


    class Meta:
        db_table = 'CategoryElement'

    def __str__(self):
        return self.name

# Worker
class Worker(models.Model):
    restaurant = models.ForeignKey(Restaurante, on_delete=models.CASCADE, related_name='get_Restaurante_Workers')
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='get_Profile_Workers')
    login_code = models.CharField(max_length=20, unique=True)
    type = models.CharField(max_length=20, choices=[('Waiter', 'Waiter'), ('Chef', 'Chef')])
    active = models.BooleanField(default=True)

    class Meta:
        db_table = 'Worker'

    def __str__(self):
        return self.user.user.username

# Table Order
class TableOrder(models.Model):
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='get_Table_Orders')
    category_element = models.ForeignKey(CategoryElement, on_delete=models.CASCADE, related_name='get_CategoryElement_Orders')
    date = models.DateTimeField()
    active = models.BooleanField(default=True)

    class Meta:
        db_table = 'TableOrder'

    def __str__(self):
        return "Ordered " + self.category_element.name + " for - " + self.table.name

# Order State
class OrderState(models.Model):
    table_order = models.ForeignKey(TableOrder, on_delete=models.CASCADE, related_name='get_TableOrder_OrderStates')
    state = models.CharField(max_length=50, choices=[
        ('Waiting to be cooked', 'In the kitchen...'),
        ('Waiting to be served', 'Waiter is on its way...'),
        ('Waiting to be send to cook', 'Awaiting confirmation...'),
        ('Delivered, Enjoy your meal!', 'Delivered, Enjoy!')
    ])

    class Meta:
        db_table = 'OrderState'

    def __str__(self):
        return f"{self.table_order.category_element.name} - {self.state} - {self.table_order.table.name}"

class Allergen(models.Model):
    name = models.CharField(max_length=100, unique=True)
    icon = models.ImageField(upload_to='allergen_icons/', null=True, blank=True)

    class Meta:
        db_table = 'Allergen'
        verbose_name = 'Allergen'
        verbose_name_plural = 'Allergens'

    def __str__(self):
        return self.name