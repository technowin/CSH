from datetime import datetime
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render,redirect
from Account.models import *
from Masters.models import *
from DrainageConnection.models import *
import traceback
from Account.db_utils import callproc
from django.contrib import messages
from django.conf import settings
from CSH.encryption import *
import os
from CSH.settings import *
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import openpyxl
import mimetypes
from openpyxl.styles import Font, Border, Side
import pandas as pd
import calendar
from django.utils import timezone
from datetime import timedelta
from django.http import Http404
from CSH.access_control import no_direct_access

# Create your views here.
import logging
logger = logging.getLogger(__name__)

@login_required 
@no_direct_access
def index(request):
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
        context = {'role_id':role_id,'name':name,'header':header,'data':data,'user_id':request.user.id,'pre_url':pre_url}
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),user])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally: 
         return render(request,'DrainageConnection/index.html', context)

@login_required 
@no_direct_access    
def matrix_flow(request):
    docs,label,input,data = [],[],[],[]
    form_id,context,wf_id,sf,f,sb,rb,rb1  = '','','','','','','',''
    #context ={}
    try:
        early_response = None
        
        if not request.user.is_authenticated and not request.session.get('username'):
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            early_response = redirect('citizenLoginAccount')
            return early_response
        
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
                    return redirect(f'/matrix_flow?wf={encrypt_parameter(wf_id)}&af={encrypt_parameter(form_id)}&ac={ac}')
                else: messages.error(request, 'Oops...! Something went wrong!')
                return redirect(f'/index')
            if f and f !='':
                r = callproc("stp_update_forward",[wf_id,form_id,f,user])
                if r[0][0] == 'success':
                    messages.success(request, "Forwarded successfully !!")
                else: messages.error(request, 'Oops...! Something went wrong!')
                return redirect(f'/matrix_flow?wf={encrypt_parameter(wf_id)}&af={encrypt_parameter(form_id)}&ac={ac}')
            if sb and sb !='':
                r = callproc("stp_update_sendback",[wf_id,form_id,user])
                if r[0][0] == 'success':
                    messages.success(request, "Sendback successfully !!")
                elif r[0][0] == 'wrongsendback':
                    messages.error(request, 'You cannot send it back in the first stage itself.')
                    return redirect(f'/matrix_flow?wf={encrypt_parameter(wf_id)}&af={encrypt_parameter(form_id)}&ac={ac}')
                elif r[0][0] == 'multisendback':
                    messages.error(request, 'Consecutive send-backs are not permitted.')
                    return redirect(f'/matrix_flow?wf={encrypt_parameter(wf_id)}&af={encrypt_parameter(form_id)}&ac={ac}')
                else: messages.error(request, 'Oops...! Something went wrong!')
                return redirect(f'/index')
            if rb and rb !='':
                r = callproc("stp_update_rollback",[wf_id,form_id,user])
                if r[0][0] == 'success':
                    messages.success(request, "Rollback successfully !!")
                elif r[0][0] == 'wrongrollback':
                    messages.error(request, 'You cannot roll it back in the first stage itself.')
                    return redirect(f'/matrix_flow?wf={encrypt_parameter(wf_id)}&af={encrypt_parameter(form_id)}&ac={ac}')
                elif r[0][0] == 'multirollback':
                    messages.error(request, 'Consecutive roll-backs are not permitted.')
                    return redirect(f'/matrix_flow?wf={encrypt_parameter(wf_id)}&af={encrypt_parameter(form_id)}&ac={ac}')
                else: messages.error(request, 'Oops...! Something went wrong!')
                return redirect(f'/index')
            if rb1 and rb1 !='':
                r = callproc("stp_update_rollback1",[wf_id,form_id,user])
                if r[0][0] == 'success':
                    messages.success(request, "Rollback successfully !!")
                elif r[0][0] == 'multirollback':
                    messages.error(request, 'Consecutive roll-backs are not permitted.')
                    return redirect(f'/matrix_flow?wf={encrypt_parameter(wf_id)}&af={encrypt_parameter(form_id)}&ac={ac}')
                else: messages.error(request, 'Oops...! Something went wrong!')
                return redirect(f'/index')
            subordinates = callproc("stp_get_subordinates",[form_id,user])
            user_list = callproc("stp_get_dropdown_values",['marked_for'])
            reject_reasons = callproc("stp_get_dropdown_values",['reject_reasons'])
            citizen_docs = citizen_document.objects.filter(application_id=form_id) 
            # for doc_master in document_master.objects.all():
            # for doc_master in document_master.objects.exclude(is_active=0).exclude(doc_id=15):
            for doc_master in document_master.objects.exclude(is_active=0).exclude(doc_id__in=[15, 19]):
                # matching_doc = citizen_docs.filter(document=doc_master).first()
                matching_doc = citizen_docs.filter(document=doc_master).order_by('-updated_at').first()
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
                       'down_chklst':down_chklst,'down_insp':down_insp,'act_comp':act_comp}
        if request.method == "POST":
            response = None
            wf_id = decrypt_parameter(wf_id) if (wf_id := request.POST.get('wf_id', '')) else ''
            form_id = decrypt_parameter(form_id) if (form_id := request.POST.get('form_id', '')) else ''
            wf = workflow_details.objects.get(id=wf_id)
            form_user_id = wf.form_user_id
            files = request.FILES.getlist('files[]')
            comment =  request.POST.get('comment', '')
            ser= request.session.get('service_db','default')
            id1 = request.POST.get('id1', None)
            if comment!='':
                internal_user_comments.objects.create(
                        workflow=wf, comments=comment,
                        created_at=datetime.now(),created_by=str(user),updated_at=datetime.now(),updated_by=str(user)
                )  
                response = f"Your comment has been submitted: '{comment}'"
            for file in files:
                 response =  internal_docs_upload(file,role_id,user,wf,ser,'')
                
            if response:
                return JsonResponse(response, safe=False)
            
            Refusalfile = request.FILES.get('file')
            response = None

            # if Refusalfile:
                
            #     response3 = internal_docs_upload(Refusalfile, role_id, user, wf, ser, 'Refusal Document')
            #     refusal_file_resp = citizen_docs_upload(Refusalfile, form_user_id, form_id, user, ser, id1)
            #     response = response3           

            # if response:
            #     return JsonResponse(response, safe=False)

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
                    
                # elif status == 7 and ref == 'inspection':
                #     cheklist_upl_file = request.FILES.get('cheklist_upl_file')
                #     inspection_upl_file = request.FILES.get('prelim_insp_upl_file')
                #     challan_upl_file = request.FILES.get('challan_upl_file')
                #     if cheklist_upl_file and inspection_upl_file:
                #         file_resp = internal_docs_upload(cheklist_upl_file,role_id,user,wf,ser,'Checklist')
                #         file_resp = internal_docs_upload(inspection_upl_file,role_id,user,wf,ser,'Inspection')
                #         file_resp = internal_docs_upload(challan_upl_file,role_id,user,wf,ser,'ChallanForInspection')
                #     #r2 = callproc("stp_post_workflow", [wf_id, form_id, 16, 'challanReceipt', ser, user, ''])
                #     r = callproc("stp_post_workflow", [wf_id,form_id,status,ref,ser,user,''])
                #     if r[0][0] not in (""):
                #         messages.success(request, str(r[0][0]))
                #     else: messages.error(request, 'Oops...! Something went wrong!')

                elif status == 5 and ref == 'inspection':
                    # Get uploaded files
                    files = {
                        'Checklist': request.FILES.get('cheklist_upl_file'),
                        'Inspection': request.FILES.get('prelim_insp_upl_file'),
                        'ChallanForInspection': request.FILES.get('challan_upl_file')
                    }

                    # Upload each file if it exists
                    for doc_type, file_obj in files.items():
                        if file_obj:
                            internal_docs_upload(file_obj, role_id, user, wf, ser, doc_type)

                    # Determine workflow status
                    if files['ChallanForInspection']:
                        new_status = 16
                        new_ref = 'challanUploaded'
                    else:
                        new_status = status
                        new_ref = ref

                    # Call workflow procedure
                    r = callproc("stp_post_workflow", [wf_id, form_id, new_status, new_ref, ser, user, ''])
                    if r[0][0]:
                        messages.success(request, str(r[0][0]))
                    else:
                        messages.error(request, 'Oops...! Something went wrong!')

                elif (status == 6 or status==7) and (ref == 'approvall'):
                    rej_res = request.POST.get('rej_res', '').strip()
                    refusal_file = request.FILES.get('file')

                    if rej_res!='' and status in [7]:
                        internal_user_comments.objects.create(
                            workflow=wf,
                            comments=rej_res,
                            created_at=datetime.now(),
                            created_by=str(user),
                            updated_at=datetime.now(),
                            updated_by=str(user)
                        )

                    # Save refusal file if provided
                    if refusal_file:
                        response3 = internal_docs_upload(refusal_file, role_id, user, wf, ser, 'Refusal Document')
                        refusal_file_resp = citizen_docs_upload(refusal_file, form_user_id, form_id, user, ser, 13)
                        # if response3:
                        #     return JsonResponse(response3, safe=False)
                        # else:
                        #     #  fallback if upload fails
                        #     messages.error(request, "File upload failed.")
                        #     return redirect(request.META.get("HTTP_REFERER", "/"))

                    # Call approval SP after reason/file save
                    r1 = callproc("stp_post_approval", [wf_id, form_id, status, ref, ser, rej_res, user])

                    if r1[0][0] not in (""):
                        messages.success(request, str(r1[0][0]))
                        
                    else:
                        messages.error(request, "Oops...! Something went wrong!")

                    # return redirect(request.META.get("HTTP_REFERER", "/"))
                    # DESK DETAIL API 
                    # role_id = request.session.get('role_id')
                    # role = roles.objects.only('role_name').get(id=role_id)
                    # designation_map = {"EE": '1',"AEE": '2',"AE": '3'}
                    # from Account.desk_detail_api import upd_desk_detail
                    # request.session["ApplicationId1"]=wf.request_no
                    # request.session["DeskNumber"] = 'Desk ' + designation_map[role.role_name]  
                    # request.session["ReviewActionBy"] = role.role_name
                    # request.session["ReviewActionDetails"]="Approved"
                    # request.session["DeskRemark"]=rej_res
                    # desk_api_res = upd_desk_detail(request)
                    # message = f"DESK DETAIL API hit successfully | Response: {desk_api_res}"
                    # Log.objects.create(log_text=message)

                elif status == 18 and ref == 'issue_permission':
                    
                    issue_permission_file = request.FILES.get('issue_permission_file')
                    if issue_permission_file:
                        internal_resp = internal_docs_upload(issue_permission_file,role_id,user,wf,ser,'Permission Letter')
                        #citizen_resp = citizen_docs_upload(issue_permission_file, form_user_id, form_id, user, ser, id1)
                        
                    r = callproc("stp_post_workflow", [wf_id,form_id,status,ref,ser,user,''])
                    if r[0][0] not in (""):
                        messages.success(request, str(r[0][0]))
                    else: messages.error(request, 'Oops...! Something went wrong!')

                elif (status == 8 or status==9) and (ref == 'decision'):
                    rej_res = request.POST.get('rej_res', '').strip()
                    refusal_file = request.FILES.get('file')

                    if rej_res!='' and status in [9]:
                        internal_user_comments.objects.create(
                            workflow=wf,
                            comments=rej_res,
                            created_at=datetime.now(),
                            created_by=str(user),
                            updated_at=datetime.now(),
                            updated_by=str(user)
                        )

                    # Save refusal file if provided
                    if refusal_file:
                        response3 = internal_docs_upload(refusal_file, role_id, user, wf, ser, 'Refusal Document')
                        refusal_file_resp = citizen_docs_upload(refusal_file, form_user_id, form_id, user, ser, 13)
                        # if response3:
                        #     return JsonResponse(response3, safe=False)
                        # else:
                        #     #  fallback if upload fails
                        #     messages.error(request, "File upload failed.")
                        #     return redirect(request.META.get("HTTP_REFERER", "/"))

                    # Call approval SP after reason/file save
                    r1 = callproc("stp_post_approval", [wf_id, form_id, status, ref, ser, rej_res, user])

                    if r1[0][0] not in (""):
                        messages.success(request, str(r1[0][0]))
                        
                    else:
                        messages.error(request, "Oops...! Something went wrong!")
                    
                elif status == 10 and ref == 'finalInspection':
                    final_cheklist_upl_file = request.FILES.get('final_cheklist_upl_file')
                    if final_cheklist_upl_file:
                        file_resp = internal_docs_upload(final_cheklist_upl_file,role_id,user,wf,ser,'Final Checklist')
                    r = callproc("stp_post_workflow", [wf_id,form_id,status,ref,ser,user,''])
                    if r[0][0] not in (""):
                        messages.success(request, str(r[0][0]))
                    else: messages.error(request, 'Oops...! Something went wrong!')
                elif status == 11 and ref == 'certificate':
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
                    file_resp = citizen_docs_upload(certificate_upl_file,form_user_id,form_id,user,ser, 15)
                    if r[0][0] not in (""):
                        messages.success(request, str(r[0][0]))
                    else: messages.error(request, 'Oops...! Something went wrong!')
                else:
                    f_remark = request.POST.get('f_remark')
                    if f_remark!='' and status in [6, 7]:
                        internal_user_comments.objects.create(
                                workflow=wf, comments=f_remark,
                                created_at=datetime.now(),created_by=str(user),updated_at=datetime.now(),updated_by=str(user)
                        )  
                    r = callproc("stp_post_workflow", [wf_id,form_id,status,ref,ser,user,f_remark])
                    if r[0][0] not in (""):
                        messages.success(request, str(r[0][0]))
                    else: messages.error(request, 'Oops...! Something went wrong!')


                    
                    if status == 6:
                        
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
                            
                    if status == 7:
                        
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
                            
                return redirect(f'/matrix_flow?wf={encrypt_parameter(wf_id)}&af={encrypt_parameter(form_id)}&ac={ac}')
                
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),user])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally: 
        
        if early_response:
            return early_response
        
        if request.method == "GET" and sf == '' and f == '' and sb == ''and rb == ''and rb1 == '':
            return render(request,'DrainageConnection/metrix_flow.html', context)

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
 
