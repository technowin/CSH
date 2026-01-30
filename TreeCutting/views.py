from datetime import datetime
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render,redirect
from Account.models import *
from Masters.models import *
from TreeCutting.models import *
import traceback
from Account.db_utils import callproc
from django.contrib import messages
from django.conf import settings
from CSH.encryption import *
import os
from CSH.settings import *
from django.contrib.auth.decorators import login_required
import openpyxl
import mimetypes
from openpyxl.styles import Font, Border, Side
import pandas as pd
import calendar
from django.utils import timezone
from datetime import timedelta
from django.http import Http404
# from DrainageConnection.models import *

# Create your views here.
import logging
logger = logging.getLogger(__name__)
from CSH.access_control import no_direct_access

@login_required 
@no_direct_access
def index_tc(request):
    pre_url = request.META.get('HTTP_REFERER')
    header, data = [], []
    name = ''
    try:
        if not request.user.is_authenticated and not request.session.get('username'):
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('citizenLoginAccount')
        
        if request.user.is_authenticated ==True:                
                global user,role_id
                user = request.user.id    
                role_id = request.user.role_id
        if request.method == "GET":
            datalist1= callproc("stp_get_masters",['wf','','name',user])
            name = datalist1[0][0]
            header = callproc("stp_get_masters", ['wf','','header',user])
            rows = callproc("stp_get_masters",['wf','','data',user])
            for row in rows:
                id = encrypt_parameter(str(row[0]))
                form_id = encrypt_parameter(str(row[1]))    
                data.append((id,form_id) + row[2:])
        context = {'role_id':role_id,'name':name,'header':header,'data':data,'user_id':user,'pre_url':pre_url}
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),user])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally: 
         return render(request,'TreeCutting/index.html', context)

