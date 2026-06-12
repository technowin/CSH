from datetime import datetime
from multiprocessing import context
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render,redirect
from Account.models import *
from Masters.models import *
from aqi.models import *
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

# citizen index view

@no_direct_access
def citizen_index_ac(request):
    try:
        # Session validation
        if not request.session.get('user_id') or not request.session.get('phone_number'):
            request.session['_session_expired'] = True
            
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

            # Get filter parameters from request
            filter_request_no = request.GET.get('request_no', '')
            filter_plot_no = request.GET.get('plot_no', '')
            filter_survey_no = request.GET.get('survey_no', '')
            filter_submission_month = request.GET.get('submission_month', '')
            filter_status = request.GET.get('status', '')

            # Encrypt ID for new application
            new_id = 0
            encrypted_new_id = encrypt_parameter(str(new_id))
            
            # Get all applications for this architect
            getApplicantData = []
            all_applications = []
            applicationIndex = callproc("stp_getAqiApplicationsForCitizen", [user_id])

            # First, collect all applications
            for items in applicationIndex:
                parent_id = items[10] if len(items) > 10 else None
                all_applications.append({
                    "srno": items[0],
                    "id": items[1],
                    "request_no": items[2],
                    "architect_name": items[3],
                    "status": items[4],
                    "submission_month": items[5],
                    "remarks": items[6],
                    "submission_type": items[7] if len(items) > 7 else 'First',
                    "plot_no": items[8] if len(items) > 8 else '',
                    "survey_no": items[9] if len(items) > 9 else '',
                    "parent_application_id": parent_id,
                })
            
            # Find applications to show based on request_no filter
            request_ids_to_show = set()
            
            if filter_request_no:
                # Find the application with matching request_no
                target_app = next((app for app in all_applications if app['request_no'] == filter_request_no), None)
                
                if target_app:
                    # Add the target application itself
                    request_ids_to_show.add(target_app['id'])
                    
                    # If it's a first submission, find all its monthly submissions (children)
                    if target_app['submission_type'] == 'First':
                        for app in all_applications:
                            if app['parent_application_id'] == target_app['id']:
                                request_ids_to_show.add(app['id'])
                    
                    # If it's a monthly submission, find its parent
                    elif target_app['submission_type'] == 'Monthly' and target_app['parent_application_id']:
                        request_ids_to_show.add(target_app['parent_application_id'])
                        # Also find other monthly submissions of the same parent
                        for app in all_applications:
                            if app['parent_application_id'] == target_app['parent_application_id']:
                                request_ids_to_show.add(app['id'])
            
            # Now build the filtered list
            for app in all_applications:
                # Apply request_no filter
                if filter_request_no and app['id'] not in request_ids_to_show:
                    continue
                
                # Apply other filters
                show_row = True
                
                if filter_plot_no and filter_plot_no.lower() not in str(app['plot_no']).lower():
                    show_row = False
                if filter_survey_no and filter_survey_no.lower() not in str(app['survey_no']).lower():
                    show_row = False
                if filter_submission_month and filter_submission_month != app['submission_month']:
                    show_row = False
                if filter_status and filter_status != app['status']:
                    show_row = False
                
                if show_row:
                    encrypted_id = encrypt_parameter(str(app['id']))
                    default_new_id = encrypt_parameter(str(0))
                    item = {
                        "srno": app['srno'],
                        "id": encrypted_id,
                        "default_new_id": default_new_id,
                        "request_no": app['request_no'],
                        "architect_name": app['architect_name'],
                        "status": app['status'],
                        "submission_month": app['submission_month'],
                        "remarks": app['remarks'],
                        "submission_type": app['submission_type'],
                        "plot_no": app['plot_no'],
                        "survey_no": app['survey_no'],
                    }
                    getApplicantData.append(item)
            
            # Get distinct values for filter dropdowns
            distinct_request_nos = sorted(list(set([app['request_no'] for app in all_applications if app['request_no']])))
            distinct_plot_nos = sorted(list(set([app['plot_no'] for app in all_applications if app['plot_no']])))
            distinct_survey_nos = sorted(list(set([app['survey_no'] for app in all_applications if app['survey_no']])))
            distinct_months = sorted(list(set([app['submission_month'] for app in all_applications if app['submission_month']])), reverse=True)
            distinct_statuses = list(set([app['status'] for app in all_applications if app['status']]))
            
            return render(
                request,
                "AQI/AQIIndex.html",
                {
                    "data": getApplicantData, 
                    "encrypted_new_id": encrypted_new_id,
                    "filter_request_no": filter_request_no,
                    "filter_plot_no": filter_plot_no,
                    "filter_survey_no": filter_survey_no,
                    "filter_submission_month": filter_submission_month,
                    "filter_status": filter_status,
                    "distinct_request_nos": distinct_request_nos,
                    "distinct_plot_nos": distinct_plot_nos,
                    "distinct_survey_nos": distinct_survey_nos,
                    "distinct_months": distinct_months,
                    "distinct_statuses": distinct_statuses,
                }
            )

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), ""])
        logger.error(f"Error in citizen_index_ac: {str(e)}")
        messages.error(request, "Something went wrong. Please try again.")
        return redirect('citizenDashboard')

