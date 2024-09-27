from django.contrib import admin

from Account.models import *
from django.contrib.sessions.models import Session
import pprint
# Register your models here.
# admin.site.register(SignUpModel)
# admin.site.register(LoginModel)

class SessionAdmin(admin.ModelAdmin):
    def _session_data(self,obj):
        return pprint.pformat(obj.get_decoded()).replace('\n','<br>\n')
    _session_data.allow_tags=True
    list_display=['session_key','_session_data','expire_date']
    readonly_fields=['_session_data']
    exclude=['session_data']
    

admin.site.register(Session,SessionAdmin)