@login_required 
@no_direct_access   
def matrix_flow_tc(request):
    docs,label,input,data = [],[],[],[]
    form_id,context,wf_id,sf,f,sb,rb,rb1  = '','','','','','','',''
    try:
        if not request.user.is_authenticated and not request.session.get('username'):
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('citizenLoginAccount')
        
        if request.user.is_authenticated ==True:                
                global user,role_id
                user = request.user.id   
                role_id = request.user.role_id   
        if request.method == "GET":
            wf_id = decrypt_parameter(wf_id) if (wf_id := request.GET.get('wf', '')) else ''
            form_id = decrypt_parameter(form_id) if (form_id := request.GET.get('af', '')) else ''
            workflow = workflow_details.objects.get(id=wf_id) 
            matrix = service_matrix.objects.get(level=workflow.level)
            act_comp = status_master.objects.filter(level=workflow.level,status_id=workflow.status_id).exists()
            
            doc_ids = [16, 17]
            existing_docs = citizen_document.objects.filter( document_id__in=doc_ids, application_id=form_id).values_list('document_id', flat=True)

            if all(doc_id in existing_docs for doc_id in doc_ids):
                checkUpload = 1 
            else:
                checkUpload = 0 
            
            ac = request.GET.get('ac', '')
            f = request.GET.get('f', '')
            sf = request.GET.get('sf', '')
            sb = request.GET.get('sb', '')
            rb = request.GET.get('rb', '')
            rb1 = request.GET.get('rb1', '')
            if sf and sf !='':
                r = callproc("stp_update_sendforward",[wf_id,form_id,sf,user])
                if r[0][0] == 'success':
                    messages.success(request, "Send Forward successfully !!")
                elif r[0][0] == 'incomplete':
                    messages.error(request, 'Before forwarding, please complete the necessary actions.')
                    return redirect(f'/matrix_flow_tc?wf={encrypt_parameter(wf_id)}&af={encrypt_parameter(form_id)}&ac={ac}')
                else: messages.error(request, 'Oops...! Something went wrong!')
                return redirect(f'/index_tc')
            if f and f !='':
                r = callproc("stp_update_forward",[wf_id,form_id,f,user])
                if r[0][0] == 'success':
                    messages.success(request, "Forwarded successfully !!")
                else: messages.error(request, 'Oops...! Something went wrong!')
                return redirect(f'/matrix_flow_tc?wf={encrypt_parameter(wf_id)}&af={encrypt_parameter(form_id)}&ac={ac}')
            if sb and sb !='':
                r = callproc("stp_update_sendback",[wf_id,form_id,user])
                if r[0][0] == 'success':
                    messages.success(request, "Sendback successfully !!")
                elif r[0][0] == 'wrongsendback':
                    messages.error(request, 'You cannot send it back in the first stage itself.')
                    return redirect(f'/matrix_flow_tc?wf={encrypt_parameter(wf_id)}&af={encrypt_parameter(form_id)}&ac={ac}')
                elif r[0][0] == 'multisendback':
                    messages.error(request, 'Consecutive send-backs are not permitted.')
                    return redirect(f'/matrix_flow_tc?wf={encrypt_parameter(wf_id)}&af={encrypt_parameter(form_id)}&ac={ac}')
                else: messages.error(request, 'Oops...! Something went wrong!')
                return redirect(f'/index_tc')
            if rb and rb !='':
                r = callproc("stp_update_rollback",[wf_id,form_id,user])
                if r[0][0] == 'success':
                    messages.success(request, "Rollback successfully !!")
                elif r[0][0] == 'wrongrollback':
                    messages.error(request, 'You cannot roll it back in the first stage itself.')
                    return redirect(f'/matrix_flow_tc?wf={encrypt_parameter(wf_id)}&af={encrypt_parameter(form_id)}&ac={ac}')
                elif r[0][0] == 'multirollback':
                    messages.error(request, 'Consecutive roll-backs are not permitted.')
                    return redirect(f'/matrix_flow_tc?wf={encrypt_parameter(wf_id)}&af={encrypt_parameter(form_id)}&ac={ac}')
                else: messages.error(request, 'Oops...! Something went wrong!')
                return redirect(f'/index_tc')
            if rb1 and rb1 !='':
                r = callproc("stp_update_rollback1",[wf_id,form_id,user])
                if r[0][0] == 'success':
                    messages.success(request, "Rollback successfully !!")
                elif r[0][0] == 'multirollback':
                    messages.error(request, 'Consecutive roll-backs are not permitted.')
                    return redirect(f'/matrix_flow_tc?wf={encrypt_parameter(wf_id)}&af={encrypt_parameter(form_id)}&ac={ac}')
                else: messages.error(request, 'Oops...! Something went wrong!')
                return redirect(f'/index_tc')
            subordinates = callproc("stp_get_subordinates",[form_id,user])
            user_list = callproc("stp_get_dropdown_values",['marked_for'])
            reject_reasons = callproc("stp_get_dropdown_values",['reject_reasons'])
            citizen_docs = citizen_document.objects.filter(application_id=form_id) 
            for doc_master in document_master.objects.all().exclude(doc_id=18):
                matching_doc = citizen_docs.filter(document=doc_master).first()
                doc_entry = {'doc_name': doc_master.doc_name,'file_path': None,'file_name': None,'id': None,'correct': None,'comment': None}
                if matching_doc and matching_doc.filepath:
                    full_filepath = os.path.join(MEDIA_ROOT, matching_doc.filepath)
                    file_name = os.path.basename(full_filepath)
                    if os.path.exists(full_filepath):
                        doc_entry['file_path'] = encrypt_parameter(matching_doc.filepath)
                        doc_entry['file_name'] = file_name
                        doc_entry['id'] =  str(matching_doc.id)
                        doc_entry['correct'] =  str(matching_doc.correct_mark)
                        doc_entry['comment'] =  str(matching_doc.comment or '')
                docs.append(doc_entry)
            label = callproc("stp_get_masters", ['fm','','header',form_id])
            label = [l[0] for l in label]
            input = callproc("stp_get_masters",['fm','','data',form_id])
            fields = list(zip(label, input[0]))
            header = callproc("stp_get_masters", ['iud','','header',wf_id])
            rows = callproc("stp_get_masters",['iud','','data',wf_id])
            for row in rows:
                if os.path.exists(os.path.join(MEDIA_ROOT, str(row[5]))):
                    encrypted_id = encrypt_parameter(str(row[5]))
                else: encrypted_id = None
                new_row = row[:5] + (encrypted_id,)
                data.append(new_row)
            header1 = callproc("stp_get_masters", ['iuc','','header',wf_id])
            data1 = callproc("stp_get_masters",['iuc','','data',wf_id])
            down_chklst = encrypt_parameter("sample.pdf")
            down_insp = encrypt_parameter("sample.pdf")
            context = {'role_id':role_id,'user_id':request.user.id,'docs':docs,'fields': fields,'header': header,'data': data,'header1': header1,
                       'data1': data1,'subordinates':subordinates,'user_list':user_list,'ac':ac,'wf_id':encrypt_parameter(wf_id),
                       'form_id': encrypt_parameter(form_id),'workflow':workflow,'reject_reasons':reject_reasons,'matrix':matrix,
                       'down_chklst':down_chklst,'down_insp':down_insp,'act_comp':act_comp,'checkUpload':checkUpload}
        if request.method == "POST":
            response = None
            wf_id = decrypt_parameter(wf_id) if (wf_id := request.POST.get('wf_id', '')) else ''
            form_id = decrypt_parameter(form_id) if (form_id := request.POST.get('form_id', '')) else ''
            wf = workflow_details.objects.get(id=wf_id)
            form_user_id = wf.form_user_id
            files = request.FILES.getlist('files[]')
            # filess = request.FILES.getlist('filess[]')
            comment =  request.POST.get('comment', '')
            ser= request.session.get('service_db','default')
            id1 = request.POST.get('id1', None)
            id2 = request.POST.get('id2', None)
            id3 = request.POST.get('id3', None)
            if comment!='':
                internal_user_comments.objects.create(
                        workflow=wf, comments=comment,
                        created_at=datetime.now(),created_by=str(user),updated_at=datetime.now(),updated_by=str(user)
                )  
                response = f"Your comment has been submitted: '{comment}'"
            for file in files:
                 response =  internal_docs_upload(file,role_id,user,wf,ser,'')
            
            filess = request.FILES.getlist('filess[]')

            if len(filess) >= 1:
                file1 = filess[0]

                if len(filess) > 1:
                    file2 = filess[1]
                else:
                    file2 = None

                response1 = internal_docs_upload(file1, role_id, user, wf, ser, '')
                file_resp = citizen_docs_upload(file1, form_user_id, form_id, user, ser, id1)
                
                response2 = None 
                
                if file2:
                    response2 = internal_docs_upload(file2, role_id, user, wf, ser, '')
                    file_resp = citizen_docs_upload(file2, form_user_id, form_id, user, ser, id2)

                response = response1 or response2
                    
            if response:
                return JsonResponse(response, safe=False)

            Refusalfile = request.FILES.get('file')
            response = None

            if Refusalfile:
                
                response3 = internal_docs_upload(Refusalfile, role_id, user, wf, ser, 'Refusal Document')
                refusal_file_resp = citizen_docs_upload(Refusalfile, form_user_id, form_id, user, ser, id3)
                response = response3

            if response:
                return JsonResponse(response, safe=False)
            
            ref = decrypt_parameter(matrix_ref) if (matrix_ref := request.POST.get('matrix_ref', '')) else ''
            ac = decrypt_parameter(ac) if (ac := request.POST.get('ac', '')) else ''
            status =  request.POST.get('btnclk', '')
            if status.isdigit():
                status = int(status)
                
                if (status == 3 or status == 4) and (ref == 'scrutiny'):
                    doc_ids = request.POST.getlist('doc_ids')
                    rej_res = request.POST.get('rej_res')
                    if rej_res!='' and status in [4]:
                        internal_user_comments.objects.create(
                                workflow=wf, comments=rej_res,
                                created_at=datetime.now(),created_by=str(user),updated_at=datetime.now(),updated_by=str(user)
                        )  
                    for doc_id in doc_ids:
                        if doc_id !='':
                            doc_id = decrypt_parameter(doc_id)
                            correct = request.POST.get(f"correct_{doc_id}")
                            incorrect = request.POST.get(f"incorrect_{doc_id}")
                            rej_com = request.POST.get(f"reject_comment_{doc_id}")
                            r = callproc("stp_post_citizen_scrutiny", [doc_id,correct,incorrect,rej_com,user])
                    r1 = callproc("stp_post_scrutiny", [wf_id,form_id,status,ref,ser,rej_res,user])
                    if r1[0][0] not in (""):
                        messages.success(request, str(r1[0][0]))
                    else: messages.error(request, 'Oops...! Something went wrong!')
                    
                    # code to update api_data
                    
                    if status == 4:
                        
                        dataAPI = api_data.objects.filter(form_id=form_id, form_user_id=form_user_id, workflow_id=wf_id).first()
                        
                        if dataAPI:
                            
                            request.session['userId'] = dataAPI.user_id
                            request.session['trackId'] = dataAPI.track_id
                            request.session['serviceId'] = dataAPI.service_id
                            request.session['applicationId'] = dataAPI.application_no
                            request.session['application_status'] = '5'
                            request.session['remarks'] = rej_res
                            request.session['form_id'] = dataAPI.form_id
                            request.session['form_user_id'] = dataAPI.form_user_id
                            request.session['workflow_id'] = dataAPI.workflow_id
                            request.session['phone_number'] = dataAPI.mobile_no
                            
                            from Account.views import upd_citizen
                            upd_citizen(request)
                            
                elif status == 5 and ref == 'inspection':
                    cheklist_upl_file = request.FILES.get('cheklist_upl_file')
                    inspection_upl_file = request.FILES.get('inspection_upl_file')
                    if cheklist_upl_file and inspection_upl_file:
                        file_resp = internal_docs_upload(cheklist_upl_file,role_id,user,wf,ser,'Checklist')
                        file_resp = internal_docs_upload(inspection_upl_file,role_id,user,wf,ser,'Inspection')
                    r = callproc("stp_post_workflow", [wf_id,form_id,status,ref,ser,user,''])
                    if r[0][0] not in (""):
                        messages.success(request, str(r[0][0]))
                    else: messages.error(request, 'Oops...! Something went wrong!')
                elif status == 6 and ref == 'public_notice':
                    notice_upl_file = request.FILES.get('notice_upl_file')
                    objection_upl_file = request.FILES.get('objection_upl_file')
                    if notice_upl_file and objection_upl_file:
                        file_resp = internal_docs_upload(notice_upl_file,role_id,user,wf,ser,'Public Notice')
                        file_resp = internal_docs_upload(objection_upl_file,role_id,user,wf,ser,'Objection')
                    r = callproc("stp_post_workflow", [wf_id,form_id,status,ref,ser,user,''])
                    if r[0][0] not in (""):
                        messages.success(request, str(r[0][0]))
                    else: messages.error(request, 'Oops...! Something went wrong!')
                elif status == 7 and ref == 'department_proposal':
                    DepProposal_upl_file = request.FILES.get('DepProposal_upl_file')
                    if DepProposal_upl_file:
                        file_resp = internal_docs_upload(DepProposal_upl_file,role_id,user,wf,ser,'Department Proposal')
                    r = callproc("stp_post_workflow", [wf_id,form_id,status,ref,ser,user,''])
                    if r[0][0] not in (""):
                        messages.success(request, str(r[0][0]))
                    else: messages.error(request, 'Oops...! Something went wrong!')
                elif status == 10 and ref == 'letter_of_payment':
                    letOfPay_upl_file = request.FILES.get('letOfPay_upl_file')
                    plantOfLetter_upl_file = request.FILES.get('plantOfLetter_upl_file')
                    if letOfPay_upl_file and plantOfLetter_upl_file:
                        file_resp = internal_docs_upload(letOfPay_upl_file,role_id,user,wf,ser,'Letter of Payment')
                        file_resp = internal_docs_upload(plantOfLetter_upl_file,role_id,user,wf,ser,'Plantation Letter')
                    r = callproc("stp_post_workflow", [wf_id,form_id,status,ref,ser,user,''])
                    fui = workflow_details.objects.filter(id=wf_id).first()
                    form_user_id = fui.form_user_id
                    file_resp_1 = citizen_docs_upload(letOfPay_upl_file,form_user_id,form_id,user, ser, 13)
                    file_resp_2 = citizen_docs_upload(plantOfLetter_upl_file, form_user_id, form_id, user, ser, 15)
                    if r[0][0] not in (""):
                        messages.success(request, str(r[0][0]))
                    else: messages.error(request, 'Oops...! Something went wrong!')
                elif status == 13 and ref == 'certificate':
                    iss_remark = request.POST.get('iss_remark')
                    if iss_remark!='':
                        internal_user_comments.objects.create(
                                workflow=wf, comments=iss_remark,
                                created_at=datetime.now(),created_by=str(user),updated_at=datetime.now(),updated_by=str(user)
                        )  
                    certificate_upl_file = request.FILES.get('certificate_upl_file')
                    if certificate_upl_file:
                        file_resp = internal_docs_upload(certificate_upl_file,role_id,user,wf,ser,'Issue Certificate')
                    r = callproc("stp_post_workflow", [wf_id,form_id,status,ref,ser,user,iss_remark])
                    fui = workflow_details.objects.filter(id=wf_id).first()
                    form_user_id = fui.form_user_id
                    file_resp = citizen_docs_upload(certificate_upl_file,form_user_id,form_id,user,ser, 14)
                    if r[0][0] not in (""):
                        messages.success(request, str(r[0][0]))
                    else: messages.error(request, 'Oops...! Something went wrong!')
                else:
                    f_remark = request.POST.get('f_remark')
                    if f_remark!='' and status in [8, 9, 11, 12]:
                        internal_user_comments.objects.create(
                                workflow=wf, comments=f_remark,
                                created_at=datetime.now(),created_by=str(user),updated_at=datetime.now(),updated_by=str(user)
                        ) 
                    r = callproc("stp_post_workflow", [wf_id,form_id,status,ref,ser,user,f_remark])
                    if r[0][0] not in (""):
                        messages.success(request, str(r[0][0]))
                    else: messages.error(request, 'Oops...! Something went wrong!')
                    
                    if status == 11:
                        
                        dataAPI = api_data.objects.filter(form_id=form_id, form_user_id=form_user_id, workflow_id=wf_id).first()
                        
                        if dataAPI:
                            
                            request.session['userId'] = dataAPI.user_id
                            request.session['trackId'] = dataAPI.track_id
                            request.session['serviceId'] = dataAPI.service_id
                            request.session['applicationId'] = dataAPI.application_no
                            request.session['application_status'] = '4'
                            request.session['remarks'] = f_remark
                            request.session['form_id'] = dataAPI.form_id
                            request.session['form_user_id'] = dataAPI.form_user_id
                            request.session['workflow_id'] = dataAPI.workflow_id
                            request.session['phone_number'] = dataAPI.mobile_no
                            
                            from Account.views import upd_citizen
                            upd_citizen(request)
                            
                    if status == 12 or status == 9:
                        
                        dataAPI = api_data.objects.filter(form_id=form_id, form_user_id=form_user_id, workflow_id=wf_id).first()
                        
                        if dataAPI:
                            
                            request.session['userId'] = dataAPI.user_id
                            request.session['trackId'] = dataAPI.track_id
                            request.session['serviceId'] = dataAPI.service_id
                            request.session['applicationId'] = dataAPI.application_no
                            request.session['application_status'] = '5'
                            request.session['remarks'] = f_remark
                            request.session['form_id'] = dataAPI.form_id
                            request.session['form_user_id'] = dataAPI.form_user_id
                            request.session['workflow_id'] = dataAPI.workflow_id
                            request.session['phone_number'] = dataAPI.mobile_no
                            
                            from Account.views import upd_citizen
                            upd_citizen(request)
                            
                    
                    
                return redirect(f'/matrix_flow_tc?wf={encrypt_parameter(wf_id)}&af={encrypt_parameter(form_id)}&ac={ac}')
                
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),user])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally: 
         if request.method == "GET" and sf == '' and f == '' and sb == ''and rb == '' and rb1 == '':
            return render(request,'TreeCutting/metrix_flow.html', context)

