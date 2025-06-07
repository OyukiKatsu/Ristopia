# Initial_DATA.py
#python manage.py shell
#exec(open('Initial_DATA.py', encoding='utf-8').read())
import os
import random
import django
from datetime import datetime
from django.conf import settings
from django.core.files import File
from django.contrib.auth.models import User
from django.core.management import call_command

from core.models import (
    Allergen,
    Profile,
    Restaurante,
    Worker,
    Menu,
    Category,
    CategoryElement,
    Map,
    Table,
    TableCell,
    Bar,
    BarCell,
)

# ————————————— OPEN LOG FILE —————————————
log_path = os.path.join(os.getcwd(), 'data.txt')
log_file = open(log_path, 'w', encoding='utf-8')

def log(msg: str):
    """Print to console AND write to data.txt."""
    print(msg)
    log_file.write(msg + '\n')

# — (1) Ensure Django is configured if run standalone:
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TFG.settings')
django.setup()

# — (2) Run migrations:
log(">>> Running makemigrations…")
try:
    call_command('makemigrations', 'core', interactive=False)
    log("    • makemigrations done.")
except Exception as e:
    log(f"    • makemigrations output: {e}")

log(">>> Running migrate…")
call_command('migrate', interactive=False)
log("    • migrate done.")

# ────────────────────────────────────
#   BORRAR TODO EL CONTENIDO EXISTENTE
# ────────────────────────────────────
log(">>> Clearing existing data from all tables…")
from django.db import transaction

with transaction.atomic():
    from core.models import OrderState, TableOrder
    OrderState.objects.all().delete()
    TableOrder.objects.all().delete()

    from core.models import TableCell, BarCell
    TableCell.objects.all().delete()
    BarCell.objects.all().delete()

    from core.models import Table, Bar
    Table.objects.all().delete()
    Bar.objects.all().delete()

    from core.models import Map
    Map.objects.all().delete()

    from core.models import CategoryElement, Category
    CategoryElement.objects.all().delete()
    Category.objects.all().delete()

    from core.models import Menu
    Menu.objects.all().delete()

    from core.models import Worker
    Worker.objects.all().delete()

    from core.models import Restaurante
    Restaurante.objects.all().delete()

    from core.models import Profile
    Profile.objects.all().delete()

    User.objects.filter(is_superuser=False).delete()

    from core.models import Allergen
    Allergen.objects.all().delete()

log(">>> Database cleared.\n")

# ───────────────────────────────────────────────
# 1. Folders where your “initial” icons live. Adjust as needed.
ALLERGEN_ICON_DIR = os.path.join(settings.MEDIA_ROOT, 'core/forInitialData/allergen_icons')
ELEMENTS_ICON_DIR = os.path.join(settings.MEDIA_ROOT, 'core/forInitialData/elements_icons')  # not used
OWNER_ICON_DIR    = os.path.join(settings.MEDIA_ROOT, 'core/forInitialData/owner_icon')
WORKERS_ICON_DIR  = os.path.join(settings.MEDIA_ROOT, 'core/forInitialData/workers_icons')
# ───────────────────────────────────────────────

# ----------------------------------------------------------------------------
# PART A: CREATE ALLERGENS
allergen_names = [
    "Gluten", "Crustaceans", "Egg", "Fish", "Peanuts",
    "Soybeans", "Milk", "Treenuts", "Celery",
    "Mustard", "Sesame", "Lupin", "Molluscs",
]
log("=== Creating (or updating) allergens ===")
for name in allergen_names:
    allergen, created = Allergen.objects.get_or_create(name=name)
    icon_filename = f"{name}.png"
    icon_path = os.path.join(ALLERGEN_ICON_DIR, icon_filename)

    if os.path.exists(icon_path):
        with open(icon_path, 'rb') as f:
            allergen.icon.save(icon_filename, File(f), save=True)
        log(f"  • Icon set for: {name}")
    else:
        log(f"  • (No icon found for {name}, skipping icon)")

    if created:
        log(f"  • Created allergen: {name}")
    else:
        log(f"  • Already existed: {name}")

