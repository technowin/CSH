# Generated by Django 4.2.7 on 2024-10-23 07:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Masters', '0009_rename_href_service_matrix_model_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='service_master',
            name='short_name',
            field=models.TextField(blank=True, null=True),
        ),
    ]