def internal_docs_upload(file,role_id,user,wf,ser,name1):
    file_resp = None
    role = roles.objects.get(id=role_id)
    service = service_master.objects.using("default").get(ser_id=ser)
    sub_path = f'{service.ser_name}/{role.role_name}/user_{user}/workflow_{str(wf.id)}/{file.name}'
    full_path = os.path.join(MEDIA_ROOT, sub_path)
    folder_path = os.path.dirname(full_path)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path, exist_ok=True)
    file_exists_in_folder = os.path.exists(full_path)
    file_exists_in_db = internal_user_document.objects.filter(file_path=sub_path,workflow=wf,name=name1).exists()
    if file_exists_in_db:
        document = internal_user_document.objects.filter(file_path=sub_path,workflow=wf,name=name1).first()
        document.updated_at = datetime.now()
        document.updated_by = str(user)
        document.name=name1
        document.save()
        with open(full_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        if name1 =='':
            file_resp =  f"File has been updated."
        else: file_resp =  f"File '{file.name}' has been updated."
        
    else:
        with open(full_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        internal_user_document.objects.create(
            workflow=wf, file_name=file.name,file_path=sub_path,name=name1,
            created_at=datetime.now(),created_by=str(user),updated_at=datetime.now(),updated_by=str(user)
        )  
        if name1 =='':
            file_resp =  f"File has been inserted."
        else: file_resp =  f"File '{file.name}' has been inserted."
    return file_resp

def citizen_docs_upload(file,user,form_id,created_by,ser, doc_id1):
    file_resp = None
    # if status == 10:
    #     doc = document_master.objects.get(doc_id=13)
    # else:
    #     doc = document_master.objects.get(doc_id=14)
    
    doc = document_master.objects.get(doc_id=doc_id1)
        
    app_form = application_form.objects.get(id=form_id)
    service = service_master.objects.using("default").get(ser_id=ser)
    sub_path = f'{service.ser_name}/User/user_{user}/application_{form_id}/document_{doc.doc_id}/{file.name}'
    full_path = os.path.join(MEDIA_ROOT, sub_path)
    folder_path = os.path.dirname(full_path)
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path, exist_ok=True)
    file_exists_in_folder = os.path.exists(full_path)
    file_exists_in_db = citizen_document.objects.filter(filepath=sub_path).exists()
    if file_exists_in_db:
        document = citizen_document.objects.filter(filepath=sub_path).first()
        document.updated_at = datetime.now()
        document.updated_by = str(user)
        document.save()
        with open(full_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        file_resp =  f"File '{file.name}' has been updated."
    else:
        with open(full_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        citizen_document.objects.create(
            user_id=user,file_name=file.name,filepath=sub_path,
            document=doc,application_id=app_form,
            created_by=str(created_by),updated_by=str(created_by),
            created_at=datetime.now(),updated_at=datetime.now()
        )
       
        file_resp =  f"File '{file.name}' has been inserted."
    return file_resp

@no_direct_access
def applicationFormIndexTC(request):
    try:
        if not request.session.get('user_id') or not request.session.get('phone_number'):
            # Set session expiry flag for middleware
            request.session['_session_expired'] = True
            
            # Clear user-specific session data
            user_session_keys = ['phone_number', 'user_id', 'role_id', 'full_name']
            for key in user_session_keys:
                if key in request.session:
                    del request.session[key]
            
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('citizenLoginAccount')
        
        if request.method == "GET":
            phone_number = request.session["phone_number"]

            if phone_number:
                user = get_object_or_404(CustomUser, phone=phone_number, role_id=2)
                user_id = user.id
            else:
                user_id = None

            new_id = 1
            countRefusedDocument = None
            refused_id = None
            encrypted_new_id = encrypt_parameter(str(new_id))

            getApplicantData = []
             
            
            applicationIndex = callproc("stp_getFormDetailsForTC", [user_id])

            for items in applicationIndex:
                encrypted_id = encrypt_parameter(str(items[1]))
                item = {
                    "srno": items[0],
                    "id": encrypted_id,
                    "request_no": items[2],
                    "name_of_applicant": items[3],
                    "status": items[4],
                    "comments": items[5],
                }

                getApplicantData.append(item)
                
                if items[4] == 'Committee Refusal':
                    
                    refused_id = items[1]
            
            countRefusedDocumentId = callproc("stp_getRefusedDocumentDetails", [refused_id])
            countRefusedDocument = countRefusedDocumentId[0][0] if countRefusedDocumentId else 0
            
            return render(
                request,
                "TreeCutting/TreeCuttingIndex.html",
                {"data": getApplicantData, "encrypted_new_id": {encrypted_new_id}, "countRefusedDocument": countRefusedDocument},
            )

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), ""])
        logger.error(f"Error in applicationFormIndexTC: {str(e)}")

    # finally:
    #     return render(
    #         request,
    #         "TreeCutting/TreeCuttingIndex.html",
    #         {"data": getApplicantData, "encrypted_new_id": {encrypted_new_id}, "countRefusedDocument": countRefusedDocument},
    #     )