# def citizen_docs_upload(file,user,form_id,created_by,ser, doc_id1):
#     file_resp = None
#     doc = document_master.objects.get(doc_id=doc_id1)
#     app_form = application_form.objects.get(id=form_id)
#     service = service_master.objects.using("default").get(ser_id=ser)
#     sub_path = f'{service.ser_name}/User/user_{user}/application_{form_id}/document_{doc.doc_id}/{file.name}'
#     full_path = os.path.join(MEDIA_ROOT, sub_path)
#     folder_path = os.path.dirname(full_path)
    
#     if not os.path.exists(folder_path):
#         os.makedirs(folder_path, exist_ok=True)
#     file_exists_in_folder = os.path.exists(full_path)
#     file_exists_in_db = citizen_document.objects.filter(filepath=sub_path).exists()
#     if file_exists_in_db:
#         document = citizen_document.objects.filter(filepath=sub_path).first()
#         document.updated_at = datetime.now()
#         document.updated_by = str(user)
#         document.save()
#         with open(full_path, 'wb+') as destination:
#             for chunk in file.chunks():
#                 destination.write(chunk)
#         file_resp =  f"File '{file.name}' has been updated."
#     else:
#         with open(full_path, 'wb+') as destination:
#             for chunk in file.chunks():
#                 destination.write(chunk)

