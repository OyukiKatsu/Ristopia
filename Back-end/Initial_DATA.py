#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
To seed your DB, just do:
    $ python Initial_DATA.py
"""

import os
import sys
import subprocess

# If we're running outside manage.py shell, re-spawn inside it:
if __name__ == '__main__' and 'DJANGO_SETTINGS_MODULE' not in os.environ:
    subprocess.run([
        sys.executable, 'manage.py', 'shell', '-c',
        "exec(open('Initial_DATA.py', encoding='utf-8').read()); exit()"
    ])
    sys.exit(0)

# ————————————————————————————————
# Now inside manage.py shell
# ————————————————————————————————

import random
import django
from datetime import datetime
from django.conf import settings
from django.core.files import File
from django.contrib.auth.models import User
from django.core.management import call_command
from django.db import transaction

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TFG.settings')
django.setup()

from core.models import (
    Allergen, Profile, Restaurante, Worker,
    Menu, Category, CategoryElement,
    Map, Table, TableCell, Bar, BarCell,
    TableOrder, OrderState
)

# ————————————— OPEN LOG FILE —————————————
log_path = os.path.join(os.getcwd(), 'data.txt')
log_file = open(log_path, 'w', encoding='utf-8')
def log(msg: str):
    print(msg)
    log_file.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} | {msg}\n")

# (1) Migrations
log(">>> makemigrations…")
try:
    call_command('makemigrations', 'core', interactive=False, verbosity=0)
    log("    • OK")
except Exception as e:
    log(f"    • Error: {e!r}")
log(">>> migrate…")
call_command('migrate', interactive=False, verbosity=0)
log("    • OK\n")

# (2) Flush in correct order
log(">>> Clearing existing data…")
with transaction.atomic():
    OrderState.objects.all().delete()
    TableOrder.objects.all().delete()
    TableCell.objects.all().delete()
    BarCell.objects.all().delete()
    Table.objects.all().delete()
    Bar.objects.all().delete()
    Map.objects.all().delete()
    CategoryElement.objects.all().delete()
    Category.objects.all().delete()
    Menu.objects.all().delete()
    Worker.objects.all().delete()
    Restaurante.objects.all().delete()
    Profile.objects.all().delete()
    User.objects.filter(is_superuser=False).delete()
    Allergen.objects.all().delete()
log("    • Cleared\n")

# Icon folders
ALLERGEN_ICON_DIR    = os.path.join(settings.MEDIA_ROOT, 'core/forInitialData/allergen_icons')
OWNER_ICON_DIR       = os.path.join(settings.MEDIA_ROOT, 'core/forInitialData/owner_icon')
WORKERS_ICON_DIR     = os.path.join(settings.MEDIA_ROOT, 'core/forInitialData/workers_icons')
RESTAURANT_ICON_DIR  = os.path.join(settings.MEDIA_ROOT, 'core/forInitialData/restaurant_icons')
ELEMENTS_ICON_DIR    = os.path.join(settings.MEDIA_ROOT, 'core/forInitialData/elements_icons')

# A. Allergens
log("=== Seeding Allergens ===")
for name in [
    "Gluten","Crustaceans","Egg","Fish","Peanuts",
    "Soybeans","Milk","Treenuts","Celery",
    "Mustard","Sesame","Lupin","Molluscs",
]:
    alg, created = Allergen.objects.get_or_create(name=name)
    p = os.path.join(ALLERGEN_ICON_DIR, f"{name}.png")
    if os.path.exists(p):
        with open(p,'rb') as f:
            alg.icon.save(f"{name}.png", File(f), save=True)
        log(f"  • Icon for {name}")
    log(f"  • {'Created' if created else 'Exists'} {name}")
log(f"=== {Allergen.objects.count()} Allergens ===\n")

# B. Owner
log("=== Seeding Owner ===")
owner_u, cu = User.objects.get_or_create(
    username='Oyuki_Katsu', defaults={'email':'gjaraizm@gmail.com'}
)
if cu:
    owner_u.set_password('testing1234'); owner_u.save()
    log("  • Created User Oyuki_Katsu / testing1234")
else:
    log("  • User existed")
owner_p, cp = Profile.objects.get_or_create(
    user=owner_u, defaults={'email':owner_u.email}
)
if cp:
    # pick any owner icon (or skip if none)
    imgs = [f for f in os.listdir(OWNER_ICON_DIR) if f.lower().endswith('.png')]
    if imgs:
        pick = random.choice(imgs)
        with open(os.path.join(OWNER_ICON_DIR,pick),'rb') as f:
            owner_p.profile_picture.save(pick, File(f), save=True)
        log(f"  • Owner icon: {pick}")
    owner_p.save()
    log("  • Profile created")
else:
    log("  • Profile existed")
log("")

# C. Restaurant
log("=== Seeding Restaurant ===")
rest, cr = Restaurante.objects.get_or_create(
    name="ASADOR MONTEQUINTO", defaults={'owner':owner_p}
)
if cr:
    # use your Asador_Montequinto.png
    rest_icon = os.path.join(RESTAURANT_ICON_DIR, 'Asador_Montequinto.png')
    if os.path.exists(rest_icon):
        with open(rest_icon,'rb') as f:
            rest.icon.save('Asador_Montequinto.png', File(f), save=True)
        log("  • Restaurant icon set")
    rest.save()
    log("  • Restaurant created")
else:
    log("  • Restaurant existed")
log("")

# D. Workers (first gets first file, second gets second)
log("=== Seeding Workers ===")
worker_files = sorted([
    f for f in os.listdir(WORKERS_ICON_DIR)
    if f.lower().endswith('.png')
])
for idx, (uname,email,code,role) in enumerate([
    ('CHEF_TEST','xgjarmor597@ieshnosmachado.org','12345','Chef'),
    ('WAITER_TEST','pwpvivaecyp@gmail.com','54321','Waiter'),
]):
    u, cu2 = User.objects.get_or_create(username=uname, defaults={'email':email})
    if cu2:
        u.set_password('default1234'); u.save()
        log(f"  • Created user {uname}/default1234")
    else:
        log(f"  • User {uname} existed")
    p, cp2 = Profile.objects.get_or_create(user=u, defaults={'email':u.email})
    if cp2:
        # assign icon deterministically
        if idx < len(worker_files):
            wf = worker_files[idx]
            with open(os.path.join(WORKERS_ICON_DIR,wf),'rb') as f:
                p.profile_picture.save(wf, File(f), save=True)
            log(f"    • Worker icon: {wf}")
        p.save()
        log(f"    • Profile for {uname} created")
    else:
        log(f"    • Profile for {uname} existed")
    w, cw = Worker.objects.get_or_create(
        user=p, restaurant=rest,
        defaults={'login_code':code,'type':role,'active':True}
    )
    log(f"    • {'Created' if cw else 'Exists'} Worker {uname} ({role}) code={code}")
log("")

# — PART E: MENU, CATEGORIES, ELEMENTS & ALLERGEN MAPPING —
log("=== Seeding Menu / Categories / Elements ===")
menu, cm = Menu.objects.get_or_create(restaurant=rest)
if cm: log(f"  • Menu for {rest.name}")

# Define categories & elements, including `allergens` list
categories_data = [
    {
        'name': 'Drinks',
        'elements': [
            {'name': 'Coca-Cola',        'desc': '330 ml can',                 'price': '2.00',  'cost': '0.50',  'type': 'Drink',       'recipe': 'Serve ice-cold',                      'allergens': []},
            {'name': 'Orange Juice',     'desc': 'Fresh-squeezed 300 ml',      'price': '3.00',  'cost': '0.80',  'type': 'Drink',       'recipe': 'Shake and serve',                    'allergens': []},
            {'name': 'Peanut Smoothie',  'desc': 'Rich & creamy 350 ml',       'price': '4.50',  'cost': '1.20',  'type': 'Drink',       'recipe': 'Blend peanuts & banana',             'allergens': ['Peanuts', 'Milk']},
            {'name': 'Mango Lassi',      'desc': 'Yogurt drink 300 ml',        'price': '4.00',  'cost': '1.00',  'type': 'Drink',       'recipe': 'Blend mango & yogurt',              'allergens': ['Milk']},
            {'name': 'Sparkling Water',  'desc': '500 ml bottle',             'price': '1.80',  'cost': '0.20',  'type': 'Drink',       'recipe': 'Serve chilled',                     'allergens': []},
        ]
    },
    {
        'name': 'Starters',
        'elements': [
            {'name': 'Patatas Bravas',      'desc': 'Spicy potatoes',               'price': '5.00',  'cost': '1.50', 'type': 'To share',     'recipe': 'Fry & top with sauce',            'allergens': ['Celery']},
            {'name': 'Gazpacho Andaluz',    'desc': 'Cold tomato soup',            'price': '4.50',  'cost': '1.20', 'type': 'First plate',   'recipe': 'Blend veg & chill',               'allergens': ['Celery']},
            {'name': 'Shrimp Cocktail',     'desc': 'Chilled shrimp',              'price': '7.00',  'cost': '2.50', 'type': 'First plate',   'recipe': 'Serve with sauce',                 'allergens': ['Crustaceans']},
            {'name': 'Cheese Platter',      'desc': 'Assorted cheeses',            'price': '8.50',  'cost': '3.00', 'type': 'To share',     'recipe': 'Arrange & garnish',                'allergens': ['Milk']},
            {'name': 'Olive Tapenade',      'desc': 'Olives & herbs spread',       'price': '5.50',  'cost': '1.80', 'type': 'To share',     'recipe': 'Blend & serve with bread',         'allergens': ['Sulphites']},
        ]
    },
    {
        'name': 'Soups & Salads',
        'elements': [
            {'name': 'Minestrone Soup',       'desc': 'Hearty veg soup',             'price': '6.00',  'cost': '1.80', 'type': 'First plate',  'recipe': 'Simmer veg & beans',             'allergens': ['Celery']},
            {'name': 'Chicken Caesar Salad',  'desc': 'Romaine, chicken, dressing', 'price': '7.50',  'cost': '2.50', 'type': 'First plate',  'recipe': 'Toss ingredients',                'allergens': ['Egg', 'Fish', 'Milk']},
            {'name': 'Greek Salad',           'desc': 'Tomato, cucumber, feta',      'price': '6.50',  'cost': '2.00', 'type': 'First plate',  'recipe': 'Mix & drizzle olive oil',         'allergens': ['Milk']},
            {'name': 'Lentil Soup',           'desc': 'Spiced lentil broth',        'price': '5.50',  'cost': '1.50', 'type': 'First plate',  'recipe': 'Simmer lentils & spices',         'allergens': []},
            {'name': 'Quinoa & Avocado Salad','desc': 'Superfood bowl',             'price': '8.00',  'cost': '2.50', 'type': 'First plate',  'recipe': 'Toss quinoa & avocado',           'allergens': []},
        ]
    },
    {
        'name': 'Main Courses',
        'elements': [
            {'name': 'Entrecôte Steak',     'desc': '250 g grilled ribeye',        'price': '14.00', 'cost': '7.00', 'type': 'Second plate', 'recipe': 'Season & grill',                  'allergens': []},
            {'name': 'Pollo Asado',         'desc': 'Roast chicken half',         'price': '10.00', 'cost': '4.00', 'type': 'Second plate', 'recipe': 'Marinate & roast',                'allergens': []},
            {'name': 'Paella Valenciana',   'desc': 'Rice with meat & veggies',   'price': '13.00', 'cost': '5.50', 'type': 'Second plate', 'recipe': 'Cook rice with stock',            'allergens': ['Molluscs', 'Celery']},
            {'name': 'Salmon en Papillote', 'desc': 'Baked salmon parcel',        'price': '12.50', 'cost': '6.00', 'type': 'Second plate', 'recipe': 'Bake in parchment',               'allergens': ['Fish']},
            {'name': 'Vegetable Stir-Fry',  'desc': 'Mixed veg & tofu',          'price': '9.00',  'cost': '3.00', 'type': 'Second plate', 'recipe': 'Stir-fry with soy sauce',         'allergens': ['Soybeans']},
        ]
    },
    {
        'name': 'Side Dishes',
        'elements': [
            {'name': 'French Fries',        'desc': 'Crispy potato fries',         'price': '3.50',  'cost': '1.00', 'type': 'To share',     'recipe': 'Deep-fry potatoes',                'allergens': []},
            {'name': 'Steamed Vegetables',  'desc': 'Carrot, broccoli, beans',     'price': '4.00',  'cost': '1.20', 'type': 'To share',     'recipe': 'Steam & season',                    'allergens': []},
            {'name': 'Garlic Bread',        'desc': 'Toasted with garlic butter', 'price': '3.00',  'cost': '0.80', 'type': 'To share',     'recipe': 'Bake with garlic butter',            'allergens': ['Milk']},
            {'name': 'Onion Rings',         'desc': 'Battered & fried onions',     'price': '4.50',  'cost': '1.30', 'type': 'To share',     'recipe': 'Batter & fry',                      'allergens': ['Egg', 'Gluten']},
            {'name': 'Mixed Olives',        'desc': 'Marinated olives',           'price': '3.50',  'cost': '0.90', 'type': 'To share',     'recipe': 'Marinate in herbs',                 'allergens': ['Sulphites']},
        ]
    },
    {
        'name': 'Desserts',
        'elements': [
            {'name': 'Flan Casero',           'desc': 'Homemade custard',          'price': '3.50',  'cost': '1.00', 'type': 'Dessert',      'recipe': 'Bake custard with caramel',       'allergens': ['Egg', 'Milk']},
            {'name': 'Churros con Chocolate', 'desc': 'Fried dough sticks',       'price': '4.50',  'cost': '1.20', 'type': 'Dessert',      'recipe': 'Fry & serve with chocolate',     'allergens': ['Gluten']},
            {'name': 'Tarta de Queso',        'desc': 'Cheesecake with berries',   'price': '4.00',  'cost': '1.50', 'type': 'Dessert',      'recipe': 'Bake & top with fruit',          'allergens': ['Egg', 'Milk']},
            {'name': 'Chocolate Mousse',      'desc': 'Light & airy',             'price': '4.50',  'cost': '1.20', 'type': 'Dessert',      'recipe': 'Fold whipped cream & chocolate', 'allergens': ['Egg', 'Milk']},
            {'name': 'Fruit Sorbet',          'desc': 'Seasonal fruits',          'price': '3.00',  'cost': '0.70', 'type': 'Dessert',      'recipe': 'Freeze blended fruit',           'allergens': []},
        ]
    },
    {
        'name': 'Specials',
        'elements': [
            {'name': 'Lobster Thermidor',   'desc': 'Creamy lobster bake',        'price': '18.00', 'cost': '9.00', 'type': 'Second plate','recipe':'Bake lobster in mornay','allergens':['Molluscs','Milk']},
            {'name': 'Duck à l’Orange',      'desc': 'Duck breast & orange sauce', 'price': '16.50', 'cost': '8.00', 'type': 'Second plate','recipe':'Roast duck with sauce','allergens':[]},
            {'name': 'Beef Wellington',     'desc': 'Fillet in puff pastry',      'price': '17.00', 'cost': '8.50', 'type': 'Second plate','recipe':'Encase beef in pastry','allergens':['Egg','Gluten']},
            {'name': 'Seafood Paella',      'desc': 'Rice with mixed seafood',    'price': '15.00', 'cost': '7.00', 'type': 'Second plate','recipe':'Cook rice & seafood','allergens':['Crustaceans','Molluscs']},
            {'name': 'Vegan Buddha Bowl',   'desc': 'Grain & veggie bowl',        'price': '12.00', 'cost': '4.00', 'type': 'Second plate','recipe':'Assemble grains & veg','allergens':[]},
        ]
    },
]

for c in categories_data:
    cat, nc = Category.objects.get_or_create(menu=menu, name=c['name'], defaults={'active':True})
    log(f"  • {'Created' if nc else 'Exists'} Category {c['name']}")
    for e in c['elements']:
        ce, ne = CategoryElement.objects.get_or_create(
            category=cat, name=e['name'],
            defaults={
                'description':e['desc'],'price':e['price'],
                'cost':e['cost'],'type':e['type'],
                'recipe':e['recipe'],'active':True
            }
        )
        if ne:
            # load element icon from elements_icons/{name}.png
            icon_file = f"{e['name']}.png"
            icon_path = os.path.join(ELEMENTS_ICON_DIR, icon_file)
            if os.path.exists(icon_path):
                with open(icon_path,'rb') as f:
                    ce.icon.save(icon_file, File(f), save=True)
                log(f"    • Icon for {e['name']}")
        log(f"    • {'Created' if ne else 'Exists'} Element {e['name']}")
        # add allergens
        for alg in e['allergens']:
            try:
                aobj = Allergen.objects.get(name=alg)
                ce.allergens.add(aobj)
                log(f"      – Added Allergen {alg}")
            except Allergen.DoesNotExist:
                log(f"      ! Missing Allergen {alg}")
log("")

# — PART F: MAPS, TABLES, TABLECELLS & BARS —
log("=== Seeding Maps + Tables + Bars ===")
def pad5(n): return str(n).zfill(5)

layouts = [
    # name, dx, dy, table_count, tw, th, cols, row_start
    ("COMEDOR", 26, 24, 20, 2, 2, 5, 7),
    ("SALA DE EVENTOS", 26, 17, 5, 2, 10, 5, 7),
]
for name, dx, dy, tcount, tw, th, cols, base_y in layouts:
    mp, mnew = Map.objects.get_or_create(
        restaurant=rest, name=name,
        defaults={'dimension_x':dx, 'dimension_y':dy}
    )
    log(f"  • {'Created' if mnew else 'Exists'} Map {name}")
    # Tables
    for i in range(tcount):
        row, col = divmod(i, cols)
        x0 = col * (tw+3)
        y0 = base_y + row*(th+3)
        tname = f"{name[:3]}_tbl_{i+1:02d}"
        code = pad5(i+1)
        tbl, tnew = Table.objects.get_or_create(
            map=mp, name=tname,
            defaults={'open':False,'authentication_code':code,'calling_waiter':False}
        )
        if tnew: log(f"    • Table {tname} at ({x0},{y0})")
        existing = set(tbl.cells.values_list('x','y'))
        for dx_ in range(tw):
            for dy_ in range(th):
                cx,cy = x0+dx_, y0+dy_
                if (cx,cy) not in existing:
                    TableCell.objects.create(table=tbl, x=cx, y=cy)
    # Bar 2×4 in top-right, buffer >=3
    bar, bnew = Bar.objects.get_or_create(map=mp)
    log(f"    • {'Created' if bnew else 'Exists'} Bar for {name}")
    existing = set(bar.cells.values_list('x','y'))
    bx0, by0 = dx - tw - 2, 0  # leave 2-cell gap
    for dx_ in range(tw):
        for dy_ in range(4):
            x_, y_ = bx0+dx_, by0+dy_
            if (x_,y_) not in existing:
                BarCell.objects.create(bar=bar, x=x_, y=y_)
log("")

# — FINAL SUMMARY —
log("=== INITIAL DATA COMPLETE ===")
log(f"Restaurant “{rest.name}” summary:")
log(f"  • Workers: {Worker.objects.filter(restaurant=rest).count()}")
log(f"  • Menu:    {Menu.objects.filter(restaurant=rest).count()}")
log(f"  • Categories: {Category.objects.filter(menu=menu).count()}")
log(f"  • Elements:   {CategoryElement.objects.filter(category__menu=menu).count()}")
log(f"  • Maps:       {Map.objects.filter(restaurant=rest).count()}")
log(f"  • Tables:     {Table.objects.filter(map__restaurant=rest).count()}")
log(f"  • Bars:       {Bar.objects.filter(map__restaurant=rest).count()}")
log("\nAll steps logged to data.txt.")
log_file.close()
