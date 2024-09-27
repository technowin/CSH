from django import forms

from Account.models import CustomUser



class RegistrationForm(forms.ModelForm):
    class Meta:
        model=CustomUser
        fields =['email','full_name','password']
    
    password = forms.CharField(widget=forms.PasswordInput)