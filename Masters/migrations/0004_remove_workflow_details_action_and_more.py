# Generated by Django 4.2.7 on 2024-10-15 07:02

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('Masters', '0003_smslog_smstext'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='workflow_details',
            name='action',
        ),
        migrations.RemoveField(
            model_name='workflow_details',
            name='user',
        ),
        migrations.RemoveField(
            model_name='workflow_history',
            name='action',
        ),
        migrations.RemoveField(
            model_name='workflow_history',
            name='user',
        ),
        migrations.AddField(
            model_name='workflow_details',
            name='form_id',
            field=models.ForeignKey(blank=True, db_column='form_id', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='form_id_F', to='Masters.application_form'),
        ),
        migrations.AddField(
            model_name='workflow_details',
            name='form_user',
            field=models.ForeignKey(blank=True, db_column='form_user_id', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_flow_F', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='workflow_history',
            name='form_id',
            field=models.ForeignKey(blank=True, db_column='form_id', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='hist_form_id_F', to='Masters.application_form'),
        ),
        migrations.AddField(
            model_name='workflow_history',
            name='form_user',
            field=models.ForeignKey(blank=True, db_column='form_user_id', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_hist_F', to=settings.AUTH_USER_MODEL),
        ),
    ]