#         citizen_document.objects.create(
#             user_id=user,file_name=file.name,filepath=sub_path,
#             document=doc,application_id=app_form,
#             created_by=str(created_by),updated_by=str(created_by),
#             created_at=datetime.now(),updated_at=datetime.now()
#         )
       
#         file_resp =  f"File '{file.name}' has been inserted."
#     return file_resp

def citizen_docs_upload(file, user, form_id, created_by, ser, doc_id1):
    doc = document_master.objects.get(doc_id=doc_id1)
    app_form = application_form.objects.get(id=form_id)
    service = service_master.objects.using("default").get(ser_id=ser)

    sub_path = f'{service.ser_name}/User/user_{user}/application_{form_id}/document_{doc.doc_id}/{file.name}'
    full_path = os.path.join(MEDIA_ROOT, sub_path)
    folder_path = os.path.dirname(full_path)

    os.makedirs(folder_path, exist_ok=True)

    #  Fetch ALL existing records
    existing_docs = citizen_document.objects.filter(
        application_id=app_form,
        document=doc
    )

    # Delete ALL old files
    for old_doc in existing_docs:
        if old_doc.filepath:
            old_path = os.path.join(MEDIA_ROOT, old_doc.filepath)
            if os.path.exists(old_path):
                os.remove(old_path)

    # Delete ALL old DB records (ONCE)
    existing_docs.delete()

    # Save new file
    with open(full_path, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)

    # Insert ONE new record
    citizen_document.objects.create(
        user_id=user,
        file_name=file.name,
        filepath=sub_path,
        document=doc,
        application_id=app_form,
        created_by=str(created_by),
        updated_by=str(created_by),
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    return f"File '{file.name}' uploaded successfully."

def sample_doc(columns,file_name,user):
    try:
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = 'Sample Format'
        
        if columns and columns[0]:
            columns = [col[0] for col in columns[0]]
        
        black_border = Border(
            left=Side(border_style="thin", color="000000"),
            right=Side(border_style="thin", color="000000"),
            top=Side(border_style="thin", color="000000"),
            bottom=Side(border_style="thin", color="000000")
        )
        
        for col_num, header in enumerate(columns, 1):
            cell = sheet.cell(row=1, column=col_num)
            cell.value = header
            cell.font = Font(bold=True)
            cell.border = black_border
        
        for col in sheet.columns:
            max_length = 0
            column = col[0].column_letter  
            for cell in col:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
                    
            adjusted_width = max_length + 2 
            sheet.column_dimensions[column].width = adjusted_width  
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="' + str(file_name) +" "+str(datetime.now().strftime("%d-%m-%Y")) + '.xlsx"'
        workbook.save(response)
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),user])  
    finally:
        return response      

# application Form Index
@no_direct_access
def applicationFormIndex(request):
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
        
        phone_number = request.session['phone_number']
        
        if phone_number:
            user = get_object_or_404(CustomUser, phone=phone_number, role_id = 2)
            user_id = user.id
        else:
            user_id = None 

        new_id = 1
        new_id_Value = 0
        countRefusedDocument = None
        refused_id = None
        encrypted_new_id = encrypt_parameter(str(new_id))
        encrypted_new_id_Value = encrypt_parameter(str(new_id_Value))
        
        getApplicantData = []

        if request.method == "GET":
            applicationIndex = callproc("stp_getFormDetails", [user_id])
            
            for items in applicationIndex:
                encrypted_id = encrypt_parameter(str(items[1]))
                item = {
                    "srno": items[0],
                    "id": encrypted_id,
                    "request_no": items[2],       
                    "name_of_owner": items[3],   
                    "status": items[4],          
                    "comments": items[5]          
                }
                
                getApplicantData.append(item)
                
                # if items[4] == 'Refused' or items[4] == 'New':
                if items[4] == 'Refused':
                    refused_id = items[1]
            
            countRefusedDocumentId = callproc("stp_getRefusedDocumentDetails", [refused_id] )
            countRefusedDocument = countRefusedDocumentId[0][0] if countRefusedDocumentId else 0
                    
        return render(request, "DrainageConnection/applicationFormIndex.html", {
            "data": getApplicantData,
            "encrypted_new_id": encrypted_new_id,  
            "encrypted_new_id_Value": encrypted_new_id_Value,
            "countRefusedDocument": countRefusedDocument
        })

    except Exception as e:
        print(f"Error fetching data: {e}")
        return JsonResponse({"error": "Failed to fetch data"}, status=500)
    
