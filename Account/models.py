# from django.db import models
# from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
# import bcrypt
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from .managers import ServiceManager



class CustomUserManager(BaseUserManager):
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        # user.password_text = password
        user.set_password(password)
        # user.encrypted_password = user.password
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, password, **extra_fields)
    
    def get_queryset(self):
        from .db_utils import get_service_db
        service_db = get_service_db()
        return super().get_queryset().using(service_db)

        
class CustomUser(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True)
    # title = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    # encrypted_password = models.CharField(max_length=225,null=True,blank=True)  # Adjust the max_length as needed
    phone = models.CharField(unique=True,max_length=255)
    first_time_login = models.IntegerField(default=1)  # 1 for True, 0 for False
    last_login = models.DateTimeField(default=timezone.now)
    # password_text = models.CharField(max_length=128)

    is_active = models.BooleanField(default=True)
    # is_staff = models.BooleanField(default=False)
    superior_id =  models.BigIntegerField(null=True, blank=True)
    role_id = models.BigIntegerField(null=True, blank=True)
    device_token = models.CharField(max_length=255, null=True, blank=True)
    objects = CustomUserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['full_name']  # Add any additional required fields
    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.phone


class roles(models.Model):
    id = models.AutoField(primary_key=True)
    role_name = models.TextField(null=True, blank=True)
    role_disc = models.TextField(null=True, blank=True)
    role_type = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True, auto_now=True)
    created_by = models.TextField(null=True, blank=True)
    updated_by = models.TextField(null=True, blank=True)
    objects = ServiceManager()
    class Meta:
        db_table = 'roles'

class user_dept_services(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.BigIntegerField(null=True, blank=True)
    department_id = models.BigIntegerField(null=True, blank=True)
    service_id = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    created_by = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True, auto_now=True)
    updated_by = models.TextField(null=True, blank=True)
    class Meta:
        db_table = 'user_dept_services'
    def __str__(self):
        return f'User {self.user_id} - Role {self.service_id}'
    
class OTPVerification(models.Model):
    mobile = models.TextField(null=True, blank=True)
    otp_text = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = ServiceManager()
    class Meta:
        db_table = 'otp_verification'
        
class password_storage(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE,related_name='user_id_repos',blank=True, null=True,db_column='user_id')
    passwordText =models.CharField(max_length=255,null=True,blank=True)
    objects = ServiceManager()
    class Meta:
        db_table = 'password_storage'

class error_log(models.Model):
    id = models.AutoField(primary_key=True)
    method =models.TextField(null=True,blank=True)
    error =models.TextField(null=True,blank=True)
    error_date = models.DateTimeField(null=True,blank=True,auto_now_add=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE,related_name='error_by',blank=True, null=True)
    objects = ServiceManager()
    class Meta:
        db_table = 'error_log'

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
    short_name = models.TextField(null=True, blank=True)
    dept = models.ForeignKey(department_master, on_delete=models.CASCADE, null=True, blank=True, related_name='dept_ser_F')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by =  models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by =  models.TextField(null=True, blank=True)
    citizen_page = models.TextField(null=True, blank=True)
    internal_page = models.TextField(null=True, blank=True)
    objects = ServiceManager()
    class Meta:
        db_table = 'service_master'

class common_model(models.Model):
    name = models.CharField(max_length=255)
    id1 =models.CharField(max_length=255)
    def __str__(self):
        return self.id1    
    class Meta:
        abstract = True


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
        
class SessionActivityLog(models.Model):
    """
    Logs session binding and suspicious activity.
    No FK intentionally (audit table).
    """

    user_id = models.CharField(max_length=50, null=True, blank=True)
    user_type = models.CharField(
        max_length=20,
        choices=(('admin', 'Admin'), ('citizen', 'Citizen')),
        null=True,
        blank=True
    )

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent_hash = models.CharField(max_length=256, null=True, blank=True)
    stored_user_agent_hash = models.CharField(max_length=256, null=True, blank=True)
    stored_ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    user_agent = models.TextField(null=True, blank=True)
    stored_user_agent = models.TextField(null=True, blank=True)

    action = models.CharField(max_length=100)  
    # examples:
    # session_created, session_verified, mismatch_detected, forced_logout

    remarks = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tbl_session_activity_log'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user_type} | {self.user_id} | {self.action}"
