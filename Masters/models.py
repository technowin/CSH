from django.db import models
from django.db import models
from Account.models import *
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
         
class roles(models.Model):
    id = models.AutoField(primary_key=True)
    role_name = models.TextField(null=True, blank=True)
    role_disc = models.TextField(null=True, blank=True)
    role_type = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True, auto_now=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='roles_created', blank=True, null=True, db_column='created_by')
    updated_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='roles_updated', blank=True, null=True, db_column='updated_by')
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

class nodal_master(models.Model):
    id = models.AutoField(primary_key=True)
    nodal_office_location = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.TextField(null=True, blank=True)
    objects = ServiceManager()
    class Meta:
        db_table = 'nodal_master'

class department_master(models.Model):
    dept_id = models.AutoField(primary_key=True)
    dept_name =  models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by =  models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by =  models.TextField(null=True, blank=True)
    objects = ServiceManager()
    class Meta:
        db_table = 'department_master'
        
class service_master(models.Model):
    ser_id = models.AutoField(primary_key=True)
    ser_name = models.TextField(null=True, blank=True)
    dept = models.ForeignKey(department_master, on_delete=models.CASCADE, null=True, blank=True, related_name='dept_ser_F')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by =  models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by =  models.TextField(null=True, blank=True)
    objects = ServiceManager()
    class Meta:
        db_table = 'service_master'

class status_master(models.Model):
    status_id = models.AutoField(primary_key=True)
    status_name = models.TextField(null=True, blank=True)
    status_type = models.TextField(null=True, blank=True)
    is_active = models.IntegerField(default=1)  
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.TextField(null=True, blank=True)
    objects = ServiceManager()
    class Meta:
        db_table = 'status_master'

class document_master(models.Model):
    doc_id = models.AutoField(primary_key=True)
    doc_name = models.TextField(null=True, blank=True)
    doc_subpath =models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.TextField(null=True, blank=True)
    is_active = models.IntegerField(default=1)
    mandatory = models.IntegerField(default=1)
    objects = ServiceManager()
    class Meta:
        db_table = 'document_master'

class application_form(models.Model):
    id = models.AutoField(primary_key=True)
    request_no = models.TextField(null=True, blank=True)
    name_of_premises = models.TextField(null=True, blank=True)
    plot_no = models.TextField(null=True, blank=True)
    sector_no = models.TextField(null=True, blank=True)
    node = models.TextField(null=True, blank=True)
    name_of_owner = models.TextField(null=True, blank=True)
    address_of_owner = models.TextField(null=True, blank=True)
    name_of_plumber = models.TextField(null=True, blank=True)
    license_no_of_plumber = models.TextField(null=True, blank=True)
    address_of_plumber = models.TextField(null=True, blank=True)
    plot_size = models.TextField(null=True, blank=True)
    no_of_flats = models.IntegerField(null=True, blank=True)
    no_of_shops = models.IntegerField(null=True, blank=True)
    septic_tank_size = models.TextField(null=True, blank=True)
    status = models.ForeignKey(status_master, on_delete=models.CASCADE, null=True, blank=True, related_name='status_form_F')
    comments = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.TextField(null=True, blank=True)
    objects = ServiceManager()
    class Meta:
        db_table = "application_form"     

class service_matrix(models.Model):
    id = models.AutoField(primary_key=True) 
    ser = models.ForeignKey(service_master, on_delete=models.CASCADE, null=True, blank=True, related_name='ser_id_F')
    level = models.IntegerField(null=True, blank=True)
    role = models.ForeignKey(roles, on_delete=models.CASCADE, null=True, blank=True, related_name='roles_matrix_F')
    action = models.TextField(null=True, blank=True)
    href = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.TextField(null=True, blank=True)
    objects = ServiceManager()
    class Meta:
        db_table = 'service_matrix'

class workflow_details(models.Model):
    id = models.AutoField(primary_key=True)
    request_no = models.TextField(null=True, blank=True)  
    level = models.IntegerField(null=True, blank=True)
    status = models.ForeignKey(status_master, on_delete=models.CASCADE, null=True, blank=True, related_name='status_flow_F')
    form_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name='user_flow_F', db_column='form_user_id')
    form_id = models.ForeignKey(application_form, on_delete=models.CASCADE, null=True, blank=True, related_name='form_id_F', db_column='form_id')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.TextField(null=True, blank=True)
    objects = ServiceManager()
    class Meta:
        db_table = 'workflow_details'