@no_direct_access
def application_Master_Crate_TC(request):
    try:
        if not request.session.get('user_id') or not request.session.get('phone_number'):
            # Set session expiry flag for middleware
            request.session['_session_expired'] = True
            
            # Clear user-specific session data
            user_session_keys = ['phone_number', 'user_id', 'role_id', 'full_name']
            for key in user_session_keys:
                if key in request.session:
                    del request.session[key]
            
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('citizenLoginAccount')
        
        phone_number = request.session.get("phone_number")
        user_id = None
        if phone_number:
            user = get_object_or_404(CustomUser, phone=phone_number, role_id=2)
            user_id = user.id

        service_db = request.session.get("service_db", "")
   
        if request.method == "GET":
            message = request.session.pop("message", None)
            form_data = request.session.pop("form_data", None)
            applicantType = parameter_master.objects.filter(
                parameter_id__in=[11, 12]
            ).values_list("parameter_value", "parameter_value")
            ReasonSelect = parameter_master.objects.filter(
                parameter_name="Reason for removal of tree"
            ).values_list("parameter_value", "parameter_value")
            # documentList = document_master.objects.filter(is_active=1)
            # documentList = document_master.objects.filter(is_active=1).exclude(doc_id__in=[13, 14, 15, 16, 17, 18])
            documentList = document_master.objects.filter(is_active=1).exclude(doc_id__in=[13, 14, 15, 16, 17, 18]).order_by('order_by')

            for document in documentList:
                if document.doc_subpath:
                    document.encrypted_subpath = encrypt_parameter(document.doc_subpath)
                else:
                    document.encrypted_subpath = None

            return render(
                request,
                "TreeCutting/applicationMasterCreateTC.html",
                {
                    "applicantType": applicantType,
                    "ReasonSelect": ReasonSelect,
                    "documentList": documentList,
                    "message": message,
                    "form_data": form_data,
                },
            )

        elif request.method == "POST":
            applicant_type = request.POST.get("applicant_type")
            name_of_applicant = request.POST.get("applicant_name")
            plot_no = request.POST.get("plot_no")
            survey_no = request.POST.get("survey_no")
            address = request.POST.get("address")
            total_existing_no_of_trees = request.POST.get("existing_trees")
            proposed_no_of_trees_to_cut_or_transplant = request.POST.get("trees_to_cut")
            balance_no_of_trees_to_retain = request.POST.get("trees_to_retain")
            reason_for_cutting_trees = request.POST.get("removal_reason")

            if not (
                applicant_type
                and name_of_applicant
                and plot_no
                and survey_no
                and address
                and total_existing_no_of_trees
                and proposed_no_of_trees_to_cut_or_transplant
                and balance_no_of_trees_to_retain
                and reason_for_cutting_trees
            ):
                messages.error(request, "All fields are required.")
                return redirect("applicationFormIndexTC")

            mandatory_documents = document_master.objects.filter(
                mandatory=1, is_active=1
            )
            all_uploaded = True
            missing_documents = []

            for document in mandatory_documents:
                if not request.FILES.get(f"upload_{document.doc_id}"):
                    all_uploaded = False
                    missing_documents.append(document.doc_name)

            if not all_uploaded:
                message = "Please upload the mandatory documents."
                request.session["message"] = message
                request.session["form_data"] = {
                    "applicant_type": applicant_type,
                    "name_of_applicant": name_of_applicant,
                    "plot_no": plot_no,
                    "survey_no": survey_no,
                    "address": address,
                    "total_existing_no_of_trees": total_existing_no_of_trees,
                    "proposed_no_of_trees_to_cut_or_transplant": proposed_no_of_trees_to_cut_or_transplant,
                    "balance_no_of_trees_to_retain": balance_no_of_trees_to_retain,
                    "reason_for_cutting_trees": reason_for_cutting_trees,
                }

                return redirect("application_Master_Crate_TC")

            application = application_form.objects.create(
                applicant_type=applicant_type,
                name_of_applicant=name_of_applicant,
                plot_no=plot_no,
                survey_no=survey_no,
                address=address,
                total_existing_no_of_trees=total_existing_no_of_trees,
                proposed_no_of_trees_to_cut_or_transplant=proposed_no_of_trees_to_cut_or_transplant,
                balance_no_of_trees_to_retain=balance_no_of_trees_to_retain,
                reason_for_cutting_trees=reason_for_cutting_trees,
                created_by=user_id,
            )

            servicefetch = service_master.objects.using("default").get(
                ser_id=service_db
            )
            service_name = servicefetch.ser_name

            user_folder_path = os.path.join(settings.MEDIA_ROOT, f"{service_name}")
            os.makedirs(user_folder_path, exist_ok=True)

            user_folder_path = os.path.join(user_folder_path, f"User")
            os.makedirs(user_folder_path, exist_ok=True)

            application_folder_path = os.path.join(
                user_folder_path, f"user_{user_id}", f"application_{application.id}"
            )
            os.makedirs(application_folder_path, exist_ok=True)

            for document in document_master.objects.all():
                uploaded_file = request.FILES.get(f"upload_{document.doc_id}")

                if uploaded_file:
                    document_folder_path = os.path.join(
                        application_folder_path, f"document_{document.doc_id}"
                    )
                    os.makedirs(document_folder_path, exist_ok=True)

                    for file_name in os.listdir(document_folder_path):
                        file_path = os.path.join(document_folder_path, file_name)
                        if os.path.isfile(file_path):
                            os.remove(file_path)

                    file_name = uploaded_file.name
                    file_path = os.path.join(document_folder_path, file_name)

                    with open(file_path, "wb+") as destination:
                        for chunk in uploaded_file.chunks():
                            destination.write(chunk)

                    relative_file_path = f"{service_name}/User/user_{user_id}/application_{application.id}/document_{document.doc_id}/{file_name}"

                    existing_document = citizen_document.objects.filter(
                        user_id=user_id,
                        document=document.doc_id,
                        application_id=application,
                    ).first()

                    if existing_document:
                        existing_document.file_name = file_name
                        existing_document.filepath = relative_file_path
                        existing_document.updated_by = user_id
                        existing_document.updated_at = timezone.now()
                        existing_document.save()
                    else:
                        citizen_document.objects.create(
                            user_id=user_id,
                            file_name=file_name,
                            filepath=relative_file_path,
                            document=document,
                            application_id=application,
                            created_by=user_id,
                            updated_by=user_id,
                        )

            new_id = 0
            new_id = encrypt_parameter(str(new_id))
            row_id = encrypt_parameter(str(application.id))

            messages.success(request, "Form submitted successfully.")
            return redirect("application_Master_View_TC", row_id, new_id)

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user_id])
        logger.error(f"Error in applicationFormIndexTC: {str(e)}")

