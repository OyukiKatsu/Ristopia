# Generated by Django 5.2 on 2025-05-30 12:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_map_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='worker',
            name='login_code',
            field=models.CharField(max_length=20, unique=True),
        ),
    ]