log(f"=== Done with allergens. Total in DB: {Allergen.objects.count()} ===\n")

# ----------------------------------------------------------------------------
# PART B: CREATE OWNER USER + PROFILE
log("=== Creating owner user/profile ===")

owner_username = 'Oyuki_Katsu'
owner_email    = 'gjaraizm@gmail.com'
owner_password = 'testing1234'

owner_user, was_new = User.objects.get_or_create(
    username=owner_username,
    defaults={'email': owner_email}
)
if was_new:
    owner_user.set_password(owner_password)
    owner_user.save()
    log(f"  • Created User: {owner_username} / {owner_email}")
else:
    log(f"  • User {owner_username} already exists (skipping password‐set).")

owner_profile, prof_created = Profile.objects.get_or_create(
    user=owner_user,
    defaults={'email': owner_email}
)
if prof_created:
    files = [
        fn for fn in os.listdir(OWNER_ICON_DIR)
        if fn.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))
    ]
    if files:
        chosen = random.choice(files)
        chosen_path = os.path.join(OWNER_ICON_DIR, chosen)
        with open(chosen_path, 'rb') as f:
            owner_profile.profile_picture.save(chosen, File(f), save=True)
        log(f"  • Picked random owner icon: {chosen}")
    else:
        log("  • (No files found in OWNER_ICON_DIR; owner keeps default icon.)")
    owner_profile.save()
    log(f"  • Created Profile for owner: {owner_profile.user.username}")
else:
    log(f"  • Owner profile already exists for {owner_profile.user.username}. No new Profile created.")

log("")

# ----------------------------------------------------------------------------
# PART C: CREATE RESTAURANT “ASADOR MONTEQUINTO”
log("=== Creating restaurant “ASADOR MONTEQUINTO” ===")
restaurant_name = "ASADOR MONTEQUINTO"

restaurant, rest_created = Restaurante.objects.get_or_create(
    name=restaurant_name,
    defaults={'owner': owner_profile}
)
if rest_created:
    if owner_profile.profile_picture and os.path.exists(owner_profile.profile_picture.path):
        icon_basename = os.path.basename(owner_profile.profile_picture.path)
        with open(owner_profile.profile_picture.path, 'rb') as f:
            restaurant.icon.save(icon_basename, File(f), save=True)
        log(f"  • Saved restaurant icon from owner’s profile picture ({icon_basename})")
    else:
        log("  • Owner has no profile picture on disk; restaurant will have no icon.")
    restaurant.owner = owner_profile
    restaurant.save()
    log(f"  • Created Restaurant: {restaurant.name}")
else:
    log(f"  • Restaurant {restaurant.name} already exists (skipping).")

log("")

# ----------------------------------------------------------------------------
# PART D: CREATE WORKERS (CHEF_TEST and WAITER_TEST)
log("=== Creating worker users/profiles ===")
workers_data = [
    {
        'username':   'CHEF_TEST',
        'email':      'xgjarmor597@ieshnosmachado.org',
        'login_code': '12345',
        'type':       'Chef',
    },
    {
        'username':   'WAITER_TEST',
        'email':      'pwpvivaecyp@gmail.com',
        'login_code': '54321',
        'type':       'Waiter',
    }
]

