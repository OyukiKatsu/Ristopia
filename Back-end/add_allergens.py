import os
from django.core.files import File
from core.models import Allergen  
from django.conf import settings
# Use
# python manage.py shell
# exec(open('add_allergens.py').read())

# Where your allergen icons are stored
ICON_DIR = os.path.join(settings.MEDIA_ROOT, 'core/allergen_icons')

allergens = [
    "Gluten",
    "Crustaceans",
    "Egg",
    "Fish",
    "Peanuts",
    "Soybeans",
    "Milk",
    "Peanuts",
    "Treenuts",
    "Celery",
    "Mustard",
    "Sesame",
    "So",
    "Lupin",
    "Molluscs"
]

created_count = 0
for name in allergens:
    allergen, created = Allergen.objects.get_or_create(name=name)

    icon_filename = f"{name}.png"
    icon_path = os.path.join(ICON_DIR, icon_filename)

    if os.path.exists(icon_path):
        with open(icon_path, 'rb') as f:
            allergen.icon.save(icon_filename, File(f), save=True)
        print(f"Icon set for: {name}")
    else:
        print(f"Icon not found for: {name} ({icon_path})")

    if created:
        print(f"Created allergen: {name}")
        created_count += 1
    else:
        print(f"Already exists: {name}")

print(f"\nDone. {created_count} new allergens added or updated with icons.")
