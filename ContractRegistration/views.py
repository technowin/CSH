from datetime import datetime
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render,redirect
from Account.models import *
from Masters.models import *
from ContractRegistration.models import *
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

# Create your views here.
import logging
logger = logging.getLogger(__name__)

@login_required 
def index_cr(request):
    pre_url = request.META.get('HTTP_REFERER')
    header, data = [], []
    name = ''
    try:
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
         return render(request,'ContractRegistration/index.html', context)

@login_required 
def matrix_flow_cr(request):
    docs,label,input,data = [],[],[],[]
    form_id,context,wf_id,sf,f,sb,rb,rb1  = '','','','','','','',''
    try:
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
                    return redirect(f'/matrix_flow_cr?wf={encrypt_parameter(wf_id)}&af={encrypt_parameter(form_id)}&ac={ac}')
                else: messages.error(request, 'Oops...! Something went wrong!')
                return redirect(f'/index_cr')
            if f and f !='':
                r = callproc("stp_update_forward",[wf_id,form_id,f,user])
                if r[0][0] == 'success':
                    messages.success(request, "Forwarded successfully !!")
                else: messages.error(request, 'Oops...! Something went wrong!')
                return redirect(f'/matrix_flow_cr?wf={encrypt_parameter(wf_id)}&af={encrypt_parameter(form_id)}&ac={ac}')
            if sb and sb !='':
                r = callproc("stp_update_sendback",[wf_id,form_id,user])
                if r[0][0] == 'success':
                    messages.success(request, "Sendback successfully !!")
                elif r[0][0] == 'wrongsendback':
                    messages.error(request, 'You cannot send it back in the first stage itself.')
                    return redirect(f'/matrix_flow_cr?wf={encrypt_parameter(wf_id)}&af={encrypt_parameter(form_id)}&ac={ac}')
                elif r[0][0] == 'multisendback':
                    messages.error(request, 'Consecutive send-backs are not permitted.')
                    return redirect(f'/matrix_flow_cr?wf={encrypt_parameter(wf_id)}&af={encrypt_parameter(form_id)}&ac={ac}')
                else: messages.error(request, 'Oops...! Something went wrong!')
                return redirect(f'/index_cr')
            if rb and rb !='':
                r = callproc("stp_update_rollback",[wf_id,form_id,user])
                if r[0][0] == 'success':
                    messages.success(request, "Rollback successfully !!")
                elif r[0][0] == 'wrongrollback':
                    messages.error(request, 'You cannot roll it back in the first stage itself.')
                    return redirect(f'/matrix_flow_cr?wf={encrypt_parameter(wf_id)}&af={encrypt_parameter(form_id)}&ac={ac}')
                elif r[0][0] == 'multirollback':
                    messages.error(request, 'Consecutive roll-backs are not permitted.')
                    return redirect(f'/matrix_flow_cr?wf={encrypt_parameter(wf_id)}&af={encrypt_parameter(form_id)}&ac={ac}')
                else: messages.error(request, 'Oops...! Something went wrong!')
                return redirect(f'/index_cr')
            if rb1 and rb1 !='':
                r = callproc("stp_update_rollback1",[wf_id,form_id,user])
                if r[0][0] == 'success':
                    messages.success(request, "Rollback successfully !!")
                elif r[0][0] == 'multirollback':
                    messages.error(request, 'Consecutive roll-backs are not permitted.')
                    return redirect(f'/matrix_flow_cr?wf={encrypt_parameter(wf_id)}&af={encrypt_parameter(form_id)}&ac={ac}')
                else: messages.error(request, 'Oops...! Something went wrong!')
                return redirect(f'/index_cr')
            subordinates = callproc("stp_get_subordinates",[form_id,user])
            user_list = callproc("stp_get_dropdown_values",['marked_for'])
            reject_reasons = callproc("stp_get_dropdown_values",['reject_reasons'])
            citizen_docs = citizen_document.objects.filter(application_id=form_id) 
            for doc_master in document_master.objects.all():
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
            if comment!='':
                internal_user_comments.objects.create(
                        workflow=wf, comments=comment,
                        created_at=datetime.now(),created_by=str(user),updated_at=datetime.now(),updated_by=str(user)
                )  
                response = f"Your comment has been submitted: '{comment}'"
            for file in files:
                 response =  internal_docs_upload(file,role_id,user,wf,ser,'')
            
            Refusalfile = request.FILES.get('file')
            response = None

            if Refusalfile:

                response1 = internal_docs_upload(Refusalfile, role_id, user, wf, ser, 'Refusal Document')
                file_resp = citizen_docs_upload(Refusalfile, form_user_id, form_id, user, ser, id1)
                
                response = response1
                    
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
                elif status == 8 and ref == 'certificate':
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
                    file_resp = citizen_docs_upload(certificate_upl_file,form_user_id,form_id,user,ser, 4)
                    if r[0][0] not in (""):
                        messages.success(request, str(r[0][0]))
                    else: messages.error(request, 'Oops...! Something went wrong!')
                else:
                    f_remark = request.POST.get('f_remark')
                    if f_remark!='' and status in [11, 12]:
                        internal_user_comments.objects.create(
                                workflow=wf, comments=f_remark,
                                created_at=datetime.now(),created_by=str(user),updated_at=datetime.now(),updated_by=str(user)
                        ) 
                    r = callproc("stp_post_workflow", [wf_id,form_id,status,ref,ser,user,f_remark])
                    if r[0][0] not in (""):
                        messages.success(request, str(r[0][0]))
                    else: messages.error(request, 'Oops...! Something went wrong!')
                return redirect(f'/matrix_flow_cr?wf={encrypt_parameter(wf_id)}&af={encrypt_parameter(form_id)}&ac={ac}')
                
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),user])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally: 
         if request.method == "GET" and sf == '' and f == '' and sb == ''and rb == '' and rb1 == '':
            return render(request,'ContractRegistration/metrix_flow.html', context)

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