@no_direct_access
def application_Master_Edit_TC(request, row_id, new_id):
    try:
        if not request.session.get('user_id') or not request.session.get('phone_number'):
            # Set session expiry flag for middleware
            request.session['_session_expired'] = True
            
            # Clear user-specific session data
            user_session_keys = ['phone_number', 'user_id', 'role_id', 'full_name']
            for key in user_session_keys:
                if key in request.session:
                    del request.session[key]
            
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('citizenLoginAccount')
        
        phone_number = request.session.get("phone_number")
        user_id = None
        if phone_number:
            user = get_object_or_404(CustomUser, phone=phone_number, role_id=2)
            user_id = user.id

        service_db = request.session.get("service_db", "default")

        if request.method == "GET":

            new_id = decrypt_parameter(new_id)
            row_id = decrypt_parameter(row_id)
            message = request.session.pop("message", None)
            viewDetails = get_object_or_404(application_form, id=row_id)
            applicantType = parameter_master.objects.filter(
                parameter_id__in=[11, 12]
            ).values_list("parameter_value", "parameter_value")
            ReasonSelect = parameter_master.objects.filter(
                parameter_name="Reason for removal of tree"
            ).values_list("parameter_value", "parameter_value")
            uploaded_documents = citizen_document.objects.filter(
                user_id=user_id, application_id=viewDetails
            ).exclude( document__in=[13, 14, 15, 16, 17, 18])

            for row in uploaded_documents:
                encrypted_filepath = encrypt_parameter(str(row.filepath))
                row.filepath = encrypted_filepath

            uploaded_doc_ids = uploaded_documents.values_list("document_id", flat=True)

            all_documents = document_master.objects.all()
            
            all_documents = document_master.objects.exclude(doc_id__in=[13, 14, 15, 16, 17, 18])

            not_uploaded_documents = all_documents.exclude(doc_id__in=uploaded_doc_ids)

            documentList = document_master.objects.filter(is_active=1).exclude(doc_id__in=[13, 14, 15, 16, 17, 18])

            for document in documentList:
                if document.doc_subpath:
                    document.encrypted_subpath = encrypt_parameter(document.doc_subpath)
                else:
                    document.encrypted_subpath = None

            return render(
                request,
                "TreeCutting/applicationMasterEditTC.html",
                {
                    "viewDetails": viewDetails,
                    "applicantType": applicantType,
                    "ReasonSelect": ReasonSelect,
                    "uploaded_documents": uploaded_documents,
                    "not_uploaded_documents": not_uploaded_documents,
                    "new_id": new_id,
                    "message": message,
                },
            )
            
        if request.method == "POST":

            viewDetails = get_object_or_404(application_form, id=row_id)
            viewDetails.applicant_type = request.POST.get("applicant_type")
            viewDetails.name_of_applicant = request.POST.get("applicant_name")
            viewDetails.plot_no = request.POST.get("plot_no")
            viewDetails.survey_no = request.POST.get("survey_no")
            viewDetails.address = request.POST.get("address")
            viewDetails.total_existing_no_of_trees = request.POST.get("existing_trees")
            viewDetails.proposed_no_of_trees_to_cut_or_transplant = request.POST.get(
                "trees_to_cut"
            )
            viewDetails.balance_no_of_trees_to_retain = request.POST.get(
                "trees_to_retain"
            )
            viewDetails.reason_for_cutting_trees = request.POST.get("Reason_Select")

            if not all([viewDetails.applicant_type, viewDetails.name_of_applicant, viewDetails.plot_no, viewDetails.survey_no, 
                        viewDetails.address, viewDetails.total_existing_no_of_trees, viewDetails.proposed_no_of_trees_to_cut_or_transplant, 
                        viewDetails.balance_no_of_trees_to_retain, viewDetails.reason_for_cutting_trees]):
                
                new_id = encrypt_parameter(new_id)
                row_id = encrypt_parameter(row_id)
                # messages.error(request, "All fields are mandatory. Please fill in all fields.")
                message = "All fields are mandatory. Please fill in all fields."
                request.session["message"] = message
                return redirect("application_Master_Edit_TC", row_id, new_id) 

            viewDetails.save()

            servicefetch = service_master.objects.using("default").get(
                ser_id=service_db
            )
            service_name = servicefetch.ser_name

            user_folder_path = os.path.join(settings.MEDIA_ROOT, f"{service_name}")
            os.makedirs(user_folder_path, exist_ok=True)

            user_folder_path = os.path.join(user_folder_path, f"User")
            os.makedirs(user_folder_path, exist_ok=True)

            application_folder_path = os.path.join(
                user_folder_path, f"user_{user_id}", f"application_{viewDetails.id}"
            )
            os.makedirs(application_folder_path, exist_ok=True)

            for document in document_master.objects.all():
                uploaded_file = request.FILES.get(f"upload_{document.doc_id}")

                if uploaded_file:
                    document_folder_path = os.path.join(
                        application_folder_path, f"document_{document.doc_id}"
                    )
                    os.makedirs(document_folder_path, exist_ok=True)

                    for file_name in os.listdir(document_folder_path):
                        file_path = os.path.join(document_folder_path, file_name)
                        if os.path.isfile(file_path):
                            os.remove(file_path)

                    file_name = uploaded_file.name
                    file_path = os.path.join(document_folder_path, file_name)

                    with open(file_path, "wb+") as destination:
                        for chunk in uploaded_file.chunks():
                            destination.write(chunk)

                    relative_file_path = f"{service_name}/User/user_{user_id}/application_{viewDetails.id}/document_{document.doc_id}/{file_name}"

                    existing_document = citizen_document.objects.filter(
                        user_id=user_id,
                        document=document.doc_id,
                        application_id=viewDetails,
                    ).first()

                    if existing_document:
                        existing_document.file_name = file_name
                        existing_document.filepath = relative_file_path
                        existing_document.updated_by = user_id
                        existing_document.updated_at = timezone.now()
                        existing_document.save()
                    else:
                        citizen_document.objects.create(
                            user_id=user_id,
                            file_name=file_name,
                            filepath=relative_file_path,
                            document=document,
                            application_id=viewDetails,
                            created_by=user_id,
                            updated_by=user_id,
                        )
            
            new_id = 0
            new_id = encrypt_parameter(str(new_id))
            row_id = encrypt_parameter(str(row_id))

            return redirect("application_Master_View_TC", row_id, new_id)

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), ""])
    
    # finally:
    #     if request.method == "GET":
    #         return render(
    #             request,
    #             "TreeCutting/applicationMasterEditTC.html",
    #             {
    #                 "viewDetails": viewDetails,
    #                 "applicantType": applicantType,
    #                 "ReasonSelect": ReasonSelect,
    #                 "uploaded_documents": uploaded_documents,
    #                 "not_uploaded_documents": not_uploaded_documents,
    #                 "new_id": new_id,
    #                 "message": message,
    #             },
    #         )
        # else:
        #     new_id = 0
        #     new_id = encrypt_parameter(str(new_id))
        #     row_id = encrypt_parameter(str(row_id))

        #     return redirect("application_Master_View_TC", row_id, new_id)