# application Form Create
@no_direct_access
def applicationMasterCrate(request):
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
        
        # getDocumentData = document_master.objects.filter(is_active=1) 
        # getDocumentData = document_master.objects.filter(is_active=1).exclude(doc_id=15)
        # getDocumentData = document_master.objects.filter(is_active=1).exclude(doc_id__in=[15, 19])
        getDocumentData = document_master.objects.filter(is_active=1).exclude(doc_id__in=[15, 19]).order_by('order_by')
        for doc in getDocumentData:
            if doc.doc_subpath:
                doc.encrypted_subpath = encrypt_parameter(str(doc.doc_subpath))
        # success_message = request.session.pop('success_message', None)
        message = request.session.pop('message', None)
        form_data = request.session.pop("form_data", None)
        return render(request, 'DrainageConnection/applicationForm.html', {'documents': getDocumentData, 'message': message, 'form_data': form_data}) 
    
    except Exception as e:
       
        print(f"An error occurred: {e}")
     
        return HttpResponse("An error occurred while rendering the page.", status=500)

# application Form Create Post
def application_Master_Post(request):
    context = {}  
    try:
        global user
        
        if request.method == "POST":
            service_db = request.session.get('service_db', 'default')
            request.session['service_db'] = service_db

            phone_number = request.session.get('phone_number')
            user = CustomUser.objects.get(phone=phone_number, role_id = 2)
            full_name_session = request.session['full_name'] = user.full_name
            user_id = user.id

            mandatory_documents = document_master.objects.filter(mandatory=1, is_active=1)
            all_uploaded = True
            missing_documents = []
            
            if not request.POST.get('declaration'):
                message = 'Please confirm the declaration by checking the box before submitting the form.'
                request.session['message'] = message
                request.session["form_data"] = {
                    'Name_Premises': name_of_premises,
                    'Plot_No': plot_no,
                    'Sector_No': sector_no,
                    'Node': node,
                    'Name_Owner': name_of_owner,
                    'Address_Owner': address_of_owner,
                    'Name_Plumber': name_of_plumber,
                    'License_No_Plumber': license_no_of_plumber,
                    'Address_of_Plumber': address_of_plumber,
                    'Plot_size': plot_size,
                    'No_of_flats': no_of_flats,
                    'No_of_shops': no_of_shops,
                    'Septic_tank_size': septic_tank_size,
                    'no_of_floors': no_of_floors,
                    'applicant_contact_number': applicant_contact_number,
                }
                return redirect('applicationMasterCrate')
            
            name_of_premises = request.POST.get('Name_Premises')
            plot_no = request.POST.get('Plot_No')
            sector_no = request.POST.get('Sector_No')
            node = request.POST.get('Node')
            name_of_owner = request.POST.get('Name_Owner')
            address_of_owner = request.POST.get('Address_Owner')
            name_of_plumber = request.POST.get('Name_Plumber')
            license_no_of_plumber = request.POST.get('License_No_Plumber')
            address_of_plumber = request.POST.get('Address_of_Plumber')
            plot_size = request.POST.get('Plot_size')
            no_of_flats = request.POST.get('No_of_flats')
            no_of_shops = request.POST.get('No_of_shops')
            septic_tank_size = request.POST.get('Septic_tank_size')
            no_of_floors = request.POST.get('no_of_floors')
            applicant_contact_number = request.POST.get('applicant_contact_number')
            declaration = bool(request.POST.get('declaration'))

            for document in mandatory_documents:
                if not request.FILES.get(f'upload_{document.doc_id}'):
                    all_uploaded = False
                    missing_documents.append(document.doc_name)
                    
            if not all_uploaded:
                message = 'Please upload the mandatory documents.'
                request.session['message'] = message  
                request.session["form_data"] = {
                    'Name_Premises': name_of_premises,
                    'Plot_No': plot_no,
                    'Sector_No': sector_no,
                    'Node': node,
                    'Name_Owner': name_of_owner,
                    'Address_Owner': address_of_owner,
                    'Name_Plumber': name_of_plumber,
                    'License_No_Plumber': license_no_of_plumber,
                    'Address_of_Plumber': address_of_plumber,
                    'Plot_size': plot_size,
                    'No_of_flats': no_of_flats,
                    'No_of_shops': no_of_shops,
                    'Septic_tank_size': septic_tank_size,
                    'no_of_floors': no_of_floors,
                    'applicant_contact_number': applicant_contact_number,
                }
                return redirect('applicationMasterCrate')
                # messages.error(request, 'Please upload the mandatory documents.')
                # message = 'Please upload the mandatory documents.'
                # return redirect('applicationMasterCrate', message)
                # return render(request, "DrainageConnection/applicationForm.html", context={'message': message})

            application = application_form.objects.create(
                name_of_premises=request.POST.get('Name_Premises', ''),
                plot_no=request.POST.get('Plot_No', ''),
                sector_no=request.POST.get('Sector_No', ''),
                node=request.POST.get('Node', ''),
                name_of_owner=request.POST.get('Name_Owner', ''),
                address_of_owner=request.POST.get('Address_Owner', ''),
                name_of_plumber=request.POST.get('Name_Plumber', ''),
                license_no_of_plumber=request.POST.get('License_No_Plumber', ''),
                address_of_plumber=request.POST.get('Address_of_Plumber', ''),
                plot_size=request.POST.get('Plot_size', ''),
                no_of_flats=request.POST.get('No_of_flats', ''),
                no_of_shops=request.POST.get('No_of_shops', ''),
                septic_tank_size=request.POST.get('Septic_tank_size', ''),
                no_of_floors=request.POST.get('no_of_floors', ''),
                applicant_contact_number=request.POST.get('applicant_contact_number', ''),
                declaration = bool(request.POST.get('declaration')),
                created_by=user_id
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
            
            # user_folder_path = os.path.join(settings.MEDIA_ROOT, f'user_{user_id}')
            # application_folder_path = os.path.join(user_folder_path, f'application_{application.id}')
            # os.makedirs(application_folder_path, exist_ok=True)

            for document in document_master.objects.all():
                uploaded_file = request.FILES.get(f'upload_{document.doc_id}')
                
                if uploaded_file:
                    # Create the document folder path within the application folder
                    document_folder_path = os.path.join(application_folder_path, f'document_{document.doc_id}')
                    os.makedirs(document_folder_path, exist_ok=True)

                    # Remove all files in the document folder (if any)
                    for file_name in os.listdir(document_folder_path):
                        file_path = os.path.join(document_folder_path, file_name)
                        if os.path.isfile(file_path):
                            os.remove(file_path)  # Delete the file

                    # Construct the file name and file path for the new file
                    file_name = uploaded_file.name
                    file_path = os.path.join(document_folder_path, file_name)

                    # Save the uploaded file in chunks
                    with open(file_path, 'wb+') as destination:
                        for chunk in uploaded_file.chunks():
                            destination.write(chunk)

                    # Prepare the relative file path for database storage
                    # relative_file_path = f'user_{user_id}/application_{application.id}/document_{document.doc_id}/{file_name}'
                    relative_file_path = f"{service_name}/User/user_{user_id}/application_{application.id}/document_{document.doc_id}/{file_name}"

                    # Update the existing document or create a new record in the database
                    existing_document = citizen_document.objects.filter(
                        user_id=user_id,
                        document=document,
                        application_id=application
                    ).first()

                    
                    if existing_document:
                        existing_document.file_name = file_name
                        existing_document.filepath = relative_file_path
                        existing_document.updated_by = full_name_session
                        existing_document.updated_at = timezone.now()  # Update the timestamp
                        existing_document.save()
                    else:
                        citizen_document.objects.create(
                            user_id=user_id,
                            file_name=file_name,
                            filepath=relative_file_path,
                            document=document,
                            application_id=application,
                            created_by=full_name_session,
                            updated_by=full_name_session,
                        )
            
            new_id = 0
            new_id = encrypt_parameter(str(new_id))
            row_id = encrypt_parameter(str(application.id))
                                    
            # messages.success(request, 'Data and files uploaded successfully!')
            # request.session['success_message'] = 'Data and files uploaded successfully!'
            return redirect('viewapplicationform', row_id, new_id)  
            # return redirect('viewapplicationform', row_id=application.id, new_id=0)  

        # return redirect('viewapplicationform', row_id=application.id, new_id=0) 
    
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        user = request.user  
        callproc("stp_error_log", [fun, str(e), user])
        messages.error(request, 'Oops...! Something went wrong!')
        context['error_message'] = 'An error occurred while processing your request.'

    # finally:
    #     return redirect('viewapplicationform', row_id=application.id, new_id=0) 

# Main Index For Internal User
def InternalUserIndex(request):
    try:
        session_company = request.session.get("CC", "")
        username = ""

        service_db = request.session.get('service_db', 'default')    
        
        service = service_master.objects.get(ser_id= service_db)
        service_name = service.ser_name
    
        # Get Applicant Data

        getApplicantData = []

        applicationIndex = callproc("stp_getFormDetailsForInternalUser")
        for items in applicationIndex:
            item = {
                "srno": items[0],
                "request_no": items[1],        
                "name_of_owner": items[2],      
                "status": items[3],           
                "comments": items[4]            
            }
            getApplicantData.append(item)
        
        return render(request,"Internal User/InternalUserIndex.html",{"data": getApplicantData, "service": service_name})

    except Exception as e:
        print(f"Error fetching data: {e}")
        return JsonResponse({"error": "Failed to fetch data"}, status=500)
    except Exception as e:
        
        print(f"An error occurred: {e}")
        return HttpResponse("An error occurred while rendering the page.", status=500)  
 
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




from django.http import FileResponse, Http404
   
# View Application Form 
@no_direct_access
def viewapplicationform(request, row_id, new_id):
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
        
        context = {} 
        
        row_id = decrypt_parameter(row_id)
        new_id = decrypt_parameter(new_id)
        
        phone_number = request.session['phone_number']
        
        if phone_number:
                user = get_object_or_404(CustomUser, phone=phone_number, role_id = 2)
                user_id = user.id
        else:
                user_id = None
            
        application = get_object_or_404(application_form, pk=row_id)
        uploaded_documents = citizen_document.objects.filter(user_id=user_id, application_id=application).exclude(document_id__in=[15, 19])
        for row in uploaded_documents:
                encrypted_filepath = encrypt_parameter(str(row.filepath))
                row.filepath = encrypted_filepath
        
        row_id = encrypt_parameter(str(row_id))
        row_id_status = encrypt_parameter(str(1))
                        
        context = {
            'application': application,
            'uploaded_documents': uploaded_documents,
            'new_id': new_id,
            'MEDIA_URL': MEDIA_ROOT,
            'row_id' : row_id,
            'row_id_status' : row_id_status,
        }
        
        return render(request, 'DrainageConnection/viewapplicationform.html', context)
    
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        user = request.user
        callproc("stp_error_log", [fun, str(e), ''])
        messages.error(request, 'Oops...! Something went wrong!')

# Application Form Final Submit    
def application_Form_Final_Submit(request):
    if request.method == "POST":
        try:
                
            phone_number = request.session['phone_number']
            service_db = request.session['service_db']
        
            if phone_number:
                user = get_object_or_404(CustomUser, phone=phone_number, role_id = 2)
                user_id = user.id
            else:
                user_id = None
                
            application_id = request.POST.get('application_id')
            application = get_object_or_404(application_form, id=application_id)

            if application.status_id == 4:
                application.status_id = 9
            else:
                application.status_id = 1
                
            application.save()

            status_instance = status_master.objects.get(status_id=application.status_id)

            workflow, created = workflow_details.objects.get_or_create(
                form_id=application,
                defaults={
                    'status': status_instance,
                    'created_by': str(user),
                    'updated_at': timezone.now(),
                    'form_user_id': user_id,
                    'level': 1
                }
            )

            if not created:
                workflow.status = status_instance
                workflow.updated_at = timezone.now()
                workflow.updated_by = user_id
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
            return redirect('applicationFormIndex')

        except application_form.DoesNotExist:
            return JsonResponse({"error": "Application not found."}, status=404)
        except Exception as e:
            print(f"Error occurred: {e}")
            return JsonResponse({"error": "An unexpected error occurred."}, status=500)

    return render(request, "DrainageConnection/applicationFormIndex.html")

# Edit Application Form
@no_direct_access
def EditApplicationForm(request, row_id, row_id_status):
    context = {}

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
        
        phone_number = request.session['phone_number']
        
        if phone_number:
            user = get_object_or_404(CustomUser, phone=phone_number, role_id = 2)
            user_id = user.id
        else:
            user_id = None
        
        row_id = decrypt_parameter(row_id)
        row_id_status = decrypt_parameter(row_id_status)
        
        application = get_object_or_404(application_form, pk=row_id)

        uploaded_documents = citizen_document.objects.filter(user_id=user_id, application_id=application).exclude(document_id__in=[15, 19])
        for row in uploaded_documents:
                encrypted_filepath = encrypt_parameter(str(row.filepath))
                row.filepath = encrypted_filepath

        uploaded_doc_ids = uploaded_documents.values_list('document_id', flat=True)

        all_documents = document_master.objects.all()

        not_uploaded_documents = all_documents.exclude(doc_id__in=uploaded_doc_ids)

        context = {
            'application': application,
            'uploaded_documents': uploaded_documents,
            'not_uploaded_documents': not_uploaded_documents,
            'MEDIA_URL': settings.MEDIA_URL,
            'row_id_status': row_id_status,
        }
        
        return render(request, 'DrainageConnection/EditApplicationForm.html', context)

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        user = request.user
        callproc("stp_error_log", [fun, str(e), user])
        messages.error(request, 'Oops...! Something went wrong!')
   
# Edit Post Here          
def edit_Post_Application_Master(request, application_id, row_id_status):
    try:
        application = get_object_or_404(application_form, id=application_id)
        
        service_db = request.session.get('service_db', 'default')
        request.session['service_db'] = service_db
        phone_number = request.session.get('phone_number')
        user = CustomUser.objects.get(phone=phone_number, role_id = 2)
        full_name_session = request.session['full_name'] = user.full_name
        user_id = user.id

        if request.method == 'POST':
            name_of_premises = request.POST.get('Name_Premises')
            plot_no = request.POST.get('Plot_No')
            sector_no = request.POST.get('Sector_No')
            node = request.POST.get('Node')
            name_of_owner = request.POST.get('Name_Owner')
            address_of_owner = request.POST.get('Address_Owner')
            name_of_plumber = request.POST.get('Name_Plumber')
            license_no_plumber = request.POST.get('License_No_Plumber')
            address_of_plumber = request.POST.get('Address_of_Plumber')
            plot_size = request.POST.get('Plot_size')
            no_of_flats = request.POST.get('No_of_flats')
            no_of_shops = request.POST.get('No_of_shops')
            septic_tank_size = request.POST.get('Septic_tank_size')

            application.name_of_premises = name_of_premises
            application.plot_no = plot_no
            application.sector_no = sector_no
            application.node = node
            application.name_of_owner = name_of_owner
            application.address_of_owner = address_of_owner
            application.name_of_plumber = name_of_plumber
            application.license_no_of_plumber = license_no_plumber
            application.address_of_plumber = address_of_plumber
            application.plot_size = plot_size
            application.no_of_flats = no_of_flats
            application.no_of_shops = no_of_shops
            application.septic_tank_size = septic_tank_size

            application.save()

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
            
            # user_folder_path = os.path.join(settings.MEDIA_ROOT, f'user_{user_id}')
            # application_folder_path = os.path.join(user_folder_path, f'application_{application.id}')
            # os.makedirs(application_folder_path, exist_ok=True)

            for document in document_master.objects.all():
                uploaded_file = request.FILES.get(f'upload_{document.doc_id}')
                
                if uploaded_file:
                    # Create the document folder path within the application folder
                    document_folder_path = os.path.join(application_folder_path, f'document_{document.doc_id}')
                    os.makedirs(document_folder_path, exist_ok=True)

                    # Remove all files in the document folder (if any)
                    for file_name in os.listdir(document_folder_path):
                        file_path = os.path.join(document_folder_path, file_name)
                        if os.path.isfile(file_path):
                            os.remove(file_path)  # Delete the file

                    # Construct the file name and file path for the new file
                    file_name = uploaded_file.name
                    file_path = os.path.join(document_folder_path, file_name)

                    # Save the uploaded file in chunks
                    with open(file_path, 'wb+') as destination:
                        for chunk in uploaded_file.chunks():
                            destination.write(chunk)

                    # Prepare the relative file path for database storage
                    # relative_file_path = f'user_{user_id}/application_{application.id}/document_{document.doc_id}/{file_name}'
                    relative_file_path = f"{service_name}/User/user_{user_id}/application_{application.id}/document_{document.doc_id}/{file_name}"
                    # Update the existing document or create a new record in the database
                    existing_document = citizen_document.objects.filter(
                        user_id=user_id,
                        document=document,
                        application_id=application
                    ).first()

                    if existing_document:
                        existing_document.file_name = file_name
                        existing_document.filepath = relative_file_path
                        existing_document.updated_by = full_name_session
                        existing_document.updated_at = timezone.now()  # Update the timestamp
                        existing_document.save()
                    else:
                        citizen_document.objects.create(
                            user_id=user_id,
                            file_name=file_name,
                            filepath=relative_file_path,
                            document=document,
                            application_id=application,
                            created_by=full_name_session,
                            updated_by=full_name_session,
                        )

            new_id = 0
            new_id = encrypt_parameter(str(new_id))
            row_id = encrypt_parameter(str(application.id))
            
            if row_id_status == 1: 
                return redirect('viewapplicationform', row_id, new_id)
                # return redirect('viewapplicationform', row_id=application_id, new_id=0)
            else:
                return redirect('applicationFormIndex') 

    except Exception as e:
        print(f"Error: {e}")
        return render(request, "DrainageConnection/applicationFormIndex.html")

# Edit Application Form Final Submit
def EditApplicationFormFinalSubmit(request, row_id, row_id_status):
    context = {}

    try:
        # full_name = request.session.get('full_name')
        phone_number = request.session['phone_number']
        
        if phone_number:
            user = get_object_or_404(CustomUser, phone=phone_number, role_id = 2)
            user_id = user.id
        else:
            user_id = None 
        
        row_id = decrypt_parameter(row_id)
        row_id_status = decrypt_parameter(row_id_status)
        
        application = get_object_or_404(application_form, pk=row_id)

        uploaded_documents = citizen_document.objects.filter(user_id=user_id, application_id=application).exclude(document_id__in=[15, 19])
        
        # for doc in uploaded_documents:
        #     print(f"Document ID: {doc.id}, File Name: {doc.file_name}, "
        #           f"File Path: {doc.filepath}, Comment: {doc.comment}, "
        #           f"Created At: {doc.created_at}, User ID: {doc.user_id}")
            
        for row in uploaded_documents:
                encrypted_filepath = encrypt_parameter(str(row.filepath))
                row.filepath = encrypted_filepath
                
        uploaded_doc_ids = uploaded_documents.values_list('document_id', flat=True)

        all_documents = document_master.objects.all()
        
        all_documents = document_master.objects.exclude(doc_id__in=[15, 19]).exclude(is_active=0)

        not_uploaded_documents = all_documents.exclude(doc_id__in=uploaded_doc_ids)

        context = {
            'application': application,
            'uploaded_documents': uploaded_documents,
            'not_uploaded_documents': not_uploaded_documents,
            'MEDIA_URL': MEDIA_ROOT,
            'row_id_status': row_id_status,
        }

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), '1'])
        messages.error(request, 'Oops...! Something went wrong!')

    return render(request, 'DrainageConnection/EditApplicationFormFinalSubmit.html', context)

