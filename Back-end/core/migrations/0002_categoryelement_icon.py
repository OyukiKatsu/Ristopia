# Generated by Django 5.2 on 2025-05-07 12:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='categoryelement',
            name='icon',
            field=models.ImageField(blank=True, null=True, upload_to='category_element_icons/'),
        ),
    ]
