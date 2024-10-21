from datetime import datetime
from django.http import JsonResponse
from django.shortcuts import render
from Account.models import *
from Masters.models import *
import traceback
from Account.db_utils import callproc
from django.contrib import messages
from CSH.encryption import *
import os
from CSH.settings import *
from django.contrib.auth.decorators import login_required
# Create your views here.

@login_required 
def index(request):
    pre_url = request.META.get('HTTP_REFERER')
    header, data = [], []
    name = ''
    try:
        if request.user.is_authenticated ==True:                
                global user
                user = request.user.id    
                role_id = request.user.role_id
        if request.method == "GET":
            datalist1= callproc("stp_get_masters",['wf','','name',user])
            name = datalist1[0][0]
            header = callproc("stp_get_masters", ['wf','','header',user])
            rows = callproc("stp_get_masters",['wf','','data',user])
            for row in rows:
                encrypted_id0 = encrypt_parameter(str(row[0]))
                encrypted_id1 = encrypt_parameter(str(row[1]))
                data.append((encrypted_id0,encrypted_id1) + row[2:])
        context = {'role_id':role_id,'name':name,'header':header,'data':data,'pre_url':pre_url}
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),user])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally: 
         return render(request,'TrackFlow/index.html', context)

@login_required    
def matrix_flow(request):
    docs,label,input,data = [],[],[],[]
    form_id,context  = '',''
    try:
        if request.user.is_authenticated ==True:                
                global user,role
                user = request.user.id   
                role_id = request.user.role_id   
        if request.method == "GET":
            wf_id = decrypt_parameter(wf_id) if (wf_id := request.GET.get('wf', '')) else ''
            form_id = decrypt_parameter(form_id) if (form_id := request.GET.get('af', '')) else ''
            ac = request.GET.get('ac', '')
            subordinates = callproc("stp_get_subordinates",[form_id,user])
            user_list = callproc("stp_get_dropdown_values",['user'])
            citizen_docs = citizen_document.objects.filter(application_id=form_id) 
            for doc_master in document_master.objects.all():
                matching_doc = citizen_docs.filter(document=doc_master).first()
                doc_entry = {'doc_name': doc_master.doc_name,'file_path': None,'file_name': None}
                if matching_doc and matching_doc.filepath:
                    full_filepath = os.path.join(MEDIA_ROOT, matching_doc.filepath)
                    file_name = os.path.basename(full_filepath)
                    if os.path.exists(full_filepath):
                        encrypted_path = encrypt_parameter(matching_doc.filepath)
                        doc_entry['file_path'] = encrypted_path
                        doc_entry['file_name'] = file_name
                docs.append(doc_entry)
            label = callproc("stp_get_masters", ['fm','','header',form_id])
            label = [l[0] for l in label]
            input = callproc("stp_get_masters",['fm','','data',form_id])
            fields = list(zip(label, input[0]))
            header = callproc("stp_get_masters", ['iud','','header',wf_id])
            rows = callproc("stp_get_masters",['iud','','data',wf_id])
            for row in rows:
                if os.path.exists(os.path.join(MEDIA_ROOT, str(row[4]))):
                    encrypted_id = encrypt_parameter(str(row[4]))
                else: encrypted_id = None
                new_row = row[:4] + (encrypted_id,)
                data.append(new_row)
            header1 = callproc("stp_get_masters", ['iuc','','header',wf_id])
            data1 = callproc("stp_get_masters",['iuc','','data',wf_id])
            context = {'role_id':role_id,'docs':docs,'fields': fields,'header': header,'data': data,'header1': header1,
                       'data1': data1,'subordinates':subordinates,'user_list':user_list,'ac':ac,
                       'wf_id':encrypt_parameter(wf_id),'form_id': encrypt_parameter(form_id)}
        if request.method == "POST":
            response = None
            wf_id = decrypt_parameter(wf_id) if (wf_id := request.POST.get('wf_id', '')) else ''
            workflow_instance = workflow_details.objects.get(id=wf_id)
            files = request.FILES.getlist('files[]')
            comment =  request.POST.get('comment', '')
            if comment!='':
                internal_user_comments.objects.create(
                        workflow=workflow_instance, comments=comment,
                        created_at=datetime.now(),created_by=str(user),updated_at=datetime.now(),updated_by=str(user)
                )  
            response = f"Your comment has been submitted: '{comment}'"
           
           
            for file in files:
                role = roles.objects.get(id=role_id)
                sub_path = f'{role.role_name}/user_{user}/{file.name}'
                full_path = os.path.join(MEDIA_ROOT, sub_path)
                folder_path = os.path.dirname(full_path)
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path, exist_ok=True)
                file_exists_in_folder = os.path.exists(full_path)
                file_exists_in_db = internal_user_document.objects.filter(file_path=sub_path).exists()
                if file_exists_in_folder or file_exists_in_db:
                    document = internal_user_document.objects.filter(file_path=sub_path).first()
                    document.updated_at = datetime.now()
                    document.updated_by = str(user)
                    document.save()
                    with open(full_path, 'wb+') as destination:
                        for chunk in file.chunks():
                            destination.write(chunk)
                    response =  f"File '{file.name}' has been updated."
                else:
                    with open(full_path, 'wb+') as destination:
                        for chunk in file.chunks():
                            destination.write(chunk)
                    internal_user_document.objects.create(
                        workflow=workflow_instance, file_name=file.name,file_path=sub_path,
                        created_at=datetime.now(),created_by=str(user),updated_at=datetime.now(),updated_by=str(user)
                    )  
                    response =  f"File '{file.name}' has been inserted."
            if response:
                return JsonResponse(response, safe=False)
             
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),user])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally: 
         if request.method == "GET":
            return render(request,'TrackFlow/metrix_flow.html', context)
    