for w in workers_data:
    user_obj, created_user = User.objects.get_or_create(
        username=w['username'],
        defaults={'email': w['email']}
    )

    if created_user:
        user_obj.set_password("default1234")
        user_obj.save()
        log(f"  • Created user: {w['username']} / {w['email']} (password=default1234)")
    else:
        log(f"  • User {w['username']} already exists.")

    prof_obj, prof_was_new = Profile.objects.get_or_create(
        user=user_obj,
        defaults={'email': w['email']}
    )
    if prof_was_new:
        files = [
            fn for fn in os.listdir(WORKERS_ICON_DIR)
            if fn.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))
        ]
        if files:
            chosen = random.choice(files)
            chosen_path = os.path.join(WORKERS_ICON_DIR, chosen)
            with open(chosen_path, 'rb') as f:
                prof_obj.profile_picture.save(chosen, File(f), save=True)
            log(f"    • Picked random worker icon: {chosen}")
        else:
            log("    • (No files found in WORKERS_ICON_DIR; worker keeps default icon.)")
        prof_obj.save()
        log(f"    • Created Profile for worker: {prof_obj.user.username}")
    else:
        log(f"    • Profile already exists for worker {prof_obj.user.username}.")

    worker_obj, worker_created = Worker.objects.get_or_create(
        user=prof_obj,
        restaurant=restaurant,
        defaults={
            'login_code': w['login_code'],
            'type':       w['type'],
            'active':     True
        }
    )
    if worker_created:
        log(f"    • Created Worker: {w['username']} as {w['type']} (code {w['login_code']})")
    else:
        log(f"    • Worker {w['username']} already existed for this restaurant. Skipping.")

log("")

# ----------------------------------------------------------------------------
# PART E: CREATE MENU + CATEGORIES + CATEGORYELEMENTS
log("=== Creating menu, categories, and category elements ===")
menu_obj, menu_created = Menu.objects.get_or_create(restaurant=restaurant)
if menu_created:
    log(f"  • Created Menu for restaurant {restaurant.name}")
else:
    log(f"  • Menu for {restaurant.name} already exists")

categories_data = [
    {
        'name': 'Drinks',
        'elements': [
            {'name': 'Mineral Water',    'desc': 'Still mineral water (500ml)',       'price': '1.50',  'cost': '0.30',  'type': 'Drink',       'recipe': 'Serve cold.'},
            {'name': 'Coca‐Cola',         'desc': 'Coca‐Cola (330ml)',                 'price': '2.00',  'cost': '0.50',  'type': 'Drink',       'recipe': 'Serve cold.'},
            {'name': 'Beer (Caña)',       'desc': 'House draft beer (200ml)',         'price': '2.50',  'cost': '0.70',  'type': 'Drink',       'recipe': 'Serve cold with foamy head.'},
            {'name': 'Red Wine Glass',    'desc': 'Glass of Rioja (125ml)',           'price': '3.50',  'cost': '1.00',  'type': 'Drink',       'recipe': 'Serve at room temperature.'},
            {'name': 'Orange Juice',      'desc': 'Fresh‐squeezed orange juice (300ml)','price': '3.00',  'cost': '0.80',  'type': 'Drink',       'recipe': 'Serve cold with ice.'},
        ]
    },
    {
        'name': 'Starters',
        'elements': [
            {'name': 'Patatas Bravas',           'desc': 'Fried potatoes with spicy sauce',    'price': '5.00', 'cost': '1.50', 'type': 'To share',    'recipe': 'Fry in oil, top with sauce.'},
            {'name': 'Gazpacho Andaluz',         'desc': 'Cold tomato‐based soup',               'price': '4.50', 'cost': '1.20', 'type': 'First plate',  'recipe': 'Blend vegetables, chill.'},
            {'name': 'Jamón Ibérico Platter',    'desc': 'Iberian ham with bread',               'price': '8.00', 'cost': '3.00', 'type': 'To share',    'recipe': 'Arrange on plate with bread.'},
            {'name': 'Croquetas de Jamón',       'desc': 'Ham croquettes (6 units)',             'price': '4.00', 'cost': '1.00', 'type': 'First plate',  'recipe': 'Deep‐fry until golden.'},
            {'name': 'Ensalada Mixta',           'desc': 'Mixed salad: lettuce, tomato, olives',  'price': '4.00', 'cost': '1.00', 'type': 'First plate',  'recipe': 'Mix all ingredients fresh.'},
        ]
    },
    {
        'name': 'Main Courses',
        'elements': [
            {'name': 'Entrecôte Steak',           'desc': 'Grilled ribeye steak (250g)',         'price': '12.00', 'cost': '6.00', 'type': 'Second plate', 'recipe': 'Season, grill to preference.'},
            {'name': 'Pollo Asado',               'desc': 'Roast chicken half with potatoes',     'price': '9.00',  'cost': '4.00', 'type': 'Second plate', 'recipe': 'Marinate, roast until golden.'},
            {'name': 'Paella Valenciana',         'desc': 'Rice with rabbit, chicken, beans',      'price': '11.00', 'cost': '5.00', 'type': 'Second plate', 'recipe': 'Cook rice with stock, meat, beans.'},
            {'name': 'Bacalao a la Vizcaína',      'desc': 'Salt cod in tomato sauce',             'price': '10.00', 'cost': '4.00', 'type': 'Second plate', 'recipe': 'Soak cod, cook in sauce.'},
            {'name': 'Lomo a la Navarra',          'desc': 'Pork loin wrapped in bacon',            'price': '11.50', 'cost': '5.50', 'type': 'Second plate', 'recipe': 'Grill pork wrapped in bacon.'},
        ]
    },
    {
        'name': 'Desserts',
        'elements': [
            {'name': 'Flan Casero',        'desc': 'Homemade custard flan',                   'price': '3.50',  'cost': '1.00', 'type': 'Dessert',      'recipe': 'Bake custard, add caramel.'},
            {'name': 'Churros con Chocolate','desc': 'Fried dough sticks with thick chocolate','price': '4.50',  'cost': '1.20', 'type': 'Dessert',      'recipe': 'Fry dough, serve with hot chocolate.'},
            {'name': 'Tarta de Queso',      'desc': 'Cheesecake with berry sauce',             'price': '4.00',  'cost': '1.50', 'type': 'Dessert',      'recipe': 'Bake cheesecake, top with berries.'},
        ]
    },
]