@no_direct_access
def application_Master_View_TC(request, row_id, new_id):
    try:
        if not request.session.get('user_id') or not request.session.get('phone_number'):
            # Set session expiry flag for middleware
            request.session['_session_expired'] = True
            
            # Clear user-specific session data
            user_session_keys = ['phone_number', 'user_id', 'role_id', 'full_name']
            for key in user_session_keys:
                if key in request.session:
                    del request.session[key]
            
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('citizenLoginAccount')
        
        phone_number = request.session.get("phone_number")
        user_id = None
        if phone_number:
            user = get_object_or_404(CustomUser, phone=phone_number, role_id=2)
            user_id = user.id
            service_db = request.session.get("service_db", "default")

        if request.method == "GET":

            row_id1 = int(decrypt_parameter(row_id))
            new_id = decrypt_parameter(new_id)
            viewDetails = None
            viewDetails = application_form.objects.get(id=row_id1)

            # To Show Letter Of Payment And Plantation
            
            if viewDetails.status_id == 10:
                uploaded_documents = citizen_document.objects.filter(
                    user_id=user_id, application_id=viewDetails.id
                ).exclude(document__in=[14, 18])

                allowed_document_ids = [16, 17]
                existing_doc_ids = uploaded_documents.values_list("document__doc_id", flat=True)

                missing_docs = document_master.objects.filter(doc_id__in=set(allowed_document_ids) - set(existing_doc_ids))
                placeholder_documents = [
                    citizen_document(document=doc, filepath=None) for doc in missing_docs
                ]

                uploaded_documents = list(uploaded_documents) + placeholder_documents
            else:
                uploaded_documents = citizen_document.objects.filter(
                    user_id=user_id, application_id=viewDetails.id
                ).exclude(document__in=[13, 14, 15, 16, 17, 18])

            for row in uploaded_documents:
                if row.filepath:
                    row.filepath = encrypt_parameter(str(row.filepath))
                
            plain_new_id = new_id
            new_id = str(encrypt_parameter(str(new_id)))
            row_id = str(encrypt_parameter(str(row_id1)))

            return render(
                request,
                "TreeCutting/applicationMasterViewTC.html",
                {
                    "viewDetails": viewDetails,
                    "uploaded_documents": uploaded_documents,
                    "new_id": new_id,
                    "row_id": row_id,
                    "plain_new_id": plain_new_id,
                },
            )
            
        if request.method == "POST":

            row_id = int(decrypt_parameter(str(row_id)))
            application = get_object_or_404(application_form, id=row_id)
            viewDetails = get_object_or_404(application_form, id=row_id)
            
            servicefetch = service_master.objects.using("default").get(
                ser_id=service_db
            )
            service_name = servicefetch.ser_name

            user_folder_path = os.path.join(settings.MEDIA_ROOT, f"{service_name}")
            os.makedirs(user_folder_path, exist_ok=True)

            user_folder_path = os.path.join(user_folder_path, f"User")
            os.makedirs(user_folder_path, exist_ok=True)

            application_folder_path = os.path.join(
                user_folder_path, f"user_{user_id}", f"application_{viewDetails.id}"
            )
            os.makedirs(application_folder_path, exist_ok=True)

            for document in document_master.objects.all():
                uploaded_file = request.FILES.get(f"upload_{document.doc_id}")

                if uploaded_file:
                    document_folder_path = os.path.join(
                        application_folder_path, f"document_{document.doc_id}"
                    )
                    os.makedirs(document_folder_path, exist_ok=True)

                    for file_name in os.listdir(document_folder_path):
                        file_path = os.path.join(document_folder_path, file_name)
                        if os.path.isfile(file_path):
                            os.remove(file_path)

                    file_name = uploaded_file.name
                    file_path = os.path.join(document_folder_path, file_name)

                    with open(file_path, "wb+") as destination:
                        for chunk in uploaded_file.chunks():
                            destination.write(chunk)

                    relative_file_path = f"{service_name}/User/user_{user_id}/application_{viewDetails.id}/document_{document.doc_id}/{file_name}"

                    existing_document = citizen_document.objects.filter(
                        user_id=user_id,
                        document=document.doc_id,
                        application_id=viewDetails,
                    ).first()

                    if existing_document:
                        existing_document.file_name = file_name
                        existing_document.filepath = relative_file_path
                        existing_document.updated_by = user_id
                        existing_document.updated_at = timezone.now()
                        existing_document.save()
                    else:
                        citizen_document.objects.create(
                            user_id=user_id,
                            file_name=file_name,
                            filepath=relative_file_path,
                            document=document,
                            application_id=viewDetails,
                            created_by=user_id,
                            updated_by=user_id,
                        )
            
            application_id = int(application.id)
            if application.status_id in [4, 12]:
                application.status_id = 14
            elif application.status_id == 10:
                application.status_id = 10
            else:
                application.status_id = 1

            application.save()

            status_instance = status_master.objects.get(status_id=application.status_id)

            workflow, created = workflow_details.objects.get_or_create(
                form_id=application,
                defaults={
                    "status": status_instance,
                    "created_by": str(user_id),
                    "updated_at": timezone.now(),
                    "form_user_id": user_id,
                    "level": 1,
                },
            )

            if not created:
                workflow.status = status_instance
                workflow.updated_at = timezone.now()
                workflow.updated_by = str(user_id)
                workflow.save()
                
            workflow_id = workflow.id

            if application.request_no is None:
                service = callproc('stp_generateRequestNo', [service_db, application.id, workflow_id, user_id])
                trackId = request.session.get('trackId', '')
                if trackId:
                    from Account.views import upd_citizen
                    request.session["applicationId"]=(str(service[0][0]))
                    request.session["application_status"]=str(3)
                    request.session["workflow_id"] = workflow.id
                    request.session["form_id"]=application.id
                    request.session["form_user_id"]=str(user_id)
                    upd_citizen(request)

            return redirect("applicationFormIndexTC")
        
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), ""])
        logger.error(f"Error in applicationFormIndexTC: {str(e)}")

    # finally:
    #     if request.method == "GET":
    #         return render(
    #             request,
    #             "TreeCutting/applicationMasterViewTC.html",
    #             {
    #                 "viewDetails": viewDetails,
    #                 "uploaded_documents": uploaded_documents,
    #                 "new_id": new_id,
    #                 "row_id": row_id,
    #                 "plain_new_id": plain_new_id,
    #             },
    #         )
    #     else:
    #         return redirect("applicationFormIndexTC")

