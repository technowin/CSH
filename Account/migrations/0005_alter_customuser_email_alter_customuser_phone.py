# Generated by Django 4.2.7 on 2024-11-06 11:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Account', '0004_customuser_superior_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='email',
            field=models.EmailField(max_length=254),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='phone',
            field=models.CharField(max_length=15),
        ),
    ]