def citizen_index_cr(request):
    try:
        if request.method == "GET":
            phone_number = request.session.get("phone_number")
            user_id = None

            if phone_number:
                user = get_object_or_404(CustomUser, phone=phone_number, role_id=2)
                user_id = user.id

            new_id = 1
            countRefusedDocument = None
            refused_id = None
            encrypted_new_id = encrypt_parameter(str(new_id))

            getApplicantData = []
            show_apply_button = False
            
            applicationIndex = callproc("stp_getFormDetailsForTC", [user_id])

            for items in applicationIndex:
                encrypted_id = encrypt_parameter(str(items[1]))
                getApplicantData.append({
                    "srno": items[0],
                    "id": encrypted_id,
                    "request_no": items[2],
                    "name_of_applicant": items[3],
                    "contractor_type": items[4],
                    "status": items[5],
                    "comments": items[6],
                })

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), ""])

    return render(
        request,
        "ContractRegistration/CitizenIndex.html",
        {
            "data": getApplicantData,
            "encrypted_new_id": encrypted_new_id,
            "show_apply_button": show_apply_button,
            "countRefusedDocument": countRefusedDocument,
        },
    )

def citizen_crate_cr(request):
    try:
        phone_number = request.session.get("phone_number")
        user_id = None
        if phone_number:
            user = get_object_or_404(CustomUser, phone=phone_number, role_id=2)
            user_id = user.id

        service_db = request.session.get("service_db", "")
   
        if request.method == "GET":
            message = request.session.pop("message", None)
            form_data = request.session.pop("form_data", None)
            ContractorType = parameter_master.objects.filter(
                parameter_id__in=[23, 24, 25, 26]
            ).values_list("parameter_value", "parameter_value")

            return render(
                request,
                "ContractRegistration/CitizenCreate.html",
                {
                    "ContractorType": ContractorType,
                    # "documentList": documentList,
                    "message": message,
                    "form_data": form_data,
                },
            )

        elif request.method == "POST":
            
            contractor_type = request.POST.get("contractor_type")
            company_name = request.POST.get("applicant_name")
            gstin = request.POST.get("gstin")
            pan_no = request.POST.get("pan_no")
            cin = request.POST.get("cin")
            contact_person_name = request.POST.get("contact_person_name")
            mobile_no = request.POST.get("mobile_no")
            email = request.POST.get("email")

            if not (
                contractor_type
                and company_name
                and gstin
                and pan_no
                and cin
                and contact_person_name
                and mobile_no
                and email
            ):
                messages.error(request, "All fields are required.")
                return redirect("citizen_index_cr")

            mandatory_documents = document_master.objects.filter(
                mandatory=1, is_active=1, doc_type=contractor_type
            )

            all_uploaded = True
            missing_documents = []

            # Check for mandatory documents only
            for document in mandatory_documents:
                # Check if file is not uploaded for mandatory document
                if not request.FILES.get(f"upload_{document.doc_id}"):
                    all_uploaded = False
                    missing_documents.append(document.doc_name)

            if not all_uploaded:
                message = "Please upload the mandatory documents."
                request.session["message"] = message
                request.session["missing_documents"] = missing_documents  # Store missing documents info in session
                request.session["form_data"] = {
                    "contractor_type": contractor_type,
                    "company_name": company_name,
                    "gstin": gstin,
                    "pan_no": pan_no,
                    "cin": cin,
                    "contact_person_name": contact_person_name,
                    "mobile_no": mobile_no,
                    "email": email,
                }
                # Redirect or return appropriate response if documents are missing
                return redirect('citizen_crate_cr')


            application = application_form.objects.create(
                contractor_type=contractor_type,
                company_name=company_name,
                gstin=gstin,
                pan_no=pan_no,
                cin=cin,
                contact_person_name=contact_person_name,
                mobile_no=mobile_no,
                email=email,
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
            return redirect("citizen_view_cr", row_id, new_id)

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user_id])

