# Generated by Django 4.2.7 on 2024-08-23 09:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Account', '0002_customuser_role'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='encrypted_password',
        ),
        migrations.RemoveField(
            model_name='customuser',
            name='is_staff',
        ),
        migrations.RemoveField(
            model_name='customuser',
            name='password_text',
        ),
        migrations.RemoveField(
            model_name='customuser',
            name='title',
        ),
    ]
