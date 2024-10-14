from django.shortcuts import render
from Account.models import *
from Masters.models import *
import traceback
from Account.db_utils import callproc
from django.contrib import messages
from CSH.encryption import *

# Create your views here.


def index(request):
    pre_url = request.META.get('HTTP_REFERER')
    header, data = [], []
    entity, type, name = '', '', ''
    try:
        if request.user.is_authenticated ==True:                
                global user
                user = request.user.id   
        if request.method == "GET":
            entity = request.GET.get('entity', '')
            type = request.GET.get('type', '')
            datalist1= callproc("stp_get_masters",[entity,type,'name',user])
            name = datalist1[0][0]
            header = callproc("stp_get_masters", [entity, type, 'header',user])
            rows = callproc("stp_get_masters",[entity,type,'data',user])
            data = []
            if (entity == 'wf'): 
                for row in rows:
                    encrypted_id = encrypt_parameter(str(row[0]))
                    data.append((encrypted_id,) + row[1:])
            else:data = rows
            
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),user])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally: 
         return render(request,'TrackFlow/index.html', {'entity':entity,'type':type,'name':name,'header':header,'data':data,'pre_url':pre_url})
    
def metrix_flow(request):
    docs = []
    try:
        if request.user.is_authenticated ==True:                
                global user
                user = request.user.id   
        if request.method == "GET":
            docs = document_master.objects.filter(is_active=1)
            
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),user])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally: 
         return render(request,'TrackFlow/metrix_flow.html', {'docs':docs})
    