# Edit Post Here Final Submit        
def edit_Post_Application_Master_final_submit(request, application_id, row_id_status):
    try:
        application = get_object_or_404(application_form, id=application_id)
        
        service_db = request.session.get('service_db', 'default')
        request.session['service_db'] = service_db
        phone_number = request.session.get('phone_number')
        user = CustomUser.objects.get(phone=phone_number, role_id = 2)
        full_name_session = request.session['full_name'] = user.full_name
        user_id = user.id

        if request.method == 'POST':
            name_of_premises = request.POST.get('Name_Premises')
            plot_no = request.POST.get('Plot_No')
            sector_no = request.POST.get('Sector_No')
            node = request.POST.get('Node')
            name_of_owner = request.POST.get('Name_Owner')
            address_of_owner = request.POST.get('Address_Owner')
            name_of_plumber = request.POST.get('Name_Plumber')
            license_no_plumber = request.POST.get('License_No_Plumber')
            address_of_plumber = request.POST.get('Address_of_Plumber')
            plot_size = request.POST.get('Plot_size')
            no_of_flats = request.POST.get('No_of_flats')
            no_of_shops = request.POST.get('No_of_shops')
            septic_tank_size = request.POST.get('Septic_tank_size')
            no_of_floors = request.POST.get('no_of_floors')
            applicant_contact_number = request.POST.get('applicant_contact_number')

            application.name_of_premises = name_of_premises
            application.plot_no = plot_no
            application.sector_no = sector_no
            application.node = node
            application.name_of_owner = name_of_owner
            application.address_of_owner = address_of_owner
            application.name_of_plumber = name_of_plumber
            application.license_no_of_plumber = license_no_plumber
            application.address_of_plumber = address_of_plumber
            application.plot_size = plot_size
            application.no_of_flats = no_of_flats
            application.no_of_shops = no_of_shops
            application.septic_tank_size = septic_tank_size
            application.no_of_floors = no_of_floors
            application.applicant_contact_number = applicant_contact_number

            application.save()

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
            
            # user_folder_path = os.path.join(settings.MEDIA_ROOT, f'user_{user_id}')
            # application_folder_path = os.path.join(user_folder_path, f'application_{application.id}')
            # os.makedirs(application_folder_path, exist_ok=True)

            for document in document_master.objects.all():
                uploaded_file = request.FILES.get(f'upload_{document.doc_id}')
                
                if uploaded_file:
                    # Create the document folder path within the application folder
                    document_folder_path = os.path.join(application_folder_path, f'document_{document.doc_id}')
                    os.makedirs(document_folder_path, exist_ok=True)

                    # Remove all files in the document folder (if any)
                    for file_name in os.listdir(document_folder_path):
                        file_path = os.path.join(document_folder_path, file_name)
                        if os.path.isfile(file_path):
                            os.remove(file_path)  # Delete the file

                    # Construct the file name and file path for the new file
                    file_name = uploaded_file.name
                    file_path = os.path.join(document_folder_path, file_name)

                    # Save the uploaded file in chunks
                    with open(file_path, 'wb+') as destination:
                        for chunk in uploaded_file.chunks():
                            destination.write(chunk)

                    # Prepare the relative file path for database storage
                    # relative_file_path = f'user_{user_id}/application_{application.id}/document_{document.doc_id}/{file_name}'
                    relative_file_path = f"{service_name}/User/user_{user_id}/application_{application.id}/document_{document.doc_id}/{file_name}"
                    # Update the existing document or create a new record in the database
                    existing_document = citizen_document.objects.filter(
                        user_id=user_id,
                        document=document,
                        application_id=application
                    ).first()

                    if existing_document:
                        existing_document.file_name = file_name
                        existing_document.filepath = relative_file_path
                        existing_document.updated_by = full_name_session
                        existing_document.updated_at = timezone.now()  # Update the timestamp
                        existing_document.save()
                    else:
                        citizen_document.objects.create(
                            user_id=user_id,
                            file_name=file_name,
                            filepath=relative_file_path,
                            document=document,
                            application_id=application,
                            created_by=full_name_session,
                            updated_by=full_name_session,
                        )
            
            new_id = 0
            new_id = encrypt_parameter(str(new_id))
            row_id = encrypt_parameter(str(application.id))
            
            return redirect('viewapplicationform', row_id, new_id)
            # return redirect('viewapplicationform', row_id=application_id, new_id=0)

    except Exception as e:
        print(f"Error: {e}")
        return render(request, "DrainageConnection/applicationFormIndex.html")

