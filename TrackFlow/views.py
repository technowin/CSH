from django.shortcuts import render
from Account.models import *
from Masters.models import *
import traceback
from Account.db_utils import callproc
from django.contrib import messages
# Create your views here.


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
    