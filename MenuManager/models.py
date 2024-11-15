from django.db import models
from Account.managers import ServiceManager
# Create your models here.


class MenuMaster(models.Model):
    menu_id = models.AutoField(primary_key=True)
    menu_name = models.CharField(max_length=50, null=True, blank=True)
    menu_action = models.CharField(max_length=50, null=True, blank=True)
    menu_is_parent = models.BooleanField(null=True, blank=True)
    menu_parent_id = models.IntegerField(null=True, blank=True)
    menu_order = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    is_sub_menu = models.BooleanField(null=True, blank=True)
    sub_menu = models.IntegerField(null=True, blank=True)
    is_sub_menu2 = models.BooleanField(null=True, blank=True)
    sub_menu2 = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    created_by = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True, auto_now=True)
    updated_by = models.TextField(null=True, blank=True)
    menu_icon = models.CharField(max_length=50, null=True, blank=True)
    objects = ServiceManager()
    class Meta:
        db_table = 'menu_master'


class RoleMenuMaster(models.Model):
    role_menu_id = models.AutoField(primary_key=True)
    role_id = models.CharField(max_length=50, null=True, blank=True)
    menu_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    created_by = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True, auto_now=True)
    updated_by = models.TextField(null=True, blank=True)
    objects = ServiceManager()
    class Meta:
        db_table = 'role_menu_master'


class UserMenuDetails(models.Model):
    user_menu_id = models.AutoField(primary_key=True)
    user_id = models.CharField(max_length=50, null=True, blank=True)
    menu_id = models.IntegerField(null=True, blank=True)
    role_id = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    created_by = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True, auto_now=True)
    updated_by = models.TextField(null=True, blank=True)
    objects = ServiceManager()
    class Meta:
        db_table = 'user_menu_details'
