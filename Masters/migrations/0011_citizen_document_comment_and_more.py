# Generated by Django 4.2.7 on 2024-10-24 05:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Masters', '0010_service_master_short_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='citizen_document',
            name='comment',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='citizen_document',
            name='correct_mark',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='citizen_document',
            name='incorrect_mark',
            field=models.TextField(blank=True, null=True),
        ),
    ]