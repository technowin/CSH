# Generated by Django 4.2.7 on 2024-10-16 06:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Masters', '0004_remove_workflow_details_action_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='citizen_document',
            name='application_id',
            field=models.ForeignKey(blank=True, db_column='application_id', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='application_id_F', to='Masters.application_form'),
        ),
    ]
