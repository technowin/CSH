from django.db import models

# Create your models here.
from Account.managers import ServiceManager


class application_form(models.Model):
    id = models.AutoField(primary_key=True)
    request_no = models.TextField(null=True, blank=True)
    status = models.ForeignKey('Masters.status_master', on_delete=models.CASCADE, null=True, blank=True, related_name='status_form_tt')
    applicant_type = models.TextField(null=True, blank=True)
    name_of_applicant = models.TextField(null=True, blank=True)
    plot_no = models.TextField(null=True, blank=True)
    survey_no = models.TextField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    total_trees_to_trim = models.IntegerField(null=True, blank=True)
    reason_for_cutting_trees = models.TextField(null=True, blank=True)
    request_no = models.TextField(null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    approved_remark = models.TextField(null=True, blank=True)
    issued_certificate_remark = models.TextField(null=True, blank=True)
    refused_reason = models.TextField(null=True, blank=True)
    rejected_reason = models.TextField(null=True, blank=True)
    committee_refusal = models.TextField(null=True, blank=True)
    committee_approval = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.TextField(null=True, blank=True)
    objects = ServiceManager()
    
    objects = ServiceManager()
    class Meta:
        db_table = "application_form"  
        app_label = 'TreeTrimming'   


class citizen_document(models.Model):
    id = models.AutoField(primary_key=True) 
    user_id = models.IntegerField() 
    file_name = models.TextField(null=True, blank=True)
    filepath = models.CharField(max_length=1000, null=True, blank=True)  # Add this field
    document = models.ForeignKey('Masters.document_master', on_delete=models.CASCADE, null=True, blank=True, related_name='citizen_documents_tt', db_column='doc_id')  
    correct_mark = models.TextField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)           
    created_by = models.TextField(null=True, blank=True) 
    updated_at = models.DateTimeField(null=True, blank=True)                
    updated_by = models.TextField(null=True, blank=True)
    application_id = models.ForeignKey(application_form, on_delete=models.CASCADE, null=True, blank=True, related_name='application_id_tt', db_column='application_id')   
    objects = ServiceManager()
    class Meta:
        db_table = 'citizen_document'
        app_label = 'TreeTrimming'


class workflow_details(models.Model):
    id = models.AutoField(primary_key=True)
    request_no = models.TextField(null=True, blank=True)  
    level = models.IntegerField(null=True, blank=True)
    status = models.ForeignKey('Masters.status_master', on_delete=models.CASCADE, null=True, blank=True, related_name='status_flow_tt')
    form_user = models.ForeignKey('Account.CustomUser', on_delete=models.CASCADE, null=True, blank=True, related_name='user_flow_tt', db_column='form_user_id')
    form_id = models.ForeignKey(application_form, on_delete=models.CASCADE, null=True, blank=True, related_name='form_id_tt', db_column='form_id')
    send_forward = models.TextField(null=True, blank=True)
    forward = models.TextField(null=True, blank=True)
    sendback = models.TextField(null=True, blank=True)
    rollback = models.TextField(null=True, blank=True)
    pre_statusid = models.TextField(null=True, blank=True)
    pre_user = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.TextField(null=True, blank=True)
    objects = ServiceManager()
    class Meta:
        db_table = 'workflow_details'
        app_label = 'TreeTrimming'


class workflow_history(models.Model):
    id = models.AutoField(primary_key=True)
    workflow_id = models.IntegerField(null=True, blank=True,db_column='workflow_id')
    request_no = models.TextField(null=True, blank=True)  
    level = models.IntegerField(null=True, blank=True)
    status = models.ForeignKey('Masters.status_master', on_delete=models.CASCADE, null=True, blank=True, related_name='status_hist_tt')
    form_user = models.ForeignKey('Account.CustomUser', on_delete=models.CASCADE, null=True, blank=True, related_name='user_hist_tt', db_column='form_user_id')
    form_id = models.ForeignKey(application_form, on_delete=models.CASCADE, null=True, blank=True, related_name='hist_form_id_tt', db_column='form_id')
    send_forward = models.TextField(null=True, blank=True)
    forward = models.TextField(null=True, blank=True)
    sendback = models.TextField(null=True, blank=True)
    rollback = models.TextField(null=True, blank=True)
    pre_statusid = models.TextField(null=True, blank=True)
    pre_user = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.TextField(null=True, blank=True)
    objects = ServiceManager()
    class Meta:
        db_table = 'workflow_history'
        app_label = 'TreeTrimming'

class internal_doc_master(models.Model):
    id = models.AutoField(primary_key=True) 
    doc_name = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)             
    created_by = models.TextField(null=True, blank=True) 
    updated_at = models.DateTimeField(null=True, blank=True)               
    updated_by = models.TextField(null=True, blank=True) 
    objects = ServiceManager()
    class Meta:
        db_table = 'internal_doc_master'
        app_label = 'TreeTrimming'

class internal_user_document(models.Model):
    id = models.AutoField(primary_key=True) 
    workflow = models.ForeignKey(workflow_details, on_delete=models.CASCADE, null=True, blank=True, related_name='workflow_intdoc_tt') 
    file_name = models.TextField(null=True, blank=True)  
    file_path = models.TextField(null=True, blank=True)  
    name = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)             
    created_by = models.TextField(null=True, blank=True) 
    updated_at = models.DateTimeField(null=True, blank=True)               
    updated_by = models.TextField(null=True, blank=True) 
    objects = ServiceManager()
    class Meta:
        db_table = 'internal_user_document'
        app_label = 'TreeTrimming'


class internal_user_comments(models.Model):
    id = models.AutoField(primary_key=True) 
    workflow = models.ForeignKey(workflow_details, on_delete=models.CASCADE, null=True, blank=True, related_name='workflow_intcom_tt') 
    comments = models.TextField(null=True, blank=True)  
    created_at = models.DateTimeField(auto_now_add=True)             
    created_by = models.TextField(null=True, blank=True) 
    updated_at = models.DateTimeField(null=True, blank=True)               
    updated_by = models.TextField(null=True, blank=True) 
    objects = ServiceManager()
    class Meta:
        db_table = 'internal_user_comments'
        app_label = 'TreeTrimming'
        