@no_direct_access
def aqi_application_create(request):
    try:
        if not request.session.get('user_id') or not request.session.get('phone_number'):
            request.session['_session_expired'] = True
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
            
            # Get all active documents for AQI (excluding notice documents)
            documentList = document_master.objects.filter(
                is_active=1, 
                doc_type__in=['image', 'pdf']
            ).exclude(
                doc_id__in=[17, 18, 19, 20, 21, 22]  # Exclude officer-only documents
            ).order_by('order_by')

            for document in documentList:
                if document.doc_subpath:
                    document.encrypted_subpath = encrypt_parameter(document.doc_subpath)
                else:
                    document.encrypted_subpath = None

            return render(
                request,
                "AQI/aqiApplicationCreate.html",
                {
                    "documentList": documentList,
                    "message": message,
                    "form_data": form_data,
                },
            )

        elif request.method == "POST":
            # Get form data
            village_name = request.POST.get("village_name")
            bp_fire_no = request.POST.get("bp_fire_no")
            survey_no = request.POST.get("survey_no")
            plot_no = request.POST.get("plot_no")
            architect_name = request.POST.get("architect_name")
            builder_name = request.POST.get("builder_name")
            plot_area = request.POST.get("plot_area")
            latitude = request.POST.get("latitude")
            longitude = request.POST.get("longitude")
            submission_month = request.POST.get("submission_month")
            submission_type = request.POST.get("submission_type", "First")

            # Validate required fields
            if not all([village_name, bp_fire_no, survey_no, plot_no, architect_name, builder_name, plot_area, latitude, longitude, submission_month]):
                messages.error(request, "All fields are required.")
                return redirect("aqi_application_create")

            # NEW VALIDATION: Check if there's an existing application with active notice for same survey_no and plot_no
            existing_application_with_notice = application_form.objects.filter(
                survey_no=survey_no,
                plot_no=plot_no,
                created_by=user_id,
                status_id__in=[9, 10]  # Stop Work Notice Issued (9) or Show Cause Notice Issued (10)
            ).exists()

            if existing_application_with_notice:
                # messages.error(request, "You cannot submit a new application for this Survey No and Plot No as there is an active Stop Work/Show Cause Notice pending. Please resolve the notice first.")
                message = f"You cannot submit a new application for this Survey No and Plot No as there is an active Stop Work/Show Cause Notice pending. Please resolve the notice first."
                request.session["message"] = message
                return redirect("aqi_application_create")

            # Check mandatory documents
            mandatory_documents = document_master.objects.filter(mandatory=1, is_active=1)
            all_uploaded = True
            missing_documents = []

            for document in mandatory_documents:
                if not request.FILES.get(f"upload_{document.doc_id}"):
                    all_uploaded = False
                    missing_documents.append(document.doc_name)

            if not all_uploaded:
                message = f"Please upload the mandatory documents: {', '.join(missing_documents)}"
                request.session["message"] = message
                request.session["form_data"] = {
                    "village_name": village_name,
                    "bp_fire_no": bp_fire_no,
                    "survey_no": survey_no,
                    "plot_no": plot_no,
                    "architect_name": architect_name,
                    "builder_name": builder_name,
                    "plot_area": plot_area,
                    "latitude": latitude,
                    "longitude": longitude,
                    "submission_month": submission_month,
                    "submission_type": submission_type,
                }
                return redirect("aqi_application_create")

            # Get Draft status
            draft_status = status_master.objects.get(status_name='Draft', service_type='AQI')

            # Create application with status_id instead of status
            application = application_form.objects.create(
                village_name=village_name,
                bp_fire_no=bp_fire_no,
                survey_no=survey_no,
                plot_no=plot_no,
                architect_name=architect_name,
                builder_name=builder_name,
                plot_area=plot_area,
                latitude=latitude,
                longitude=longitude,
                submission_month=submission_month,
                submission_type=submission_type,
                is_draft=1,
                status_id=draft_status.status_id,
                created_by=user_id,
            )

            # Create folder structure
            servicefetch = service_master.objects.using("default").get(ser_id=service_db)
            service_name = servicefetch.ser_name

            user_folder_path = os.path.join(settings.MEDIA_ROOT, f"{service_name}")
            os.makedirs(user_folder_path, exist_ok=True)

            user_folder_path = os.path.join(user_folder_path, f"User")
            os.makedirs(user_folder_path, exist_ok=True)

            application_folder_path = os.path.join(
                user_folder_path, f"user_{user_id}", f"aqi_application_{application.id}"
            )
            os.makedirs(application_folder_path, exist_ok=True)

            # Upload documents
            for document in document_master.objects.filter(is_active=1):
                uploaded_file = request.FILES.get(f"upload_{document.doc_id}")

                if uploaded_file:
                    document_folder_path = os.path.join(
                        application_folder_path, f"document_{document.doc_id}"
                    )
                    os.makedirs(document_folder_path, exist_ok=True)

                    # Clear existing files
                    for file_name in os.listdir(document_folder_path):
                        file_path = os.path.join(document_folder_path, file_name)
                        if os.path.isfile(file_path):
                            os.remove(file_path)

                    file_name = uploaded_file.name
                    file_path = os.path.join(document_folder_path, file_name)

                    with open(file_path, "wb+") as destination:
                        for chunk in uploaded_file.chunks():
                            destination.write(chunk)

                    relative_file_path = f"{service_name}/User/user_{user_id}/aqi_application_{application.id}/document_{document.doc_id}/{file_name}"

                    # Save to citizen_document
                    citizen_document.objects.create(
                        user_id=user_id,
                        file_name=file_name,
                        filepath=relative_file_path,
                        doc_id=document.doc_id,
                        application_id=application.id,
                        created_by=user_id,
                        updated_by=user_id,
                    )

            # Instead of redirecting to index, redirect to VIEW
            new_id = 0
            new_id = encrypt_parameter(str(new_id))
            row_id = encrypt_parameter(str(application.id))

            messages.success(request, "Application saved as draft successfully.")
            return redirect("aqi_application_view", row_id, new_id)

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user_id if 'user_id' in locals() else ""])
        logger.error(f"Error in aqi_application_create: {str(e)}")
        messages.error(request, "Something went wrong. Please try again.")
        return redirect("citizen_index_ac")

