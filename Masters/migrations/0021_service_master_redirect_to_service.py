# Generated by Django 4.2.7 on 2024-11-11 06:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Masters', '0020_remove_service_matrix_role_service_matrix_role_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='service_master',
            name='redirect_to_service',
            field=models.TextField(blank=True, null=True),
        ),
    ]