from django.db import models

# Create your models here.

from django.db import models

from Account.models import CustomUser
from Account.managers import ServiceManager
 
class application_search(models.Model):
    id = models.AutoField(primary_key=True)
    name =models.TextField(null=True,blank=True)
    description =models.TextField(null=True,blank=True)
    href =models.TextField(null=True,blank=True)
    menu_id =models.TextField(null=True,blank=True)
    is_active =models.BooleanField(null=True,blank=True,default=True)
    created_at = models.DateTimeField(null=True,blank=True,auto_now_add=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE,related_name='app_search_created',blank=True, null=True,db_column='created_by')
    updated_at = models.DateTimeField(null=True,blank=True,auto_now_add=True)
    updated_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE,related_name='app_search_updated',blank=True, null=True,db_column='updated_by')
    objects = ServiceManager()
    class Meta:
        db_table = 'application_search'
    def __str__(self):
        return self.name
         
class Roles(models.Model):
    id = models.AutoField(primary_key=True)
    role_id = models.IntegerField(null=True, blank=False)
    role_name = models.TextField(null=True, blank=True)
    role_type = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True, auto_now=True)
    created_by = models.ForeignKey('Account.CustomUser', on_delete=models.CASCADE, related_name='roles_created', blank=True, null=True, db_column='created_by')
    updated_by = models.ForeignKey('Account.CustomUser', on_delete=models.CASCADE, related_name='roles_updated', blank=True, null=True, db_column='updated_by')
    objects = ServiceManager()
    class Meta:
        db_table = 'roles'

class parameter_master(models.Model):
    parameter_id = models.AutoField(primary_key=True)
    parameter_name =models.TextField(null=True,blank=True)
    parameter_value =models.TextField(null=True,blank=True)
    created_at = models.DateTimeField(null=True,blank=True,auto_now_add=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE,related_name='parameter_created_by',blank=True, null=True,db_column='created_by')
    updated_at = models.DateTimeField(null=True,blank=True,auto_now_add=True)
    updated_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE,related_name='parameter_updated_by',blank=True, null=True,db_column='updated_by')
    objects = ServiceManager()
    class Meta:
        db_table = 'parameter_master'
    def __str__(self):
        return self.parameter_name

class NodalMaster(models.Model):
    id = models.AutoField(primary_key=True)
    nodal_office_location = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.CharField(max_length=100, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.CharField(max_length=100, null=True, blank=True)
    objects = ServiceManager()
    class Meta:
        db_table = 'nodal_master'

class DepartmentMaster(models.Model):
    dept_id = models.AutoField(primary_key=True)
    dept_name = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.CharField(max_length=100, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.CharField(max_length=100, null=True, blank=True)
    objects = ServiceManager()
    class Meta:
        db_table = 'department_master'
        
class ServiceMaster(models.Model):
    ser_id = models.AutoField(primary_key=True)
    ser_name = models.CharField(max_length=100, null=True, blank=True)
    dept_id_id = models.ForeignKey('DepartmentMaster', on_delete=models.CASCADE, null=True, blank=True, related_name='dept_id_F', db_column="dept_id_id")
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.CharField(max_length=100, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.CharField(max_length=100, null=True, blank=True)
    objects = ServiceManager()
    class Meta:
        db_table = 'service_master'

class StatusMaster(models.Model):
    status_id = models.AutoField(primary_key=True)
    status_name = models.CharField(max_length=100, null=True, blank=True)
    is_active = models.IntegerField(default=1)  
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.CharField(max_length=100, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.CharField(max_length=100, null=True, blank=True)
    objects = ServiceManager()
    class Meta:
        db_table = 'status_master'

class DocumentMaster(models.Model):
    doc_id = models.AutoField(primary_key=True)
    doc_name = models.CharField(max_length=255, null=True, blank=True)
    doc_path = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100, null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.CharField(max_length=100, null=True, blank=True)
    objects = ServiceManager()
    class Meta:
        db_table = 'document_master'
        
# Transaction

class WorkflowDetail(models.Model):
    request_no = models.CharField(max_length=255, primary_key=True)  
    level = models.IntegerField(null=True, blank=True)
    user_id_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name='user_id_F', db_column='user_id_id')
    status = models.CharField(max_length=50, null=True, blank=True)
    action = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100, null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.CharField(max_length=100, null=True, blank=True)
    objects = ServiceManager()
    class Meta:
        db_table = 'workflow_details'

class LevelActionMapping(models.Model):
    id = models.AutoField(primary_key=True)
    action = models.CharField(max_length=100, null=True, blank=True)
    next_action = models.CharField(max_length=100, null=True, blank=True)
    level = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100, null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.CharField(max_length=100, null=True, blank=True)
    objects = ServiceManager()
    class Meta:
        db_table = 'level_action_mapping'
        
class ServiceMatrix(models.Model):
    id = models.AutoField(primary_key=True)  # Explicitly defining the id field
    ser_id_id = models.ForeignKey('ServiceMaster', on_delete=models.CASCADE, null=True, blank=True, related_name='ser_id_id_F', db_column='ser_id_id')
    level = models.IntegerField(null=True, blank=True)
    role_name = models.CharField(max_length=100, null=True, blank=True)
    action = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100, null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.CharField(max_length=100, null=True, blank=True)
    objects = ServiceManager()
    class Meta:
        db_table = 'service_matrix'

class CitizenDocument(models.Model):
    userdocumentid = models.AutoField(primary_key=True)       
    file_name = models.CharField(max_length=255, null=True, blank=True)  
    doc_id_id = models.ForeignKey('DocumentMaster', on_delete=models.CASCADE, null=True, blank=True, related_name='doc_id_id_F', db_column='doc_id_id')  
    created_at = models.DateTimeField(auto_now_add=True)           
    created_by = models.CharField(max_length=100, null=True, blank=True) 
    updated_at = models.DateTimeField(null=True, blank=True)                
    updated_by = models.CharField(max_length=100, null=True, blank=True)  
    objects = ServiceManager()
    class Meta:
        db_table = 'citizen_document'
        
class InternalUserDocument(models.Model):
    request_no_id = models.ForeignKey('WorkflowDetail', on_delete=models.CASCADE, null=True, blank=True, related_name='request_no_F', db_column='request_no_id') 
    file_name = models.CharField(max_length=255, null=True, blank=True)  
    created_at = models.DateTimeField(auto_now_add=True)             
    created_by = models.CharField(max_length=100, null=True, blank=True) 
    updated_at = models.DateTimeField(null=True, blank=True)               
    updated_by = models.CharField(max_length=100, null=True, blank=True) 
    objects = ServiceManager()
    class Meta:
        db_table = 'internal_user_document'

        
class Log(models.Model):
    log_text = models.TextField(null=True,blank=True)
    objects = ServiceManager()
    class Meta:
        db_table = 'logs'