@no_direct_access
def aqi_application_edit(request, row_id, new_id):
    try:
        if not request.session.get('user_id') or not request.session.get('phone_number'):
            request.session['_session_expired'] = True
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
        
        # Decrypt once at the beginning
        row_id_decrypted = decrypt_parameter(row_id)
        new_id_decrypted = decrypt_parameter(new_id)

        if request.method == "GET":
            message = request.session.pop("message", None)
            viewDetails = get_object_or_404(application_form, id=row_id_decrypted)
            
            # Get uploaded documents
            uploaded_documents = citizen_document.objects.filter(
                user_id=user_id, application_id=viewDetails.id
            )
            
            from Masters.models import document_master as DocumentMaster
            
            for row in uploaded_documents:
                if row.filepath:
                    row.encrypted_filepath = encrypt_parameter(str(row.filepath))
                if row.doc_id:
                    row.document_master = DocumentMaster.objects.filter(doc_id=row.doc_id).first()
            
            # Get list of uploaded document IDs
            uploaded_doc_ids = uploaded_documents.values_list("doc_id", flat=True)
            
            # Check if this is a monthly submission
            if viewDetails.submission_type == 'Monthly':
                # For monthly submission, only show AQI Monitoring Report (doc_id=5)
                all_documents = DocumentMaster.objects.filter(
                    is_active=1, doc_id=5
                ).order_by('order_by')
                not_uploaded_documents = all_documents.exclude(doc_id__in=uploaded_doc_ids)
                document_list = DocumentMaster.objects.filter(
                    is_active=1, doc_id=5
                ).order_by('order_by')
            else:
                # For first submission, show all documents except officer-only
                all_documents = DocumentMaster.objects.filter(
                    is_active=1
                ).exclude(
                    doc_id__in=[17, 18, 19, 20, 21, 22]
                ).order_by('order_by')
                not_uploaded_documents = all_documents.exclude(doc_id__in=uploaded_doc_ids)
                document_list = DocumentMaster.objects.filter(
                    is_active=1
                ).exclude(
                    doc_id__in=[17, 18, 19, 20, 21, 22]
                ).order_by('order_by')
            
            for doc in document_list:
                if doc.doc_subpath:
                    doc.encrypted_subpath = encrypt_parameter(doc.doc_subpath)
                else:
                    doc.encrypted_subpath = None
                    
            parent_request_no = None
            if viewDetails.submission_type == 'Monthly' and viewDetails.parent_application_id:
                parent_app = application_form.objects.filter(id=viewDetails.parent_application_id).first()
                if parent_app:
                    parent_request_no = parent_app.request_no

            return render(
                request,
                "AQI/aqiApplicationEdit.html",
                {
                    "viewDetails": viewDetails,
                    "uploaded_documents": uploaded_documents,
                    "not_uploaded_documents": not_uploaded_documents,
                    "documentList": document_list,
                    "encrypted_row_id": row_id,
                    "encrypted_new_id": new_id,
                    "message": message,
                    "is_monthly_edit": viewDetails.submission_type == 'Monthly',
                    "parent_request_no": parent_request_no,
                },
            )
            
        if request.method == "POST":
            viewDetails = get_object_or_404(application_form, id=row_id_decrypted)
            
            # Update form data
            viewDetails.village_name = request.POST.get("village_name")
            viewDetails.bp_fire_no = request.POST.get("bp_fire_no")
            viewDetails.survey_no = request.POST.get("survey_no")
            viewDetails.plot_no = request.POST.get("plot_no")
            viewDetails.architect_name = request.POST.get("architect_name")
            viewDetails.builder_name = request.POST.get("builder_name")
            viewDetails.plot_area = request.POST.get("plot_area")
            viewDetails.latitude = request.POST.get("latitude")
            viewDetails.longitude = request.POST.get("longitude")
            viewDetails.submission_month = request.POST.get("submission_month")
            viewDetails.submission_type = request.POST.get("submission_type", "First")
            
            # For monthly submission, update monthly fields
            if viewDetails.submission_type == 'Monthly':
                viewDetails.monthly_aqi_value = request.POST.get("monthly_aqi_value")
                viewDetails.monthly_aqi_category = request.POST.get("monthly_aqi_category")
                viewDetails.monthly_remarks = request.POST.get("monthly_remarks")
            
            # Validate required fields
            required_fields = [viewDetails.village_name, viewDetails.bp_fire_no, viewDetails.survey_no, 
                               viewDetails.plot_no, viewDetails.architect_name, viewDetails.builder_name,
                               viewDetails.plot_area, viewDetails.latitude, viewDetails.longitude, 
                               viewDetails.submission_month]
            
            if not all(required_fields):
                new_id_encrypted = encrypt_parameter(str(new_id_decrypted))
                row_id_encrypted = encrypt_parameter(str(row_id_decrypted))
                message = "All fields are mandatory. Please fill in all fields."
                request.session["message"] = message
                return redirect("aqi_application_edit", row_id_encrypted, new_id_encrypted)
            
            # For monthly submission, validate AQI value
            if viewDetails.submission_type == 'Monthly' and not viewDetails.monthly_aqi_value:
                new_id_encrypted = encrypt_parameter(str(new_id_decrypted))
                row_id_encrypted = encrypt_parameter(str(row_id_decrypted))
                message = "AQI Value is mandatory for monthly submission."
                request.session["message"] = message
                return redirect("aqi_application_edit", row_id_encrypted, new_id_encrypted)

            viewDetails.updated_by = user_id
            viewDetails.save()

            # Folder structure for documents
            servicefetch = service_master.objects.using("default").get(ser_id=service_db)
            service_name = servicefetch.ser_name

            user_folder_path = os.path.join(settings.MEDIA_ROOT, f"{service_name}")
            os.makedirs(user_folder_path, exist_ok=True)

            user_folder_path = os.path.join(user_folder_path, f"User")
            os.makedirs(user_folder_path, exist_ok=True)

            application_folder_path = os.path.join(
                user_folder_path, f"user_{user_id}", f"aqi_application_{viewDetails.id}"
            )
            os.makedirs(application_folder_path, exist_ok=True)

            from Masters.models import document_master as DocumentMaster
            
            # For monthly submission, only process doc_id=5
            if viewDetails.submission_type == 'Monthly':
                documents_to_process = DocumentMaster.objects.filter(doc_id=5)
            else:
                documents_to_process = DocumentMaster.objects.filter(is_active=1)
            
            for document in documents_to_process:
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

                    relative_file_path = f"{service_name}/User/user_{user_id}/aqi_application_{viewDetails.id}/document_{document.doc_id}/{file_name}"

                    existing_document = citizen_document.objects.filter(
                        user_id=user_id,
                        doc_id=document.doc_id,
                        application_id=viewDetails.id,
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
                            doc_id=document.doc_id,
                            application_id=viewDetails.id,
                            created_by=user_id,
                            updated_by=user_id,
                        )
            
            new_id_encrypted = encrypt_parameter(str(new_id_decrypted))
            row_id_encrypted = encrypt_parameter(str(row_id_decrypted))
            
            messages.success(request, "Application updated successfully.")
            return redirect("aqi_application_view", row_id_encrypted, new_id_encrypted)

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user_id if 'user_id' in locals() else ""])
        logger.error(f"Error in aqi_application_edit: {str(e)}")
        messages.error(request, "Something went wrong. Please try again.")
        return redirect("citizen_index_ac")

