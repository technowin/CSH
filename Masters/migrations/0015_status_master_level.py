# Generated by Django 4.2.7 on 2024-10-25 11:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Masters', '0014_workflow_details_forward_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='status_master',
            name='level',
            field=models.TextField(blank=True, null=True),
        ),
    ]