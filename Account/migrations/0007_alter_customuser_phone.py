# Generated by Django 4.2.7 on 2025-01-09 13:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Account', '0005_alter_customuser_phone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='phone',
            field=models.CharField(max_length=255, unique=True),
        ),
    ]
