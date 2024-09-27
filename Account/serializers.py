from rest_framework import serializers
from .models import CustomUser

class UserSerializer(serializers.ModelSerializer):
    # role_id = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = ['id', 'full_name', 'email','role_id','is_active']
    # def get_role_id(self, obj):
    #     if obj.role:
    #         if obj.role.role_name:
    #             return obj.role.role_name
    #         else:
    #             return None
    #     return None
class LoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField()
    device_token = serializers.CharField()

class RegistrationSerializer(serializers.Serializer):
    # id = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField()
    full_name = serializers.CharField()
    phone = serializers.CharField()
    is_active = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    role_id = serializers.CharField(allow_blank=True, allow_null=True, required=False)
