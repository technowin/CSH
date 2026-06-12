from django.db import models
from Account.managers import ServiceManager
from Masters.models import *
       
# In aqi/models.py

class application_form(models.Model):
    id = models.AutoField(primary_key=True)
    request_no = models.TextField(null=True, blank=True)
    status_id = models.IntegerField(null=True, blank=True)  # Store status ID
    
    # AQI specific fields
    village_name = models.TextField(null=True, blank=True)
    bp_fire_no = models.TextField(null=True, blank=True)
    survey_no = models.TextField(null=True, blank=True)
    plot_no = models.TextField(null=True, blank=True)
    architect_name = models.TextField(null=True, blank=True)
    builder_name = models.TextField(null=True, blank=True)
    plot_area = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    
    # Monthly submission fields
    submission_month = models.CharField(max_length=10, null=True, blank=True)
    submission_type = models.CharField(max_length=20, null=True, blank=True)
    is_draft = models.IntegerField(default=1)
    
    # Workflow & remarks
    comments = models.TextField(null=True, blank=True)
    approved_remark = models.TextField(null=True, blank=True)
    rejected_reason = models.TextField(null=True, blank=True)
    refused_reason = models.TextField(null=True, blank=True)
    issued_certificate_remark = models.TextField(null=True, blank=True)
    
    parent_application_id = models.IntegerField(null=True, blank=True)

    # Monthly AQI specific fields
    monthly_aqi_value = models.IntegerField(null=True, blank=True)
    monthly_aqi_category = models.CharField(max_length=50, null=True, blank=True)
    monthly_remarks = models.TextField(null=True, blank=True)  
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.TextField(null=True, blank=True)
    
    objects = ServiceManager()
    
    class Meta:
        db_table = "application_form"  # Same table name as TreeTrimming
        app_label = 'aqi'
    
    @property
    def status(self):
        from Masters.models import status_master
        if self.status_id:
            return status_master.objects.filter(status_id=self.status_id).first()
        return None


class citizen_document(models.Model):
    id = models.AutoField(primary_key=True) 
    user_id = models.IntegerField() 
    file_name = models.TextField(null=True, blank=True)
    filepath = models.CharField(max_length=1000, null=True, blank=True)
    doc_id = models.IntegerField(null=True, blank=True)
    application_id = models.IntegerField(null=True, blank=True)
    correct_mark = models.TextField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)           
    created_by = models.TextField(null=True, blank=True) 
    updated_at = models.DateTimeField(null=True, blank=True)                
    updated_by = models.TextField(null=True, blank=True)
    
    objects = ServiceManager()
    
    class Meta:
        db_table = 'citizen_document'  # Same table name
        app_label = 'aqi'


class workflow_details(models.Model):
    id = models.AutoField(primary_key=True)
    request_no = models.TextField(null=True, blank=True)  
    level = models.IntegerField(null=True, blank=True)
    status_id = models.IntegerField(null=True, blank=True)  # Use IntegerField, not ForeignKey
    form_user_id = models.IntegerField(null=True, blank=True)
    form_id = models.IntegerField(null=True, blank=True)
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
        db_table = 'workflow_details'  # Same table name
        app_label = 'aqi'


class workflow_history(models.Model):
    id = models.AutoField(primary_key=True)
    workflow_id = models.IntegerField(null=True, blank=True)
    request_no = models.TextField(null=True, blank=True)  
    level = models.IntegerField(null=True, blank=True)
    status_id = models.IntegerField(null=True, blank=True)
    form_user_id = models.IntegerField(null=True, blank=True)
    form_id = models.IntegerField(null=True, blank=True)
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
        db_table = 'workflow_history'  # Same table name
        app_label = 'aqi'

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
        app_label = 'aqi'

class internal_user_document(models.Model):
    id = models.AutoField(primary_key=True) 
    workflow = models.ForeignKey(workflow_details, on_delete=models.CASCADE, null=True, blank=True, related_name='workflow_intdoc_aqi') 
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
        app_label = 'aqi'

class internal_user_comments(models.Model):
    id = models.AutoField(primary_key=True) 
    workflow = models.ForeignKey(workflow_details, on_delete=models.CASCADE, null=True, blank=True, related_name='workflow_intcom_aqi') 
    comments = models.TextField(null=True, blank=True)  
    created_at = models.DateTimeField(auto_now_add=True)             
    created_by = models.TextField(null=True, blank=True) 
    updated_at = models.DateTimeField(null=True, blank=True)               
    updated_by = models.TextField(null=True, blank=True) 
    
    objects = ServiceManager()
    
    class Meta:
        db_table = 'internal_user_comments'
        app_label = 'aqi'