def downloadIssuedCertificatedc(request, row_id):
    try:
        phone_number = request.session.get('phone_number')
        user = CustomUser.objects.get(phone=phone_number, role_id = 2)
        request.session['full_name'] = user.full_name
        
        row_id = decrypt_parameter(row_id)
        document = citizen_document.objects.get(application_id=row_id, document_id=15)
        
        filepath = document.filepath
        file_name = document.file_name

        encrypted_filepath = encrypt_parameter(filepath)
        
        return redirect('download_doc', encrypted_filepath)
    
    except citizen_document.DoesNotExist:
        raise Http404("Document not found")
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user.id])
        logger.error(f"Error downloading file {file_name}: {str(e)}")
        return HttpResponse("An error occurred while trying to download the file.", status=500)

# def downloadRefusalDocument(request, row_id):
#     try:
#         phone_number = request.session.get('phone_number')
#         user = CustomUser.objects.get(phone=phone_number, role_id = 2)
#         request.session['full_name'] = user.full_name
        
#         row_id = decrypt_parameter(row_id)
#         document = citizen_document.objects.get(application_id=row_id, document_id=13)
        
#         filepath = document.filepath
#         file_name = document.file_name

#         encrypted_filepath = encrypt_parameter(filepath)
        
#         return redirect('download_doc', encrypted_filepath)
    
