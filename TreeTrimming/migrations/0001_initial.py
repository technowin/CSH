# Generated by Django 4.2.7 on 2024-11-28 06:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('Masters', '0004_status_master_status_color'),
    ]

    operations = [
        migrations.CreateModel(
            name='application_form',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('applicant_type', models.TextField(blank=True, null=True)),
                ('name_of_applicant', models.TextField(blank=True, null=True)),
                ('plot_no', models.TextField(blank=True, null=True)),
                ('survey_no', models.TextField(blank=True, null=True)),
                ('address', models.TextField(blank=True, null=True)),
                ('total_trees_to_trim', models.IntegerField(blank=True, null=True)),
                ('reason_for_cutting_trees', models.TextField(blank=True, null=True)),
                ('request_no', models.TextField(blank=True, null=True)),
                ('comments', models.TextField(blank=True, null=True)),
                ('approved_remark', models.TextField(blank=True, null=True)),
                ('issued_certificate_remark', models.TextField(blank=True, null=True)),
                ('refused_reason', models.TextField(blank=True, null=True)),
                ('rejected_reason', models.TextField(blank=True, null=True)),
                ('committee_refusal', models.TextField(blank=True, null=True)),
                ('committee_approval', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.TextField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('updated_by', models.TextField(blank=True, null=True)),
                ('status', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='status_form_tt', to='Masters.status_master')),
            ],
            options={
                'db_table': 'application_form',
            },
        ),
        migrations.CreateModel(
            name='internal_doc_master',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('doc_name', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.TextField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(blank=True, null=True)),
                ('updated_by', models.TextField(blank=True, null=True)),
            ],
            options={
                'db_table': 'internal_doc_master',
            },
        ),
        migrations.CreateModel(
            name='workflow_history',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('workflow_id', models.IntegerField(blank=True, db_column='workflow_id', null=True)),
                ('request_no', models.TextField(blank=True, null=True)),
                ('level', models.IntegerField(blank=True, null=True)),
                ('send_forward', models.TextField(blank=True, null=True)),
                ('forward', models.TextField(blank=True, null=True)),
                ('sendback', models.TextField(blank=True, null=True)),
                ('rollback', models.TextField(blank=True, null=True)),
                ('pre_statusid', models.TextField(blank=True, null=True)),
                ('pre_user', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.TextField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(blank=True, null=True)),
                ('updated_by', models.TextField(blank=True, null=True)),
                ('form_id', models.ForeignKey(blank=True, db_column='form_id', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='hist_form_id_tt', to='TreeTrimming.application_form')),
                ('form_user', models.ForeignKey(blank=True, db_column='form_user_id', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_hist_tt', to=settings.AUTH_USER_MODEL)),
                ('status', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='status_hist_tt', to='Masters.status_master')),
            ],
            options={
                'db_table': 'workflow_history',
            },
        ),
        migrations.CreateModel(
            name='workflow_details',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('request_no', models.TextField(blank=True, null=True)),
                ('level', models.IntegerField(blank=True, null=True)),
                ('send_forward', models.TextField(blank=True, null=True)),
                ('forward', models.TextField(blank=True, null=True)),
                ('sendback', models.TextField(blank=True, null=True)),
                ('rollback', models.TextField(blank=True, null=True)),
                ('pre_statusid', models.TextField(blank=True, null=True)),
                ('pre_user', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.TextField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(blank=True, null=True)),
                ('updated_by', models.TextField(blank=True, null=True)),
                ('form_id', models.ForeignKey(blank=True, db_column='form_id', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='form_id_tt', to='TreeTrimming.application_form')),
                ('form_user', models.ForeignKey(blank=True, db_column='form_user_id', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_flow_tt', to=settings.AUTH_USER_MODEL)),
                ('status', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='status_flow_tt', to='Masters.status_master')),
            ],
            options={
                'db_table': 'workflow_details',
            },
        ),
        migrations.CreateModel(
            name='internal_user_document',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('file_name', models.TextField(blank=True, null=True)),
                ('file_path', models.TextField(blank=True, null=True)),
                ('name', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.TextField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(blank=True, null=True)),
                ('updated_by', models.TextField(blank=True, null=True)),
                ('workflow', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='workflow_intdoc_tt', to='TreeTrimming.workflow_details')),
            ],
            options={
                'db_table': 'internal_user_document',
            },
        ),
        migrations.CreateModel(
            name='internal_user_comments',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('comments', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.TextField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(blank=True, null=True)),
                ('updated_by', models.TextField(blank=True, null=True)),
                ('workflow', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='workflow_intcom_tt', to='TreeTrimming.workflow_details')),
            ],
            options={
                'db_table': 'internal_user_comments',
            },
        ),
        migrations.CreateModel(
            name='citizen_document',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('user_id', models.IntegerField()),
                ('file_name', models.TextField(blank=True, null=True)),
                ('filepath', models.CharField(blank=True, max_length=1000, null=True)),
                ('correct_mark', models.TextField(blank=True, null=True)),
                ('comment', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.TextField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(blank=True, null=True)),
                ('updated_by', models.TextField(blank=True, null=True)),
                ('application_id', models.ForeignKey(blank=True, db_column='application_id', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='application_id_tt', to='TreeTrimming.application_form')),
                ('document', models.ForeignKey(blank=True, db_column='doc_id', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='citizen_documents_tt', to='Masters.document_master')),
            ],
            options={
                'db_table': 'citizen_document',
            },
        ),
    ]
