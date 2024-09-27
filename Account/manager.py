from django.contrib.auth.base_user import BaseUserManager

# class UserManager(BaseUserManager):
#     def create_user(self,Email,PasswordText =None,**extra_fields):
#         if not self.normalize_email(Email):
#             raise ValueError("Phone Number Is Required")
#         CustomUser = self.model(Email =Email,**extra_fields)
#         CustomUser.set_password(PasswordText)
#         CustomUser.save(using=self.db)
#         return CustomUser
    
#     def create_superuser(self,Email,password ,**extra_fields):
#         # extra_fields.setdefault("is_staff",True)
#         # extra_fields.setdefault("is_superuser",True)
#         # extra_fields.setdefault("is_active",True)
#         print(password)
#         return self.create_user(Email,password,**extra_fields)
        
       