@no_direct_access
def aqi_application_view(request, row_id, new_id):
    try:
        if not request.session.get('user_id') or not request.session.get('phone_number'):
            request.session['_session_expired'] = True
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

        row_id_decrypted = int(decrypt_parameter(row_id))
        new_id_decrypted = decrypt_parameter(new_id)

        if request.method == "GET":
            viewDetails = get_object_or_404(application_form, id=row_id_decrypted)
            
            # Get uploaded documents
            uploaded_documents = citizen_document.objects.filter(
                user_id=user_id, application_id=viewDetails.id
            )
            
            from Masters.models import document_master
            for row in uploaded_documents:
                if row.filepath:
                    row.encrypted_filepath = encrypt_parameter(str(row.filepath))
                if row.doc_id:
                    row.document_master = document_master.objects.filter(doc_id=row.doc_id).first()
            
            plain_new_id = new_id_decrypted
            new_id_encrypted = str(encrypt_parameter(str(new_id_decrypted)))
            row_id_encrypted = str(encrypt_parameter(str(row_id_decrypted)))
            
            # Get parent request_no for monthly submissions
            parent_request_no = None
            if viewDetails.submission_type == 'Monthly' and viewDetails.parent_application_id:
                parent_app = application_form.objects.filter(id=viewDetails.parent_application_id).first()
                if parent_app:
                    parent_request_no = parent_app.request_no

            return render(
                request,
                "AQI/aqiApplicationView.html",
                {
                    "viewDetails": viewDetails,
                    "uploaded_documents": uploaded_documents,
                    "new_id": new_id_encrypted,
                    "row_id": row_id_encrypted,
                    "plain_new_id": plain_new_id,
                    "parent_request_no": parent_request_no,
                },
            )
        
        if request.method == "POST":
            application = get_object_or_404(application_form, id=row_id_decrypted)
            
            # Check if application was refused and needs resubmission
            if application.status_id == 4:  # Refused status
                # Change to Resubmitted status (11) instead of New
                resubmitted_status = status_master.objects.get(status_name='Resubmitted', service_type='AQI')
                application.status_id = resubmitted_status.status_id
                application.is_draft = 0
                application.save()
                
                # Update existing workflow instead of creating new
                workflow = workflow_details.objects.get(form_id=application.id)
                workflow.status_id = resubmitted_status.status_id
                workflow.level = 1  # Back to level 1 (Scrutiny)
                # workflow.forward = None
                # workflow.send_forward = None
                workflow.updated_at = timezone.now()
                workflow.updated_by = str(user_id)
                workflow.save()
                
                messages.success(request, "Application resubmitted successfully!")
                return redirect("citizen_index_ac")
                
            elif application.is_draft == 1:
                # Normal submission (existing code)
                application.is_draft = 0
                new_status = status_master.objects.get(status_name='New', service_type='AQI')
                application.status_id = new_status.status_id
                application.save()
                
                # Create workflow entry
                workflow = workflow_details.objects.create(
                    form_id=application.id,
                    status_id=new_status.status_id,
                    created_by=str(user_id),
                    form_user_id=user_id,
                    level=1,
                    created_at=timezone.now(),
                )
                
                workflow_id = workflow.id
                
                # Generate request number
                if application.request_no is None or application.request_no == "":
                    servicefetch = service_master.objects.using("default").get(ser_id=service_db)
                    service_short_name = servicefetch.short_name if servicefetch.short_name else "AQI"
                    request_number = f"{service_short_name}{application.id}{workflow.id}{user_id}"
                    application.request_no = request_number
                    application.save()
                    workflow.request_no = request_number
                    workflow.save()
                
                messages.success(request, "Application submitted successfully!")
            else:
                messages.warning(request, "Application already submitted!")
                
            return redirect("citizen_index_ac")
        
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user_id if 'user_id' in locals() else ""])
        logger.error(f"Error in aqi_application_view: {str(e)}")
        messages.error(request, "Something went wrong. Please try again.")
        return redirect("citizen_index_ac")
  