def citizen_edit_cr(request, row_id, new_id):
    try:
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
            
            contractorType = parameter_master.objects.filter(
                parameter_id__in=[23, 24, 25, 26]
            ).values_list("parameter_value", "parameter_value")
            
            uploaded_documents = citizen_document.objects.filter(
                user_id=user_id, application_id=viewDetails
            )

            for row in uploaded_documents:
                encrypted_filepath = encrypt_parameter(str(row.filepath))
                row.filepath = encrypted_filepath

            uploaded_doc_ids = uploaded_documents.values_list("document_id", flat=True)

            all_documents = document_master.objects.filter(doc_type=viewDetails.contractor_type)

            not_uploaded_documents = all_documents.exclude(doc_id__in=uploaded_doc_ids)

            documentList = document_master.objects.filter(is_active=1, doc_type=viewDetails.contractor_type)

            for document in documentList:
                if document.doc_subpath:
                    document.encrypted_subpath = encrypt_parameter(document.doc_subpath)
                else:
                    document.encrypted_subpath = None


        if request.method == "POST":

            viewDetails = get_object_or_404(application_form, id=row_id)
            viewDetails.company_name = request.POST.get("applicant_name")
            viewDetails.gstin = request.POST.get("gstin")
            viewDetails.pan_no = request.POST.get("pan_no")
            viewDetails.cin = request.POST.get("cin")
            viewDetails.contact_person_name = request.POST.get("contact_person_name")
            viewDetails.mobile_no = request.POST.get("mobile_no")
            viewDetails.email = request.POST.get("email")

            if not all([
                viewDetails.contractor_type, viewDetails.company_name, viewDetails.gstin, 
                viewDetails.pan_no, viewDetails.cin, viewDetails.contact_person_name, 
                viewDetails.mobile_no, viewDetails.email
            ]):
                
                new_id = encrypt_parameter(new_id)
                row_id = encrypt_parameter(row_id)
                message = "All fields are mandatory. Please fill in all fields."
                request.session["message"] = message
                return redirect("citizen_edit_cr", row_id, new_id) 

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

            return redirect("citizen_view_cr", row_id, new_id)

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), ""])
    finally:
        if request.method == "GET":
            return render(
                request,
                "ContractRegistration/CitizenEdit.html",
                {
                    "viewDetails": viewDetails,
                    "contractorType": contractorType,
                    "uploaded_documents": uploaded_documents,
                    "not_uploaded_documents": not_uploaded_documents,
                    "new_id": new_id,
                    "message": message,
                },
            )
        # else:
        #     new_id = 0
        #     new_id = encrypt_parameter(str(new_id))
        #     row_id = encrypt_parameter(str(row_id))

        #     return redirect("application_Master_View_TT", row_id, new_id)

