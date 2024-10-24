# Generated by Django 4.2.7 on 2024-10-18 08:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Masters', '0005_citizen_document_application_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='application_form',
            name='approved_remark',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='application_form',
            name='issued_certificate_remark',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='application_form',
            name='refused_reason',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='application_form',
            name='rejected_reason',
            field=models.TextField(blank=True, null=True),
        ),
    ]