@no_direct_access
def download_notice(request, row_id, doc_id):
    try:
        phone_number = request.session.get('phone_number')
        user = CustomUser.objects.get(phone=phone_number, role_id=2)
        
        # Decrypt row_id
        row_id = decrypt_parameter(row_id)
        
        # Get the notice document from citizen_document
        citizen_doc = citizen_document.objects.filter(
            application_id=row_id, 
            doc_id=doc_id
        ).first()
        
        if not citizen_doc or not citizen_doc.filepath:
            return redirect(f"{request.META.get('HTTP_REFERER', 'citizen_index_ac')}?doc_status=not_uploaded")
        
        # Check if file exists
        file_path = os.path.join(settings.MEDIA_ROOT, citizen_doc.filepath)
        if not os.path.exists(file_path):
            return redirect(f"{request.META.get('HTTP_REFERER', 'citizen_index_ac')}?doc_status=not_uploaded")
        
        # Encrypt filepath and redirect to download_doc
        encrypted_filepath = encrypt_parameter(citizen_doc.filepath)
        return redirect('download_doc', encrypted_filepath)
        
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name if tb else "download_notice"
        callproc("stp_error_log", [fun, str(e), user.id if 'user' in locals() else None])
        logger.error(f"Error in download_notice: {str(e)}")
        return redirect(f"{request.META.get('HTTP_REFERER', 'citizen_index_ac')}?doc_status=not_uploaded")