for cat_data in categories_data:
    category_obj, cat_created = Category.objects.get_or_create(
        menu=menu_obj,
        name=cat_data['name'],
        defaults={'active': True}
    )
    if cat_created:
        log(f"  • Created Category: {cat_data['name']}")
    else:
        log(f"  • Category {cat_data['name']} already exists")

    for elem in cat_data['elements']:
        ce_obj, ce_created = CategoryElement.objects.get_or_create(
            category=category_obj,
            name=elem['name'],
            defaults={
                'description': elem['desc'],
                'price':       elem['price'],
                'cost':        elem['cost'],
                'type':        elem['type'],
                'recipe':      elem['recipe'],
                'active':      True
            }
        )
        if ce_created:
            log(f"    • Created CategoryElement: {elem['name']} (in {cat_data['name']})")
        else:
            log(f"    • CategoryElement {elem['name']} already exists (in {cat_data['name']})")

log("")

# ────────────────────────────────────
# PART F: CREATE MAPS, TABLES, TABLECELLS, BARS, BARCELLS
# ────────────────────────────────────
def code5(n):
    return str(n).zfill(5)

log("=== Creating maps, tables, and bars ===")

# — Map 1: “COMEDOR” (26×24) —
map1_obj, map1_created = Map.objects.get_or_create(
    restaurant=restaurant,
    name="COMEDOR",
    defaults={'dimension_x': 26, 'dimension_y': 24}
)
if map1_created:
    log("  • Created Map: COMEDOR (26×24)")
else:
    log("  • Map COMEDOR already exists")

# 20 tables (2×2) in a 5×4 grid, base_y=7
for i in range(20):
    row, col = divmod(i, 5)
    t_x0 = col * 5       # (2 + 3)
    t_y0 = 7 + row * 5   # (2 + 3)
    table_name = f"COMEDOR_tbl_{i+1:02d}"
    code = code5(i+1)

    tbl_obj, tbl_created = Table.objects.get_or_create(
        map=map1_obj,
        name=table_name,
        defaults={
            'open':               False,
            'authentication_code': code,
            'calling_waiter':     False
        }
    )
    if tbl_created:
        log(f"    • Created Table: {table_name} at ({t_x0},{t_y0}) code={code}")
    else:
        log(f"    • Table {table_name} already exists")

    existing_cells = set(tbl_obj.cells.values_list('x', 'y'))
    for dx in range(2):
        for dy in range(2):
            cx, cy = t_x0 + dx, t_y0 + dy
            if (cx, cy) not in existing_cells:
                TableCell.objects.create(table=tbl_obj, x=cx, y=cy)