class workflow_history(models.Model):
    id = models.AutoField(primary_key=True)
    workflow_id = models.IntegerField(null=True, blank=True,db_column='workflow_id')
    request_no = models.TextField(null=True, blank=True)  
    level = models.IntegerField(null=True, blank=True)
    status = models.ForeignKey(status_master, on_delete=models.CASCADE, null=True, blank=True, related_name='status_hist_F')
    form_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name='user_hist_F', db_column='form_user_id')
    form_id = models.ForeignKey(application_form, on_delete=models.CASCADE, null=True, blank=True, related_name='hist_form_id_F', db_column='form_id')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.TextField(null=True, blank=True)
    objects = ServiceManager()
    class Meta:
        db_table = 'workflow_history'

class level_action(models.Model):
    id = models.AutoField(primary_key=True)
    action = models.TextField(null=True, blank=True)
    next_action = models.TextField(null=True, blank=True)
    level = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.TextField(null=True, blank=True)
    objects = ServiceManager()
    class Meta:
        db_table = 'level_action'

class citizen_document(models.Model):
    id = models.AutoField(primary_key=True) 
    user_id = models.IntegerField() 
    file_name = models.TextField(null=True, blank=True)
    filepath = models.CharField(max_length=1000, null=True, blank=True)  # Add this field
    document = models.ForeignKey(document_master, on_delete=models.CASCADE, null=True, blank=True, related_name='citizen_documents_f', db_column='doc_id_id')  
    created_at = models.DateTimeField(auto_now_add=True)           
    created_by = models.TextField(null=True, blank=True) 
    updated_at = models.DateTimeField(null=True, blank=True)                
    updated_by = models.TextField(null=True, blank=True)
    application_id = models.ForeignKey(application_form, on_delete=models.CASCADE, null=True, blank=True, related_name='application_id_F', db_column='application_id')   
    objects = ServiceManager()
    class Meta:
        db_table = 'citizen_document'
             
class internal_user_document(models.Model):
    id = models.AutoField(primary_key=True) 
    workflow = models.ForeignKey(workflow_details, on_delete=models.CASCADE, null=True, blank=True, related_name='workflow_intdoc_F') 
    file_name = models.TextField(null=True, blank=True)  
    file_path = models.TextField(null=True, blank=True)  
    created_at = models.DateTimeField(auto_now_add=True)             
    created_by = models.TextField(null=True, blank=True) 
    updated_at = models.DateTimeField(null=True, blank=True)               
    updated_by = models.TextField(null=True, blank=True) 
    objects = ServiceManager()
    class Meta:
        db_table = 'internal_user_document'

class Log(models.Model):
    log_text = models.TextField(null=True,blank=True)
    objects = ServiceManager()
    class Meta:
        db_table = 'logs'


class smstext(models.Model):
    id = models.AutoField(primary_key=True)
    template_name = models.TextField(null=True, blank=True) 
    template_id = models.TextField(null=True, blank=True)  
    sms_id_number = models.TextField(null=True, blank=True) 
    created_at = models.DateTimeField(auto_now_add=True) 

    class Meta:
        db_table = 'smstext'
        
class smslog(models.Model):
    mobile = models.CharField(max_length=20)  
    message = models.TextField(null=True, blank=True) 
    user_id = models.CharField(max_length=50) 
    content = models.TextField(null=True, blank=True) 
    status = models.CharField(max_length=20)  
    unique_id = models.CharField(max_length=50, null=True, blank=True) 
    content_type = models.CharField(max_length=50) 
    response_status = models.CharField(max_length=20)
    is_successful = models.BooleanField(default=False)  
    response_url = models.TextField(null=True, blank=True)  
    status_description = models.TextField(null=True, blank=True)  
    template_id = models.CharField(max_length=50)  
    created_at = models.DateTimeField(auto_now_add=True)  

    class Meta:
        db_table = 'smslog'

    