@no_direct_access
def aqi_monthly_create(request, parent_id):
    try:
        # Session validation
        if not request.session.get('user_id') or not request.session.get('phone_number'):
            request.session['_session_expired'] = True
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
        
        # Decrypt parent_id
        parent_id_decrypted = decrypt_parameter(parent_id)
        
        # Get parent application
        parent_application = get_object_or_404(application_form, id=parent_id_decrypted, created_by=user_id)
        parent_request_no = parent_application.request_no
        
        # Check if monthly submission already exists for current month
        current_month = timezone.now().strftime('%Y-%m')
        existing_monthly = application_form.objects.filter(
            parent_application_id=parent_id_decrypted,
            submission_month=current_month,
            created_by=user_id
        ).exists()
        
        if request.method == "GET":
            message = request.session.pop("message", None)
            form_data = request.session.pop("form_data", None)
            
            # Get documents - for monthly, only show AQI Monitoring Report (doc_id=5)
            documentList = document_master.objects.filter(
                is_active=1,
                doc_type__in=['image', 'pdf']
            ).exclude(
                doc_id__in=[17, 18, 19, 20, 21, 22]
            ).order_by('order_by')
            
            # For monthly submission, only keep doc_id=5
            documentList = documentList.filter(doc_id=5)
            
            for document in documentList:
                if document.doc_subpath:
                    document.encrypted_subpath = encrypt_parameter(document.doc_subpath)
                else:
                    document.encrypted_subpath = None
            
            # Pre-filled data from parent
            pre_filled_data = {
                'village_name': parent_application.village_name,
                'survey_no': parent_application.survey_no,
                'plot_no': parent_application.plot_no,
                'bp_fire_no': parent_application.bp_fire_no,
                'architect_name': parent_application.architect_name,
                'builder_name': parent_application.builder_name,
                'plot_area': parent_application.plot_area,
                'latitude': parent_application.latitude,
                'longitude': parent_application.longitude,
                
            }
            
            return render(
                request,
                "AQI/aqiApplicationCreate.html",
                {
                    "documentList": documentList,
                    "parent_id": parent_id,
                    "pre_filled_data": pre_filled_data,
                    "message": message,
                    "form_data": form_data,
                    "current_month": current_month,
                    "is_monthly_submission": True,  # Flag to indicate monthly submission
                    "existing_monthly": existing_monthly,
                    "parent_request_no": parent_request_no, 
                },
            )
        
        elif request.method == "POST":
            # Get form data
            submission_month = request.POST.get("submission_month")
            monthly_aqi_value = request.POST.get("monthly_aqi_value")
            monthly_aqi_category = request.POST.get("monthly_aqi_category")
            monthly_remarks = request.POST.get("monthly_remarks")
            
            # Get pre-filled data from hidden fields or parent
            village_name = request.POST.get("village_name") or parent_application.village_name
            bp_fire_no = request.POST.get("bp_fire_no") or parent_application.bp_fire_no
            survey_no = request.POST.get("survey_no") or parent_application.survey_no
            plot_no = request.POST.get("plot_no") or parent_application.plot_no
            architect_name = request.POST.get("architect_name") or parent_application.architect_name
            builder_name = request.POST.get("builder_name") or parent_application.builder_name
            plot_area = request.POST.get("plot_area") or parent_application.plot_area
            latitude = request.POST.get("latitude") or parent_application.latitude
            longitude = request.POST.get("longitude") or parent_application.longitude
            
            # Validate required fields
            if not all([submission_month, monthly_aqi_value]):
                messages.error(request, "Submission Month and AQI Value are required.")
                return redirect("aqi_monthly_create", parent_id=parent_id)
            
            # Check if monthly submission already exists for this month
            if existing_monthly:
                messages.error(request, f"You have already submitted monthly report for {submission_month}.")
                return redirect("citizen_index_ac")
            
            # Check mandatory document (AQI Monitoring Report - doc_id=5)
            mandatory_documents = document_master.objects.filter(doc_id=5, mandatory=1, is_active=1)
            all_uploaded = True
            
            for document in mandatory_documents:
                if not request.FILES.get(f"upload_{document.doc_id}"):
                    all_uploaded = False
                    break
            
            if not all_uploaded:
                message = "Please upload the AQI Monitoring Report."
                request.session["message"] = message
                request.session["form_data"] = {
                    "submission_month": submission_month,
                    "monthly_aqi_value": monthly_aqi_value,
                    "monthly_aqi_category": monthly_aqi_category,
                    "monthly_remarks": monthly_remarks,
                }
                return redirect("aqi_monthly_create", parent_id=parent_id)
            
            # Get Draft status
            draft_status = status_master.objects.get(status_name='Draft', service_type='AQI')
            
            # Create monthly application
            application = application_form.objects.create(
                village_name=village_name,
                bp_fire_no=bp_fire_no,
                survey_no=survey_no,
                plot_no=plot_no,
                architect_name=architect_name,
                builder_name=builder_name,
                plot_area=plot_area,
                latitude=latitude,
                longitude=longitude,
                submission_month=submission_month,
                submission_type='Monthly',
                is_draft=1,
                status_id=draft_status.status_id,
                parent_application_id=parent_id_decrypted,
                monthly_aqi_value=monthly_aqi_value,
                monthly_aqi_category=monthly_aqi_category,
                monthly_remarks=monthly_remarks,
                created_by=user_id,
            )
            
            # Create folder structure
            servicefetch = service_master.objects.using("default").get(ser_id=service_db)
            service_name = servicefetch.ser_name
            
            user_folder_path = os.path.join(settings.MEDIA_ROOT, f"{service_name}")
            os.makedirs(user_folder_path, exist_ok=True)
            
            user_folder_path = os.path.join(user_folder_path, f"User")
            os.makedirs(user_folder_path, exist_ok=True)
            
            application_folder_path = os.path.join(
                user_folder_path, f"user_{user_id}", f"aqi_application_{application.id}"
            )
            os.makedirs(application_folder_path, exist_ok=True)
            
            # Upload AQI Monitoring Report (doc_id=5)
            for document in document_master.objects.filter(doc_id=5):
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
                    
                    relative_file_path = f"{service_name}/User/user_{user_id}/aqi_application_{application.id}/document_{document.doc_id}/{file_name}"
                    
                    citizen_document.objects.create(
                        user_id=user_id,
                        file_name=file_name,
                        filepath=relative_file_path,
                        doc_id=document.doc_id,
                        application_id=application.id,
                        created_by=user_id,
                        updated_by=user_id,
                    )
            
            # Redirect to VIEW page
            new_id = encrypt_parameter(str(0))
            row_id = encrypt_parameter(str(application.id))
            
            messages.success(request, f"Monthly report for {submission_month} saved as draft successfully.")
            return redirect("aqi_application_view", row_id, new_id)
    
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user_id if 'user_id' in locals() else ""])
        logger.error(f"Error in aqi_monthly_create: {str(e)}")
        messages.error(request, "Something went wrong. Please try again.")
        return redirect("citizen_index_ac")