#     except citizen_document.DoesNotExist:
#         return Http404("Document not found")
#     except Exception as e:
#         tb = traceback.extract_tb(e.__traceback__)
#         fun = tb[0].name
#         callproc("stp_error_log", [fun, str(e), user.id])
#         logger.error(f"Error downloading file {file_name}: {str(e)}")
#         return HttpResponse("An error occurred while trying to download the file.", status=500)



def downloadRefusalDocument(request, row_id):
    try:
        phone_number = request.session.get('phone_number')
        user = CustomUser.objects.get(phone=phone_number, role_id=2)
        request.session['full_name'] = user.full_name

        row_id = decrypt_parameter(row_id)

        # Get the latest refusal document (doc_id = 19) for this application
        document = (
            citizen_document.objects
            .filter(application_id=row_id, document_id=13)
            .order_by('-id')  # latest by primary key
            .first()
        )

        if not document:
            raise Http404("Refusal document not found")

        filepath = document.filepath
        file_name = document.file_name

        encrypted_filepath = encrypt_parameter(filepath)

        return redirect('download_doc', encrypted_filepath)

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name if tb else "downloadRefusalDocument"
        callproc("stp_error_log", [fun, str(e), user.id if 'user' in locals() else None])
        logger.error(f"Error downloading refusal file {file_name if 'file_name' in locals() else ''}: {str(e)}")
        return HttpResponse("An error occurred while trying to download the file.", status=500)


