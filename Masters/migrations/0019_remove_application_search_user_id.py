# Generated by Django 4.2.7 on 2024-09-19 05:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Masters', '0018_application_search_menu_id_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='application_search',
            name='user_id',
        ),
    ]