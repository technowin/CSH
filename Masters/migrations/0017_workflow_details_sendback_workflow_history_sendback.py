# Generated by Django 4.2.7 on 2024-10-29 05:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Masters', '0016_rename_previous_user_workflow_details_pre_statusid_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='workflow_details',
            name='sendback',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='workflow_history',
            name='sendback',
            field=models.TextField(blank=True, null=True),
        ),
    ]