# Bar 2×4 at top-right (x=24,y=0)
bar1_obj, bar1_created = Bar.objects.get_or_create(map=map1_obj)
if bar1_created:
    log("    • Created Bar for COMEDOR at (24,0)")
else:
    log("    • Bar already exists for COMEDOR")

existing_bar_cells = set(bar1_obj.cells.values_list('x', 'y'))
for dx in range(2):
    for dy in range(4):
        bx, by = 24 + dx, dy
        if (bx, by) not in existing_bar_cells:
            BarCell.objects.create(bar=bar1_obj, x=bx, y=by)

log("  • Finished setting up COMEDOR (tables + bar).\n")

# — Map 2: “SALA DE EVENTOS” (26×17) —
map2_obj, map2_created = Map.objects.get_or_create(
    restaurant=restaurant,
    name="SALA DE EVENTOS",
    defaults={'dimension_x': 26, 'dimension_y': 17}
)
if map2_created:
    log("  • Created Map: SALA DE EVENTOS (26×17)")
else:
    log("  • Map SALA DE EVENTOS already exists")

# 5 tables (2×10) in a row, base_y=7
for i in range(5):
    t_x0, t_y0 = i * 5, 7
    table_name = f"SALAEV_tbl_{i+1}"
    code = code5(100 + i + 1)

    tbl_obj, tbl_created = Table.objects.get_or_create(
        map=map2_obj,
        name=table_name,
        defaults={
            'open':               False,
            'authentication_code': code,
            'calling_waiter':     False
        }
    )
    if tbl_created:
        log(f"    • Created Table: {table_name} at ({t_x0},{t_y0}) code={code}")
    else:
        log(f"    • Table {table_name} already exists")

    existing_cells = set(tbl_obj.cells.values_list('x', 'y'))
    for dx in range(2):
        for dy in range(10):
            cx, cy = t_x0 + dx, t_y0 + dy
            if (cx, cy) not in existing_cells:
                TableCell.objects.create(table=tbl_obj, x=cx, y=cy)

# Bar 2×4 at top-right (x=24,y=0)
bar2_obj, bar2_created = Bar.objects.get_or_create(map=map2_obj)
if bar2_created:
    log("    • Created Bar for SALA DE EVENTOS at (24,0)")
else:
    log("    • Bar already exists for SALA DE EVENTOS")

existing_bar2_cells = set(bar2_obj.cells.values_list('x', 'y'))
for dx in range(2):
    for dy in range(4):
        bx, by = 24 + dx, dy
        if (bx, by) not in existing_bar2_cells:
            BarCell.objects.create(bar=bar2_obj, x=bx, y=by)

log("  • Finished setting up SALA DE EVENTOS (tables + bar).\n\n")

# ────────────────────────────────────
# FINAL: SUMMARY
log("=== INITIAL DATA SCRIPT COMPLETE ===")
log(f"Restaurant “{restaurant.name}” now has:")
log(f"  • {Worker.objects.filter(restaurant=restaurant).count()} workers")
log(f"  • {Menu.objects.filter(restaurant=restaurant).count()} menu")
log(f"  • {Category.objects.filter(menu=menu_obj).count()} categories")
log(f"  • {CategoryElement.objects.filter(category__menu=menu_obj).count()} elements")
log(f"  • {Map.objects.filter(restaurant=restaurant).count()} maps")
log(f"  • {Table.objects.filter(map__restaurant=restaurant).count()} tables")
log(f"  • {Bar.objects.filter(map__restaurant=restaurant).count()} bars")
log("")
log("**If you saw any “already exists” messages, it means this script was run before or some data was partially created.**")
log("Everything that did not exist has now been created.")

# ————————————— CLOSE LOG FILE —————————————
log_file.close()