# Workflow & document models (same table names for both TreeTrimming and AQI)

@login_required 
@no_direct_access
def index_ac(request):
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
        return render(request,'AQI/index.html', context)
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),user])  
        messages.error(request, 'Oops...! Something went wrong!')

@login_required 
@no_direct_access     
def matrix_flow_ac(request):
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
                    return redirect(f'/matrix_flow_ac?wf={encrypt_parameter(wf_id)}&af={encrypt_parameter(form_id)}&ac={ac}')
                else: messages.error(request, 'Oops...! Something went wrong!')
                return redirect(f'/index_ac')
            if f and f !='':
                r = callproc("stp_update_forward",[wf_id,form_id,f,user])
                if r[0][0] == 'success':
                    messages.success(request, "Forwarded successfully !!")
                else: messages.error(request, 'Oops...! Something went wrong!')
                return redirect(f'/matrix_flow_ac?wf={encrypt_parameter(wf_id)}&af={encrypt_parameter(form_id)}&ac={ac}')
            if sb and sb !='':
                r = callproc("stp_update_sendback",[wf_id,form_id,user])
                if r[0][0] == 'success':
                    messages.success(request, "Sendback successfully !!")
                elif r[0][0] == 'wrongsendback':
                    messages.error(request, 'You cannot send it back in the first stage itself.')
                    return redirect(f'/matrix_flow_ac?wf={encrypt_parameter(wf_id)}&af={encrypt_parameter(form_id)}&ac={ac}')
                elif r[0][0] == 'multisendback':
                    messages.error(request, 'Consecutive send-backs are not permitted.')
                    return redirect(f'/matrix_flow_ac?wf={encrypt_parameter(wf_id)}&af={encrypt_parameter(form_id)}&ac={ac}')
                else: messages.error(request, 'Oops...! Something went wrong!')
                return redirect(f'/index_ac')
            if rb and rb !='':
                r = callproc("stp_update_rollback",[wf_id,form_id,user])
                if r[0][0] == 'success':
                    messages.success(request, "Rollback successfully !!")
                elif r[0][0] == 'wrongrollback':
                    messages.error(request, 'You cannot roll it back in the first stage itself.')
                    return redirect(f'/matrix_flow_ac?wf={encrypt_parameter(wf_id)}&af={encrypt_parameter(form_id)}&ac={ac}')
                elif r[0][0] == 'multirollback':
                    messages.error(request, 'Consecutive roll-backs are not permitted.')
                    return redirect(f'/matrix_flow_ac?wf={encrypt_parameter(wf_id)}&af={encrypt_parameter(form_id)}&ac={ac}')
                else: messages.error(request, 'Oops...! Something went wrong!')
                return redirect(f'/index_ac')
            if rb1 and rb1 !='':
                r = callproc("stp_update_rollback1",[wf_id,form_id,user])
                if r[0][0] == 'success':
                    messages.success(request, "Rollback successfully !!")
                elif r[0][0] == 'multirollback':
                    messages.error(request, 'Consecutive roll-backs are not permitted.')
                    return redirect(f'/matrix_flow_ac?wf={encrypt_parameter(wf_id)}&af={encrypt_parameter(form_id)}&ac={ac}')
                else: messages.error(request, 'Oops...! Something went wrong!')
                return redirect(f'/index_ac')
            subordinates = callproc("stp_get_subordinates",[form_id,user])
            user_list = callproc("stp_get_dropdown_values",['marked_for'])
            reject_reasons = callproc("stp_get_dropdown_values",['reject_reasons'])
            citizen_docs = citizen_document.objects.filter(application_id=form_id) 
            for doc_master in document_master.objects.filter(is_active=1).exclude(doc_id__in=[17, 18, 19, 20, 21, 22]):
                # matching_doc = citizen_docs.filter(document=doc_master).first()
                matching_doc = citizen_docs.filter(doc_id=doc_master.doc_id).first()
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
            down_stop_work = encrypt_parameter("sample.pdf")
            down_show_cause = encrypt_parameter("sample.pdf")
            context = {'role_id':role_id,'user_id':request.user.id,'docs':docs,'fields': fields,'header': header,'data': data,'header1': header1,
                       'data1': data1,'subordinates':subordinates,'user_list':user_list,'ac':ac,'wf_id':encrypt_parameter(wf_id),
                       'form_id': encrypt_parameter(form_id),'workflow':workflow,'reject_reasons':reject_reasons,'matrix':matrix,
                       'down_chklst':down_chklst,'down_insp':down_insp,'down_stop_work':down_stop_work,'down_show_cause':down_show_cause,'act_comp':act_comp}
        
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
            
            if response:
                return JsonResponse(response, safe=False)
            
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
                
                elif status in [6, 7] and ref == 'approve':  # Approve (6) or Refuse (7)
                    f_remark = request.POST.get('f_remark', '')
                    
                    # Get uploaded files
                    stop_work_file = request.FILES.get('stop_work_upl_file')
                    show_cause_file = request.FILES.get('show_cause_upl_file')
                    
                    if status == 6:  # Approve - No document needed
                        if f_remark:
                            internal_user_comments.objects.create(
                                workflow=wf, comments=f_remark,
                                created_at=datetime.now(), created_by=str(user),
                                updated_at=datetime.now(), updated_by=str(user)
                            )
                        
                        # Update application_form
                        app = application_form.objects.get(id=form_id)
                        app.status_id = 6  # Approved
                        app.approved_remark = f_remark
                        app.updated_at = timezone.now()
                        app.updated_by = user
                        app.save()
                        
                        # Update workflow_details
                        old_status_id = wf.status_id
                        wf.status_id = 6
                        wf.pre_statusid = old_status_id
                        wf.updated_at = timezone.now()
                        wf.updated_by = str(user)
                        wf.rollback = None
                        wf.save()
                        
                        messages.success(request, "Application Approved successfully!")
                        
                    elif status == 7:  # Refuse - Need at least one notice
                        if not stop_work_file and not show_cause_file:
                            messages.error(request, "Please upload at least one notice document (Stop Work Notice or Show Cause Notice) before refusing.")
                            return redirect(f'/matrix_flow_ac?wf={encrypt_parameter(wf_id)}&af={encrypt_parameter(form_id)}&ac={ac}')
                        
                        # Determine which status to set
                        final_status = 7  # Default Rejected
                        notice_type = ""
                        
                        if stop_work_file:
                            # Upload Stop Work Notice to internal docs
                            internal_docs_upload(stop_work_file, role_id, user, wf, ser, 'Stop Work Notice')
                            
                            # Upload to citizen_document for architect to download
                            stop_work_doc = document_master.objects.filter(doc_id=17).first()  # Stop Work Notice
                            if stop_work_doc:
                                citizen_docs_upload(stop_work_file, form_user_id, form_id, user, ser, stop_work_doc.doc_id)
                            
                            final_status = 9  # Stop Work Notice Issued
                            notice_type = "Stop Work Notice"
                            
                        if show_cause_file:
                            # Upload Show Cause Notice to internal docs
                            internal_docs_upload(show_cause_file, role_id, user, wf, ser, 'Show Cause Notice')
                            
                            # Upload to citizen_document for architect to download
                            show_cause_doc = document_master.objects.filter(doc_id=18).first()  # Show Cause Notice
                            if show_cause_doc:
                                citizen_docs_upload(show_cause_file, form_user_id, form_id, user, ser, show_cause_doc.doc_id)
                            
                            final_status = 10  # Show Cause Notice Issued
                            notice_type = "Show Cause Notice"
                        
                        # If both notices uploaded, prioritize Show Cause Notice
                        if stop_work_file and show_cause_file:
                            final_status = 10  # Show Cause Notice Issued
                            notice_type = "Stop Work & Show Cause Notices"
                        
                        # Add remark as comment
                        if f_remark:
                            internal_user_comments.objects.create(
                                workflow=wf, comments=f_remark,
                                created_at=datetime.now(), created_by=str(user),
                                updated_at=datetime.now(), updated_by=str(user)
                            )
                        
                        # Update application_form
                        app = application_form.objects.get(id=form_id)
                        app.status_id = final_status
                        app.rejected_reason = f_remark
                        app.updated_at = timezone.now()
                        app.updated_by = user
                        app.save()
                        
                        # Update workflow_details
                        old_status_id = wf.status_id
                        wf.status_id = final_status
                        wf.pre_statusid = old_status_id
                        wf.updated_at = timezone.now()
                        wf.updated_by = str(user)
                        wf.rollback = None
                        wf.save()
                        
                        messages.success(request, f"Application Refused. {notice_type} uploaded successfully!")
                    
                return redirect(f'/matrix_flow_ac?wf={encrypt_parameter(wf_id)}&af={encrypt_parameter(form_id)}&ac={ac}')
                
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),user])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally: 
        if request.method == "GET" and sf == '' and f == '' and sb == ''and rb == '' and rb1 == '':
            return render(request,'AQI/metrix_flow.html', context)

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