from django.shortcuts import redirect
from django.contrib import messages
from django.http import Http404, HttpResponse


logger = logging.getLogger(__name__)

def viewUploadedChallan(request, form_id):
    try:
        # Decrypt workflow_id
        form_id1 = decrypt_parameter(form_id)
        rows = callproc("stp_get_challan_doc", [form_id1])

        filepath = ''
        for row in rows:
            filepath = str(row[0])

        # Full path inside MEDIA_ROOT
        file_path = os.path.join(settings.MEDIA_ROOT, filepath)

        if not os.path.exists(file_path):
            raise Http404("File not found")

        # Detect MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"

        response = FileResponse(open(file_path, "rb"), content_type=mime_type)

        # ✅ Open inline instead of download
        response["Content-Disposition"] = f'inline; filename="{os.path.basename(file_path)}"'
        return response

    except Exception as e:
        print(f"View challan error: {e}")
        raise Http404("Error fetching file")




def upload_challan_receipt(request, form_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request method."}, status=405)

    try:
        app_id = decrypt_parameter(form_id)
        application = application_form.objects.get(id=app_id)

        # Prevent duplicate upload
        if application.status_id == 17:
            return JsonResponse({
                "success": False,
                "message": "Receipt has already been uploaded. You cannot upload again."
            })

        challan_file = request.FILES.get("challan_file")
        if not challan_file:
            return JsonResponse({"success": False, "message": "No file selected."})

        # Use logged-in user safely
        phone_number = request.session['phone_number']
        
        if phone_number:
            user = get_object_or_404(CustomUser, phone=phone_number, role_id = 2)
            user_id = user.id
            full_name = request.session.get("full_name", user.full_name or user.username)
        else:
            user_id = None 
        
    
       

        # Save document (doc_id hardcoded as 24 for Challan Receipt)
        upload_challan_wrapper(
            challan_file,
            user_id,
            app_id,
            created_by=full_name,
            ser='1',
            doc_id1=24
        )

        # Update status to 17
        callproc("sp_update_status", [app_id, application.id, 17, user_id])

        return JsonResponse({"success": True, "message": "Receipt uploaded successfully."})

    except application_form.DoesNotExist:
        return JsonResponse({"success": False, "message": "Application not found."}, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"success": False, "message": f"Upload failed: {str(e)}"}, status=500)

def upload_challan_wrapper(file, user, form_id, created_by, ser, doc_id1):
    """
    Wrapper function for citizen_docs_upload that handles form ID conversion
    """
    try:
        if isinstance(form_id, str):
            form_id = int(form_id)
    except (ValueError, TypeError):
        raise ValueError("Invalid form ID format. Form ID must be a valid integer.")

    return citizen_docs_upload(file, user, form_id, created_by, ser, doc_id1)




def PermissionLetter(request, row_id):
    try:
        phone_number = request.session.get('phone_number')
        user = CustomUser.objects.get(phone=phone_number, role_id=2)
        request.session['full_name'] = user.full_name

        # Decrypt row_id
        row_id = decrypt_parameter(row_id)
        rows = callproc("stp_get_permission_doc", [row_id])

        filepath = ''
        for row in rows:
            filepath = str(row[0]) if row[0] else ''

        # ✅ If no filepath in DB
        if not filepath:
            return redirect(f"{request.META.get('HTTP_REFERER', 'home')}?doc_status=not_uploaded")

        # ✅ Build full path and check
        file_path = os.path.join(settings.MEDIA_ROOT, filepath)
        if not os.path.exists(file_path):
            return redirect(f"{request.META.get('HTTP_REFERER', 'home')}?doc_status=not_uploaded")

        # ✅ Encrypt relative path before redirecting to download_doc
        encrypted_filepath = encrypt_parameter(filepath)
        return redirect('download_doc', encrypted_filepath)

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name if tb else "PermissionLetter"
        callproc("stp_error_log", [fun, str(e), user.id if 'user' in locals() else None])
        logger.error(f"Error downloading permission letter: {str(e)}")
        return HttpResponse("An error occurred while trying to download the file.", status=500)

def upload_connection_photographs(request, form_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request method."}, status=405)

    try:
        # Decrypt form_id and fetch application
        app_id = decrypt_parameter(form_id)
        application = application_form.objects.get(id=app_id)

        #  Prevent duplicate upload (assume status 18 = photographs uploaded)
        if application.status_id == 19:
            return JsonResponse({
                "success": False,
                "message": "Connection photographs have already been uploaded. You cannot upload again."
            })

        #  Get uploaded file
        photo_file = request.FILES.get("photo_file")
        if not photo_file:
            return JsonResponse({"success": False, "message": "No file selected."})

        #  Identify logged-in user
        phone_number = request.session.get('phone_number')
        if phone_number:
            user = get_object_or_404(CustomUser, phone=phone_number, role_id=2)
            user_id = user.id
            full_name = request.session.get("full_name", user.full_name or user.username)
        else:
            user_id = None
            full_name = "System"

        #  Save document (assign doc_id = 25 for Connection Photographs)
        upload_challan_wrapper(
            photo_file,
            user_id,
            app_id,
            created_by=full_name,
            ser='1',
            doc_id1=25
        )

        #  Update application status (19 = photographs uploaded)
        callproc("sp_update_status", [app_id, application.id, 19, user_id])

        return JsonResponse({"success": True, "message": "Connection photographs uploaded successfully."})

    except application_form.DoesNotExist:
        return JsonResponse({"success": False, "message": "Application not found."}, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"success": False, "message": f"Upload failed: {str(e)}"}, status=500)


