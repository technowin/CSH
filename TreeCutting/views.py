import json
import os
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, FileResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from Account.forms import RegistrationForm
from Account.models import *
from Masters.models import *
from TreeCutting.models import *
from django.contrib.auth.decorators import login_required
from CSH.encryption import *
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph
from Account.utils import decrypt_email, encrypt_email
import traceback
import pandas as pd
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import openpyxl
from openpyxl.styles import Font, Border, Side
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q, Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import AccessToken
from Account.db_utils import callproc
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
import logging
import mimetypes
from django.db.models import Q, F, Case, When, Value
from Masters.models import document_master, citizen_document_tc

logger = logging.getLogger(__name__)


def applicationFormIndexTC(request):
    try:
        if request.method == "GET":
            phone_number = request.session["phone_number"]

            if phone_number:
                user = get_object_or_404(CustomUser, phone=phone_number, role_id=2)
                user_id = user.id
            else:
                user_id = None

            new_id = 1
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

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), ""])
        logger.error(f"Error in applicationFormIndexTC: {str(e)}")

    finally:
        return render(
            request,
            "TreeCutting/TreeCuttingIndex.html",
            {"data": getApplicantData, "encrypted_new_id": {encrypted_new_id}},
        )


def application_Master_Crate_TC(request):
    try:
        phone_number = request.session.get("phone_number")
        user_id = None
        if phone_number:
            user = get_object_or_404(CustomUser, phone=phone_number, role_id=2)
            user_id = user.id

        service_db = request.session.get("service_db", "default")

        if request.method == "GET":
            message = request.session.pop("message", None)
            form_data = request.session.pop("form_data", None)
            applicantType = parameter_master.objects.filter(
                parameter_id__in=[11, 12]
            ).values_list("parameter_value", "parameter_value")
            ReasonSelect = parameter_master.objects.filter(
                parameter_name="Reason for removal of tree"
            ).values_list("parameter_value", "parameter_value")
            documentList = document_master.objects.filter(is_active=1)

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

            application = application_form_tc.objects.create(
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

                    existing_document = citizen_document_tc.objects.filter(
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
                        citizen_document_tc.objects.create(
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


def application_Master_Edit_TC(request, row_id, new_id):
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

            viewDetails = get_object_or_404(application_form_tc, id=row_id)
            applicantType = parameter_master.objects.filter(
                parameter_id__in=[11, 12]
            ).values_list("parameter_value", "parameter_value")
            ReasonSelect = parameter_master.objects.filter(
                parameter_name="Reason for removal of tree"
            ).values_list("parameter_value", "parameter_value")
            uploaded_documents = citizen_document_tc.objects.filter(
                user_id=user_id, application_id=viewDetails
            ).exclude(document_id=15)

            for row in uploaded_documents:
                encrypted_filepath = encrypt_parameter(str(row.filepath))
                row.filepath = encrypted_filepath

            uploaded_doc_ids = uploaded_documents.values_list("document_id", flat=True)

            all_documents = document_master.objects.all()

            not_uploaded_documents = all_documents.exclude(doc_id__in=uploaded_doc_ids)

            documentList = document_master.objects.filter(is_active=1)

            for document in documentList:
                if document.doc_subpath:
                    document.encrypted_subpath = encrypt_parameter(document.doc_subpath)
                else:
                    document.encrypted_subpath = None

        if request.method == "POST":

            viewDetails = get_object_or_404(application_form_tc, id=row_id)

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

                    existing_document = citizen_document_tc.objects.filter(
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
                        citizen_document_tc.objects.create(
                            user_id=user_id,
                            file_name=file_name,
                            filepath=relative_file_path,
                            document=document,
                            application_id=viewDetails,
                            created_by=user_id,
                            updated_by=user_id,
                        )

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), ""])
    finally:
        if request.method == "GET":
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
                },
            )
        else:
            new_id = 0
            new_id = encrypt_parameter(str(new_id))
            row_id = encrypt_parameter(str(row_id))

            return redirect("application_Master_View_TC", row_id, new_id)


def application_Master_View_TC(request, row_id, new_id):
    try:
        phone_number = request.session.get("phone_number")
        user_id = None
        if phone_number:
            user = get_object_or_404(CustomUser, phone=phone_number, role_id=2)
            user_id = user.id

        if request.method == "GET":

            row_id = decrypt_parameter(row_id)
            new_id = decrypt_parameter(new_id)
            viewDetails = application_form_tc.objects.get(id=row_id)

            uploaded_documents = citizen_document_tc.objects.filter(
                user_id=user_id, application_id=viewDetails.id
            ).exclude(document=15)
            for row in uploaded_documents:
                encrypted_filepath = encrypt_parameter(str(row.filepath))
                row.filepath = encrypted_filepath

            plain_new_id = new_id
            new_id = str(encrypt_parameter(str(new_id)))
            row_id = str(encrypt_parameter(str(row_id)))

        if request.method == "POST":

            row_id = int(decrypt_parameter(str(row_id)))
            application = get_object_or_404(application_form_tc, id=row_id)

            application_id = int(application.id)
            if application.status_id == 4:
                application.status_id = 9
            else:
                application.status_id = 1

            application.save()

            status_instance = status_master.objects.get(status_id=application.status_id)

            workflow, created = workflow_details_tc.objects.get_or_create(
                form_id=application_id,
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
                workflow.updated_by = str(user)
                workflow.save()

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), ""])
        logger.error(f"Error in applicationFormIndexTC: {str(e)}")

    finally:
        if request.method == "GET":
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
        else:
            return redirect("applicationFormIndexTC")