def citizen_docs_upload(file, user, form_id, created_by, ser, doc_id1):
    file_resp = None
    
    doc = document_master.objects.get(doc_id=doc_id1)
        
    app_form = application_form.objects.get(id=form_id)
    service = service_master.objects.using("default").get(ser_id=ser)
    sub_path = f'{service.ser_name}/User/user_{user}/application_{form_id}/document_{doc.doc_id}/{file.name}'
    full_path = os.path.join(MEDIA_ROOT, sub_path)
    folder_path = os.path.dirname(full_path)
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path, exist_ok=True)
    
    file_exists_in_db = citizen_document.objects.filter(filepath=sub_path).exists()
    
    if file_exists_in_db:
        document = citizen_document.objects.filter(filepath=sub_path).first()
        document.updated_at = datetime.now()
        document.updated_by = str(created_by)  # Use created_by instead of user
        document.save()
        with open(full_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        file_resp = f"File '{file.name}' has been updated."
    else:
        with open(full_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        # FIX: Use doc_id instead of document
        citizen_document.objects.create(
            user_id=user,
            file_name=file.name,
            filepath=sub_path,
            doc_id=doc.doc_id,  # Changed from document=doc to doc_id=doc.doc_id
            application_id=app_form.id,  # Changed from application_id=app_form to application_id=app_form.id
            created_by=str(created_by),
            updated_by=str(created_by),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
       
        file_resp = f"File '{file.name}' has been inserted."
    
    return file_resp

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
    