def citizen_view_cr(request, row_id, new_id):
    try:
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
            
            uploaded_documents = citizen_document.objects.filter(
                user_id=user_id, application_id=viewDetails.id
            )

            for row in uploaded_documents:
                if row.filepath:
                    row.filepath = encrypt_parameter(str(row.filepath))
                
            plain_new_id = new_id
            new_id = str(encrypt_parameter(str(new_id)))
            row_id = str(encrypt_parameter(str(row_id1)))

        if request.method == "POST":

            row_id = int(decrypt_parameter(str(row_id)))
            application = get_object_or_404(application_form, id=row_id)
            viewDetails = get_object_or_404(application_form, id=row_id)
            
            servicefetch = service_master.objects.using("default").get(
                ser_id=service_db
            )
            service_name = servicefetch.ser_name

            application_id = int(application.id)
            if application.status_id == 4:
                application.status_id = 9
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
                    request.session["applicationId"]=str(service[0][0])
                    request.session["application_status"]=str(3)
                    request.session["workflow_id"] = workflow.id
                    request.session["form_id"]=application.id
                    request.session["form_user_id"]=str(user_id)                    
                    upd_citizen(request)
    
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), ""])
        logger.error(f"Error in applicationFormIndexTT: {str(e)}")

    finally:
        if request.method == "GET":
            return render(
                request,
                "ContractRegistration/CitizenView.html",
                {
                    "form_data": viewDetails,
                    "uploaded_documents": uploaded_documents,
                    "new_id": new_id,
                    "row_id": row_id,
                    "plain_new_id": plain_new_id,
                },
            )
        else:
            return redirect("citizen_index_cr")

def create_partial_view(request):
    try:
        if request.method == "POST":
            contractor_type = request.POST.get('contractorType')  
            phone_number = request.session.get("phone_number")
            user_id = None
            if phone_number:
                user = get_object_or_404(CustomUser, phone=phone_number, role_id=2)
                user_id = user.id
                service_db = request.session.get("service_db", "default")
            
            documents = document_master.objects.filter(doc_type=contractor_type, is_active=1)

            document_list = []
            for document in documents:
                document_list.append({
                    'doc_id': document.doc_id,
                    'doc_name': document.doc_name,
                    'doc_subpath': document.doc_subpath,
                    'mandatory': document.mandatory,
                    'encrypted_subpath': document.doc_subpath,  # Assuming you want to send the encrypted path
                    'doc_type': document.doc_type
            })

            # Send back a JsonResponse with data
            return JsonResponse({
                "message": "Data processed successfully",
                "documentList": document_list
            })


    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        # Log the error
        callproc("stp_error_log", [fun, str(e), ""])
        return JsonResponse({
            "error": "An error occurred", 
            "details": str(e)
        }, status=500)
    
def citizen_delete_cr(request, row_id, new_id):
    try:
        phone_number = request.session.get("phone_number")
        user_id = None
        if phone_number:
            user = get_object_or_404(CustomUser, phone=phone_number, role_id=2)
            user_id = user.id

        service_db = request.session.get("service_db", "default")

        new_id = decrypt_parameter(new_id)
        row_id = decrypt_parameter(row_id)

        application_form.objects.filter(id=row_id).delete()

        return redirect("citizen_index_cr")

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), ""])