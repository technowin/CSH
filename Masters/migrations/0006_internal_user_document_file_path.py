# Generated by Django 4.2.7 on 2024-10-18 05:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Masters', '0005_citizen_document_application_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='internal_user_document',
            name='file_path',
            field=models.TextField(blank=True, null=True),
        ),
    ]