def download_doc(request, filepath):
    file = decrypt_parameter(filepath)
    file_path = os.path.join(settings.MEDIA_ROOT, file)
    file_name = os.path.basename(file_path)
    try:
        if os.path.exists(file_path):
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                mime_type = 'application/octet-stream'
            
            with open(file_path, 'rb') as file:
                response = HttpResponse(file.read(), content_type=mime_type)
                response['Content-Disposition'] = f'inline; filename="{file_name}"'
                return response
        else:
            return HttpResponse("File not found", status=404)

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), ''])  
        logger.error(f"Error downloading file {file_name}: {str(e)}")
        return HttpResponse("An error occurred while trying to download the file.", status=500)
    
def downloadIssuedCertificatetc(request, row_id):
    try:
        phone_number = request.session.get('phone_number')
        user = CustomUser.objects.get(phone=phone_number, role_id = 2)
        request.session['full_name'] = user.full_name
        
        row_id = decrypt_parameter(row_id)
        document = citizen_document.objects.get(application_id=row_id, document_id=14)
        
        filepath = document.filepath
        file_name = document.file_name

        encrypted_filepath = encrypt_parameter(filepath)
        
        return redirect('download_doc', encrypted_filepath)
    
    except citizen_document.DoesNotExist:
        raise  Http404("Document not found")
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user.id])
        logger.error(f"Error downloading file {file_name}: {str(e)}")
        return HttpResponse("An error occurred while trying to download the file.", status=500)

def downloadRefusalDocumenttc(request, row_id):
    try:
        phone_number = request.session.get('phone_number')
        user = CustomUser.objects.get(phone=phone_number, role_id = 2)
        request.session['full_name'] = user.full_name
        
        row_id = decrypt_parameter(row_id)
        document = citizen_document.objects.get(application_id=row_id, document_id=18)
        
        filepath = document.filepath
        file_name = document.file_name

        encrypted_filepath = encrypt_parameter(filepath)
        
        return redirect('download_doc', encrypted_filepath)
    
    except citizen_document.DoesNotExist:
        return Http404("Document not found")
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user.id])
        logger.error(f"Error downloading file {file_name}: {str(e)}")
        return HttpResponse("An error occurred while trying to download the file.", status=500)

