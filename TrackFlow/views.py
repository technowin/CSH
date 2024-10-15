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
    name = ''
    try:
        if request.user.is_authenticated ==True:                
                global user
                user = request.user.id   
        if request.method == "GET":
            datalist1= callproc("stp_get_masters",['wf','','name',user])
            name = datalist1[0][0]
            header = callproc("stp_get_masters", ['wf','','header',user])
            rows = callproc("stp_get_masters",['wf','','data',user])
            for row in rows:
                encrypted_id0 = encrypt_parameter(str(row[0]))
                encrypted_id1 = encrypt_parameter(str(row[1]))
                data.append((encrypted_id0,encrypted_id1) + row[2:])
        context = {'name':name,'header':header,'data':data,'pre_url':pre_url}
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),user])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally: 
         return render(request,'TrackFlow/index.html', context)
    
def matrix_flow(request):
    docs,label,input = [],[],[]
    form_id,context  = '',''
    try:
        if request.user.is_authenticated ==True:                
                global user
                user = request.user.id   
        if request.method == "GET":
            wf_id = decrypt_parameter(wf_id) if (wf_id := request.GET.get('wf', '')) else ''
            form_id = decrypt_parameter(form_id) if (form_id := request.GET.get('af', '')) else ''
            docs = document_master.objects.filter(is_active=1)
            label = callproc("stp_get_masters", ['fm','','header',form_id])
            label = [l[0] for l in label]
            input = callproc("stp_get_masters",['fm','','data',form_id])
            fields = list(zip(label, input[0]))
            context = {'docs':docs,'fields': fields}
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),user])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally: 
         return render(request,'TrackFlow/metrix_flow.html', context)
    