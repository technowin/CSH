# Generated by Django 4.2.7 on 2025-03-06 05:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Masters', '0008_api_data_form_id_api_data_form_user_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='document_master',
            name='order_by',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
