from django.db import models
from django.contrib.auth.models import User

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
    dimension_x = models.IntegerField()
    dimension_y = models.IntegerField()

    class Meta:
        db_table = 'Map'

# Table
class Table(models.Model):
    map = models.ForeignKey(Map, on_delete=models.CASCADE, related_name='get_Map_Tables')
    position_x = models.IntegerField()
    position_y = models.IntegerField()
    type = models.IntegerField(choices=[(2, 'Double'), (4, 'Familiar'), (6, 'Familiar Numerous'), (8, 'Meeting')])

    class Meta:
        db_table = 'Table'

# Bar
class Bar(models.Model):
    map = models.ForeignKey(Map, on_delete=models.CASCADE, related_name='get_Map_Bars')
    position_top_left_X = models.IntegerField()
    position_top_left_Y = models.IntegerField()
    position_bottom_right_X = models.IntegerField()
    position_bottom_right_Y = models.IntegerField()

    class Meta:
        db_table = 'Bar'

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
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    cost = models.DecimalField(max_digits=8, decimal_places=2)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = 'CategoryElement'

    def __str__(self):
        return self.name

# Worker
class Worker(models.Model):
    restaurant = models.ForeignKey(Restaurante, on_delete=models.CASCADE, related_name='get_Restaurante_Workers')
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='get_Profile_Workers')
    login_code = models.CharField(max_length=20)
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

# Order State
class OrderState(models.Model):
    table_order = models.ForeignKey(TableOrder, on_delete=models.CASCADE, related_name='get_TableOrder_OrderStates')
    state = models.CharField(max_length=50, choices=[
        ('Waiting confirmation', 'Waiting confirmation'),
        ('Waiting to be cooked', 'Waiting to be cooked'),
        ('Waiting to be delivered', 'Waiting to be delivered'),
    ])

    class Meta:
        db_table = 'OrderState'
