import json
import pydoc
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import authenticate, login ,logout,get_user_model
from Account.forms import RegistrationForm
from Account.models import *
from Masters.models import *
import Db 
import bcrypt
from django.contrib.auth.decorators import login_required
from CSH.encryption import *
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph
from Account.utils import decrypt_email, encrypt_email
import requests
import traceback
import pandas as pd
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.contrib import messages
import openpyxl
from openpyxl.styles import Font, Border, Side
import calendar
from datetime import datetime, timedelta
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q, Count

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import AccessToken
from django.utils import timezone
from Account.models import *
from Masters.models import *
from Account.db_utils import callproc
from django.views.decorators.csrf import csrf_exempt
import os
from django.urls import reverse
from CSH.settings import *
import logging
logger = logging.getLogger(__name__)

@login_required
def masters(request):
    pre_url = request.META.get('HTTP_REFERER')
    header, data = [], []
    entity, type, name = '', '', ''
    global user
    user  = request.session.get('user_id', '')
    try:
         
        if request.method=="GET":
            entity = request.GET.get('entity', '')
            type = request.GET.get('type', '')
            datalist1= callproc("stp_get_masters",[entity,type,'name',user])
            name = datalist1[0][0]
            header = callproc("stp_get_masters", [entity, type, 'header',user])
            rows = callproc("stp_get_masters",[entity,type,'data',user])
            data = []
            if (entity == 'em' or entity == 'sm' or entity == 'cm' or entity == 'menu' or entity == 'user') and type !='err': 
                for row in rows:
                    encrypted_id = encrypt_parameter(str(row[0]))
                    data.append((encrypted_id,) + row[1:])
            else:data = rows

        if request.method=="POST":
            entity = request.POST.get('entity', '')
            type = request.POST.get('type', '')
            messages.success(request, 'Data updated successfully !')
                          
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),user])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally:
        Db.closeConnection()
        if request.method=="GET":
            return render(request,'Master/index.html', {'entity':entity,'type':type,'name':name,'header':header,'data':data,'pre_url':pre_url})
        elif request.method=="POST":  
            new_url = f'/masters?entity={entity}&type={type}'
            return redirect(new_url) 
        
def gen_roster_xlsx_col(columns,month_input):
    year, month = map(int, month_input.split('-'))
    _, num_days = calendar.monthrange(year, month)
    date_columns = [(datetime(year, month, day)).strftime('%d-%m-%Y') for day in range(1, num_days + 1)]
    columns.extend(date_columns)
    return columns
        
def sample_xlsx(request):
    pre_url = request.META.get('HTTP_REFERER')
    response =''
    global user
    user  = request.session.get('user_id', '')
    try:
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = 'Sample Format'
        columns = []
        if request.method=="GET":
            entity = request.GET.get('entity', '')
            type = request.GET.get('type', '')
        if request.method=="POST":
            entity = request.POST.get('entity', '')
            type = request.POST.get('type', '')
        file_name = {'em': 'Employee Master','sm': 'Worksite Master','cm': 'Company Master','r': 'Roster'}[entity]
        columns = callproc("stp_get_masters", [entity, type, 'sample_xlsx',user])
        if columns and columns[0]:
            columns = [col[0] for col in columns[0]]
        if entity == "r":
            month = request.POST.get('month', '')
            columns = gen_roster_xlsx_col(columns,month)

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
        messages.error(request, 'Oops...! Something went wrong!')
    finally:
        return response      

@login_required  
def roster_upload(request):
    global user
    user  = request.session.get('user_id', '')
    if request.method == 'POST' and request.FILES.get('roster_file'):
        try:
            excel_file = request.FILES['roster_file']
            file_name = excel_file.name
            df = pd.read_excel(excel_file)

            entity = request.POST.get('entity', '')
            type = request.POST.get('type', '')
            company_id = request.POST.get('company_id', '')
            month_input  =str(request.POST.get('month_year', ''))
            total_rows = len(df)
            update_count = error_count = success_count = 0
            checksum_id = None
            worksites = []

            if entity == 'r':
                year, month = map(int, month_input.split('-'))
                _, num_days = calendar.monthrange(year, month)
                date_columns = [(datetime(year, month, day)).strftime('%d-%m-%Y') for day in range(1, num_days + 1)]
                start_columns = callproc("stp_get_masters", [entity, type, 'sample_xlsx',user])
                if start_columns and start_columns[0]:
                    start_columns = [col[0] for col in start_columns[0]]

                if not all(col in df.columns for col in start_columns + date_columns):
                    messages.error(request, 'Oops...! The uploaded Excel file does not contain the required columns.!')
                    return redirect(f'/masters?entity={entity}&type={type}')
                
                c = callproc('stp_insert_checksum', ('roster',company_id,month,year,file_name))

                checksum_id = c[0][0]
                
                for index,row in df.iterrows():
                    employee_id = row.get('Employee Id', '')
                    employee_name = row.get('Employee Name', '')
                    worksite  = row.get('Worksite', '')
                    
                    for date_col in date_columns:
                        shift_date = datetime.strptime(date_col, '%d-%m-%Y').date()
                        shift_time = row.get(date_col) 
                        if pd.isna(shift_time):
                            shift_time = None
                        params = (str(employee_id),employee_name,int(company_id),worksite,shift_date,shift_time,checksum_id,user)
                        r = callproc('stp_insert_roster', params)
                        if r[0][0] not in ("success", "updated"):
                            if worksite not in worksites:
                                worksites.append(worksite)
                            error_message = str(r[0][0])
                            error_params = ('roster', company_id,worksite,file_name,shift_date,error_message,checksum_id)
                            callproc('stp_insert_error_log', error_params)
                            messages.error(request, "Errors occurred during upload. Please check error logs.")
                    if r[0][0] == "success": success_count += 1
                    elif r[0][0] == "updated": update_count += 1  
                    else: error_count += 1
                checksum_msg = f"Total Rows Processed: {total_rows}, Successful Entries: {success_count}, Updates: {update_count}, Errors: {error_count}"
                callproc('stp_update_checksum', ('roster',company_id,', '.join(worksites),month,year,file_name,checksum_msg,error_count,update_count,checksum_id))
                if error_count == 0 and update_count == 0 and success_count > 0:
                    messages.success(request, f"All data uploaded successfully!.")
                elif error_count == 0 and success_count == 0 and update_count > 0:
                    messages.warning(request, f"All data updated successfully!.")
                else:
                    messages.warning(request, f"The upload processed {total_rows} rows, resulting in {success_count} successful entries, {update_count} updates, and {error_count} errors; please check the error logs for details.")
                    
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            fun = tb[0].name
            callproc("stp_error_log", [fun, str(e), user])  
            messages.error(request, 'Oops...! Something went wrong!')

        finally:
            return redirect(f'/masters?entity={entity}&type={type}')     
        
@login_required        
def site_master(request):
    global user
    user  = request.session.get('user_id', '')
    try:
        
        if request.method == "GET":
            roster_types = callproc("stp_get_roster_type")
            company_names = callproc("stp_get_company_names")
            site_id = request.GET.get('site_id', '')
            if site_id == "0":
                if request.method == "GET":
                    context = {'company_names': company_names, 'roster_type': roster_types,'site_id':site_id}

            else:
                site_id1 = request.GET.get('site_id', '')
                site_id = decrypt_parameter(site_id1)
                data = callproc("stp_edit_site_master", (site_id,)) 
                if data and data[0]:
                    data = data[0][0]
                    context = {
                        'roster_types':roster_types,
                        'company_names':company_names,
                        'site_id' : data[0],
                        'site_name': data[1],
                        'site_address': data[2],
                        'pincode': data[3],
                        'contact_person_name': data[4],
                        'contact_person_email': data[5], 
                        'contact_person_mobile_no': data[6],
                        'is_active':data[7],
                        'no_of_days': data[8],               
                        'notification_time': data[9],
                        'reminder_time': data[10],
                        'company_name' :data[11],
                        'roster_type': data[13]
                    }

        if request.method == "POST":
            siteId = request.POST.get('site_id', '')
            if siteId == "0":
                response_data = {"status": "fail"}
                
                siteName = request.POST.get('siteName', '')
                siteAddress = request.POST.get('siteAddress', '')
                pincode = request.POST.get('pincode', '')
                contactPersonName = request.POST.get('contactPersonName', '')
                contactPersonEmail = request.POST.get('contactPersonEmail', '')
                contactPersonMobileNo = request.POST.get('Number', '')  
                # is_active = request.POST.get('status_value', '') 
                # noOfDays = request.POST.get('FieldDays', '')  
                # notificationTime = request.POST.get('notificationTime', '')
                # ReminderTime = request.POST.get('ReminderTime', '')
                companyId = request.POST.get('company_id', '')  
                # rosterType = request.POST.get('roster_type', '')
               
                params = [
                    siteName, 
                    siteAddress, 
                    pincode, 
                    contactPersonName, 
                    contactPersonEmail, 
                    contactPersonMobileNo, 
                    # is_active,
                    # noOfDays, 
                    # notificationTime, 
                    # ReminderTime, 
                    companyId
                    # rosterType
                ]
                
                datalist = callproc("stp_insert_site_master", params)
                if datalist[0][0] == "success":
                    messages.success(request, 'Data successfully entered !')
                else: messages.error(request, datalist[0][0])
            else:
                if request.method == "POST" :
                    siteId = request.POST.get('site_id', '')
                    siteName = request.POST.get('siteName', '')
                    siteAddress = request.POST.get('siteAddress', '')
                    pincode = request.POST.get('pincode', '')
                    contactPersonName = request.POST.get('contactPersonName', '')
                    contactPersonEmail = request.POST.get('contactPersonEmail', '')
                    contactPersonMobileNo = request.POST.get('Number', '')  
                    # noOfDays = request.POST.get('FieldDays', '') 
                    isActive = request.POST.get('status_value', '')
                    # notificationTime = request.POST.get('notificationTime', '')
                    # ReminderTime = request.POST.get('ReminderTime', '')
                    CompanyId = request.POST.get('company_id', '')
                    # Rostertype = request.POST.get('roster_type', '')
                    
                    params = [siteId,siteName,siteAddress,pincode,contactPersonName,contactPersonEmail,
                                        contactPersonMobileNo,isActive,CompanyId]
                    callproc("stp_update_site_master",params) 
                    messages.success(request, "Data updated successfully...!")

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally:
        if request.method=="GET":
            return render(request, "Master/site_master.html", context)
        elif request.method=="POST":  
            return redirect( f'/masters?entity=sm&type=i')
        
@login_required      
def company_master(request):
    global user
    user  = request.session.get('user_id', '')
    try:
        if request.method == "GET":
        
            company_id = request.GET.get('company_id', '')
            if company_id == "0":
                if request.method == "GET":
                    context = {'company_id':company_id}
            else:
                company_id1 = request.GET.get('company_id', '')
                company_id= decrypt_parameter(company_id1)
                data = callproc("stp_edit_company_master", (company_id,))  # Note the comma to make it a tuple
                if data and data[0]:
                    data = data[0][0]
                    context = {
                        'company_id' : data[0],
                        'company_name': data[1],
                        'company_address': data[2],
                        'pincode': data[3],
                        'contact_person_name': data[4],
                        'contact_person_email': data[5], 
                        'contact_person_mobile_no': data[6],
                        'is_active':data[7]
                    }

        if request.method == "POST" :
            company_id = request.POST.get('company_id', '')
            if company_id == '0':
                response_data = {"status": "fail"}
                company_name = request.POST.get('company_name', '')
                company_address = request.POST.get('company_address', '')
                pincode = request.POST.get('pincode', '')
                contact_person_name = request.POST.get('contact_person_name', '')
                contact_person_email = request.POST.get('contact_person_email', '')
                contact_person_mobile_no = request.POST.get('contact_person_mobile_no', '') 
                # is_active = request.POST.get('status_value', '') 
                params = [
                    company_name, 
                    company_address, 
                    pincode, 
                    contact_person_name,
                    contact_person_email,
                    contact_person_mobile_no
                    # is_active
                ]
                datalist = callproc("stp_insert_company_master", params)
                if datalist[0][0] == "success":
                    messages.success(request, 'Data successfully entered !')
                else: messages.error(request, datalist[0][0])
            else :
                company_id = request.POST.get('company_id', '')
                company_name = request.POST.get('company_name', '')
                company_address = request.POST.get('company_address', '')
                pincode = request.POST.get('pincode', '')
                contact_person_name = request.POST.get('contact_person_name', '')
                contact_person_email = request.POST.get('contact_person_email', '')
                contact_person_mobile_no = request.POST.get('contact_person_mobile_no', '') 
                is_active = request.POST.get('status_value', '') 
                   
                params = [company_id,company_name,company_address,pincode,contact_person_name,contact_person_email,
                                            contact_person_mobile_no,is_active]    
                callproc("stp_update_company_master",params) 
                messages.success(request, "Data updated successfully ...!")
                
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally:
        if request.method=="GET":
            return render(request, "Master/company_master.html", context)
        elif request.method == "POST":
            return redirect(f'/masters?entity=cm&type=i')

@login_required        
def employee_master(request):
    global user
    user  = request.session.get('user_id', '')
    try:
        if request.method == "GET":
            id = request.GET.get('id', '')
            employee_status = callproc("stp_get_employee_status")
            site_name= callproc("stp_get_dropdown_values",('site',))
            if id == "0":
                if request.method == "GET":
                    context = {'id':id, 'employee_status':employee_status, 'employee_status_id': '','site_name':site_name}
            else:
                id1 = request.GET.get('id', '')
                id = decrypt_parameter(id1)
                data = callproc("stp_edit_employee_master", (id,))
                if data and data[0]:
                    data = data[0][0] 
                    context = {
                        'site_name':site_name,
                        'employee_status':employee_status,
                        'id':data[0],
                        'employee_id' : data[1],
                        'employee_name': data[2],
                        'mobile_no': data[3],
                        'site_name_value': data[4],
                        'employee_status_id': data[5],
                        'is_active': data[6]
                    }

        if request.method == "POST" :
            id = request.POST.get('id', '')
            if id == '0':
                employeeId = request.POST.get('employee_id', '')
                employeeName = request.POST.get('employee_name', '')
                mobileNo = request.POST.get('mobile_no', '')
                site_name = request.POST.get('site_name', '')
                # employeeStatus = request.POST.get('employee_status_name', '')
                # activebtn = request.POST.get('status_value', '')
                params = [
                    employeeId, 
                    employeeName, 
                    mobileNo, 
                    site_name
                    # employeeStatus,
                    # activebtn
                ]
                
                datalist = callproc("stp_insert_employee_master", params)
                if datalist[0][0] == "success":
                    messages.success(request, 'Data successfully entered !')
                else: messages.error(request, datalist[0][0])
            else:
                id = request.POST.get('id', '')
                employee_id = request.POST.get('employee_id', '')
                employee_name = request.POST.get('employee_name', '')
                mobile_no = request.POST.get('mobile_no', '')
                site_name = request.POST.get('site_name', '')
                employee_status = request.POST.get('employee_status_name', '')
                is_active = request.POST.get('status_value', '')  
                            
                params = [id,employee_id,employee_name,mobile_no,site_name,employee_status,is_active]    
                callproc("stp_update_employee_master",params) 
                messages.success(request, "Data successfully Updated!")

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally:
        if request.method=="GET":
            return render(request, "Master/employee_master.html", context)
        elif request.method=="POST":  
            return redirect(f'/masters?entity=em&type=i')

@login_required  
def upload_excel(request):

    if request.method == 'POST' and request.FILES.get('excelFile'):
        excel_file = request.FILES['excelFile']
        file_name = excel_file.name
        df = pd.read_excel(excel_file)
        total_rows = len(df)
        update_count = error_count = success_count = 0
        checksum_id = None
        r=None
        global user
        user  = request.session.get('user_id', '')
        try:
            entity = request.POST.get('entity', '')
            type = request.POST.get('type', '')
            company_id = request.POST.get('company_id', None)
            columns = callproc("stp_get_masters", [entity, type, 'sample_xlsx',user])
            if columns and columns[0]:
                columns = [col[0] for col in columns[0]]
            if not all(col in df.columns for col in columns):
                messages.error(request, 'Oops...! The uploaded Excel file does not contain the required columns.!')
                return redirect(f'/masters?entity={entity}&type={type}')
            upload_for = {'em': 'employee master','sm': 'site master','cm': 'company master','r': 'roster'}[entity]
            c = callproc('stp_insert_checksum', (upload_for,company_id,str(datetime.now().month),str(datetime.now().year),file_name))
            checksum_id = c[0][0]

            if entity == 'em':
                for index,row in df.iterrows():
                    params = tuple(str(row.get(column, '')) for column in columns)
                    r = callproc('stp_insert_employee_master', params)
                    if r[0][0] not in ("success", "updated"):
                        cursor.callproc('stp_insert_error_log', [upload_for, company_id,'',file_name,datetime.now().date(),str(r[0][0]),checksum_id])
                    if r[0][0] == "success": success_count += 1 
                    elif r[0][0] == "updated": update_count += 1  
                    else: error_count += 1
            elif entity == 'sm':
                for index,row in df.iterrows():
                    params = tuple(str(row.get(column, '')) for column in columns)
                    params += (str(company_id),)
                    r = callproc('stp_insert_site_master', params)
                    if r[0][0] not in ("success", "updated"):
                        callproc('stp_insert_error_log', [upload_for, company_id,'',file_name,datetime.now().date(),str(r[0][0]),checksum_id])
                    if r[0][0] == "success": success_count += 1 
                    elif r[0][0] == "updated": update_count += 1  
                    else: error_count += 1
            elif entity == 'cm':
                for index,row in df.iterrows():
                    params = tuple(str(row.get(column, '')) for column in columns)
                    r = callproc('stp_insert_company_master', params)
                    if r[0][0] not in ("success", "updated"):
                        callproc('stp_insert_error_log', [upload_for, company_id,'',file_name,datetime.now().date(),str(r[0][0]),checksum_id])
                    if r[0][0] == "success": success_count += 1 
                    elif r[0][0] == "updated": update_count += 1  
                    else: error_count += 1
            checksum_msg = f"Total Rows Processed: {total_rows}, Successful Entries: {success_count}" f"{f', Updates: {update_count}' if update_count > 0 else ''}" f"{f', Errors: {error_count}' if error_count > 0 else ''}"
            callproc('stp_update_checksum', (upload_for,company_id,'',str(datetime.now().month),str(datetime.now().year),file_name,checksum_msg,error_count,update_count,checksum_id))
            if error_count == 0 and update_count == 0 and success_count > 0:
                messages.success(request, f"All data uploaded successfully!.")
            elif error_count == 0 and success_count == 0 and update_count > 0:
                messages.warning(request, f"All data updated successfully!.")
            else:messages.warning(request, f"The upload processed {total_rows} rows, resulting in {success_count} successful entries"  f"{f', {update_count} updates' if update_count > 0 else ''}" f", and {error_count} errors; please check the error logs for details.")
                   
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            fun = tb[0].name
            callproc("stp_error_log", [fun, str(e), user])  
            messages.error(request, 'Oops...! Something went wrong!')
        finally:
            return redirect(f'/masters?entity={entity}&type=i')

def get_access_control(request):
    company = []
    worksite = []
    global user
    user  = request.session.get('user_id', '')
    try:
        if request.method == "POST":
            type = request.POST.get('type','')
            ur = request.POST.get('ur', '')
            company = callproc("stp_get_access_control_val", [type,ur,'company'])
            worksite = callproc("stp_get_access_control_val", [type,ur,'worksite'])
            if type == 'worksites':
                company_id = request.POST.getlist('company_id','')
                company_ids = ','.join(company_id)
                worksite = callproc("stp_get_access_control_val", [type,company_ids,'worksites'])

            response = {'result': 'success', 'company': company, 'worksite': worksite}
        else: response = {'result': 'fail', 'message': 'Invalid request method'}

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        callproc("stp_error_log", [tb[0].name, str(e), user])
        print(f"error: {e}")
        response = {'result': 'fail', 'message': 'Something went wrong!'}

    finally:
        return JsonResponse(response)

# Verification Form
def VerificationForm(request):
    try:
        return render(request, 'VerificationForm/VerificationForm.html') 
    except Exception as e:
       
        print(f"An error occurred: {e}")
     
        return HttpResponse("An error occurred while rendering the page.", status=500)

# application Form Index
def applicationFormIndex(request):
    try:
        # full_name = request.session.get('full_name')
        phone_number = request.session['phone_number']
        
        if phone_number:
            user = get_object_or_404(CustomUser, phone=phone_number)
            user_id = user.id
        else:
            user_id = None 

        new_id = 1
        new_id_Value = 0
        encrypted_new_id = encrypt_parameter(str(new_id))
        encrypted_new_id_Value = encrypt_parameter(str(new_id_Value))
        
        getApplicantData = []
        show_apply_button = False  

        if request.method == "GET":
            applicationIndex = callproc("stp_getFormDetails", [user_id])
            
            if not applicationIndex:
                show_apply_button = True
            else:
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
                    
                    if items[4] == 'Refused':
                        show_apply_button = True

        return render(request, "ApplicationForm/applicationFormIndex.html", {
            "data": getApplicantData,
            "show_apply_button": show_apply_button,  
            "encrypted_new_id": encrypted_new_id,  
            "encrypted_new_id_Value": encrypted_new_id_Value 
        })

    except Exception as e:
        print(f"Error fetching data: {e}")
        return JsonResponse({"error": "Failed to fetch data"}, status=500)

# application Form Index Aple Sarkar
@csrf_exempt
def aple_sarkar(request):
    try:
        
        getApplicantData = []
            
        if request.method == "POST":
            fullname = request.POST.get('fullname', None)
            email_id = request.POST.get('email', None)
            phone_no = request.POST.get('phone', None)
            
            CustomUser.objects.create(
                full_name=fullname,
                email=email_id,
                phone=phone_no,
            )
    
            m = Db.get_connection()

        # Get Index Data Here
            
            Db.closeConnection()
            m = Db.get_connection()

            applicationIndex = callproc("stp_getFormDetails")
            for items in applicationIndex:
                item = {
                    "srno": items[0],
                    "request_no": items[1],       
                    "name_of_owner": items[2],   
                    "status": items[3],             
                    "comments": items[4]          
                }
                getApplicantData.append(item)

        return render(request,"ApplicationForm/applicationFormIndex.html",{"data": getApplicantData})
        # return render(request,"ApplicationForm/applicationFormIndex.html",{"data": getApplicantData, "status": 1})

    except Exception as e:
        print(f"Error fetching data: {e}")
        return JsonResponse({"error": "Failed to fetch data"}, status=500)
    except Exception as e:
        print(f"An error occurred: {e}")
        return HttpResponse("An error occurred while rendering the page.", status=500)
    
# application Form Create
def applicationMasterCrate(request):
    try:
        
        if request.method == "GET":
            Db.closeConnection()
            m = Db.get_connection()
            cursor = m.cursor()
        
        getDocumentData = document_master.objects.filter(is_active=1) 
        
        # success_message = request.session.pop('success_message', None)
        
        return render(request, 'ApplicationForm/applicationForm.html', {'documents': getDocumentData}) 
    
    except Exception as e:
       
        print(f"An error occurred: {e}")
     
        return HttpResponse("An error occurred while rendering the page.", status=500)

# application Form Create Post
def application_Master_Post(request):
    context = {}  
    try:
        m = Db.get_connection()
        cursor = m.cursor()
        
        global user
        
        if request.method == "POST":
            service_db = request.session.get('service_db', 'default')
            request.session['service_db'] = service_db

            phone_number = request.session.get('phone_number')
            user = CustomUser.objects.get(phone=phone_number)
            full_name_session = request.session['full_name'] = user.full_name
            user_id = user.id

            mandatory_documents = document_master.objects.filter(mandatory=1, is_active=1)
            all_uploaded = True
            missing_documents = []

            for document in mandatory_documents:
                if not request.FILES.get(f'upload_{document.doc_id}'):
                    all_uploaded = False
                    missing_documents.append(document.doc_name)
                    
            if not all_uploaded:
                messages.error(request, 'Please upload the mandatory documents.')
                return redirect('applicationMasterCrate')

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
                created_by=user_id
            )

            user_folder_path = os.path.join(settings.MEDIA_ROOT, f'user_{user_id}')
            application_folder_path = os.path.join(user_folder_path, f'application_{application.id}')
            os.makedirs(application_folder_path, exist_ok=True)

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
                    relative_file_path = f'user_{user_id}/application_{application.id}/document_{document.doc_id}/{file_name}'

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
                                    
            m.commit()
            # messages.success(request, 'Data and files uploaded successfully!')
            # request.session['success_message'] = 'Data and files uploaded successfully!'
            return redirect('viewapplicationform', row_id, new_id)  
            # return redirect('viewapplicationform', row_id=application.id, new_id=0)  

        cursor.close()  
        m.close()  
        
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
        
        if request.method == "GET":
            Db.closeConnection()
            m = Db.get_connection()
            cursor = m.cursor()

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
    file_part, file_extension = os.path.splitext(file_path)
    try:
        if os.path.exists(file_path):
            with open(file_path, 'rb') as file:
                response = HttpResponse(file.read(), content_type='application/pdf')
                response['Content-Disposition'] = f'inline; filename="{os.path.basename(file_name)}"'
                return response
        else:
            return HttpResponse("File not found", status=404)

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),user])  
        logger.error(f"Error downloading file {file_name}: {str(e)}")
        return HttpResponse("An error occurred while trying to download the file.", status=500)
        
# View Application Form 
def viewapplicationform(request, row_id, new_id):
    try:
        context = {} 
        
        row_id = decrypt_parameter(row_id)
        new_id = decrypt_parameter(new_id)
        
        full_name = request.session.get('full_name')
        
        if full_name:
            user = get_object_or_404(CustomUser, full_name=full_name)
            user_id = user.id
        else:
            user_id = None 
            
        application = get_object_or_404(application_form, pk=row_id)
        uploaded_documents = citizen_document.objects.filter(user_id=user_id, application_id=application)
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
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        user = request.user
        callproc("stp_error_log", [fun, str(e), user])
        messages.error(request, 'Oops...! Something went wrong!')

    finally:
        return render(request, 'ApplicationForm/viewapplicationform.html', context)     

# Application Form Final Submit    
def application_Form_Final_Submit(request):
    if request.method == "POST":
        try:
            
            full_name = request.session.get('full_name')

            if full_name:
                user = get_object_or_404(CustomUser, full_name=full_name)
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
            status_id = status_master.objects.get(status_id=application.status_id)
            workflow = workflow_details.objects.filter(form_id=application_id).first()
            workflow.status=status_id
            workflow.updated_at = datetime.now()
            workflow.updated_by = str(user)
            workflow.save()
           
            return redirect('applicationFormIndex')

        except application_form.DoesNotExist:
            return JsonResponse({"error": "Application not found."}, status=404)
        except Exception as e:
            print(f"Error occurred: {e}")
            return JsonResponse({"error": "An unexpected error occurred."}, status=500)

    return render(request, "ApplicationForm/applicationFormIndex.html")

# Edit Application Form
def EditApplicationForm(request, row_id, row_id_status):
    context = {}

    try:
        full_name = request.session.get('full_name')

        if full_name:
            user = get_object_or_404(CustomUser, full_name=full_name)
            user_id = user.id
        else:
            user_id = None
        
        row_id = decrypt_parameter(row_id)
        row_id_status = decrypt_parameter(row_id_status)
        
        application = get_object_or_404(application_form, pk=row_id)

        uploaded_documents = citizen_document.objects.filter(user_id=user_id, application_id=application)
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

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        user = request.user
        callproc("stp_error_log", [fun, str(e), user])
        messages.error(request, 'Oops...! Something went wrong!')

    return render(request, 'ApplicationForm/EditApplicationForm.html', context)
   
# Edit Post Here          
def edit_Post_Application_Master(request, application_id, row_id_status):
    try:
        application = get_object_or_404(application_form, id=application_id)
        
        phone_number = request.session.get('phone_number')
        user = CustomUser.objects.get(phone=phone_number)
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

            user_folder_path = os.path.join(settings.MEDIA_ROOT, f'user_{user_id}')
            application_folder_path = os.path.join(user_folder_path, f'application_{application.id}')
            os.makedirs(application_folder_path, exist_ok=True)

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
                    relative_file_path = f'user_{user_id}/application_{application.id}/document_{document.doc_id}/{file_name}'

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
        return render(request, "ApplicationForm/applicationFormIndex.html")

# Edit Application Form Final Submit
def EditApplicationFormFinalSubmit(request, row_id, row_id_status):
    context = {}

    try:
        full_name = request.session.get('full_name')

        if full_name:
            user = get_object_or_404(CustomUser, full_name=full_name)
            user_id = user.id
        else:
            user_id = None
        
        row_id = decrypt_parameter(row_id)
        row_id_status = decrypt_parameter(row_id_status)
        
        application = get_object_or_404(application_form, pk=row_id)

        uploaded_documents = citizen_document.objects.filter(user_id=user_id, application_id=application)
        
        # for doc in uploaded_documents:
        #     print(f"Document ID: {doc.id}, File Name: {doc.file_name}, "
        #           f"File Path: {doc.filepath}, Comment: {doc.comment}, "
        #           f"Created At: {doc.created_at}, User ID: {doc.user_id}")
            
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
            'MEDIA_URL': MEDIA_ROOT,
            'row_id_status': row_id_status,
        }

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        user = request.user
        callproc("stp_error_log", [fun, str(e), user])
        messages.error(request, 'Oops...! Something went wrong!')

    return render(request, 'ApplicationForm/EditApplicationFormFinalSubmit.html', context)

# Edit Post Here Final Submit        
def edit_Post_Application_Master_final_submit(request, application_id, row_id_status):
    try:
        application = get_object_or_404(application_form, id=application_id)
        
        phone_number = request.session.get('phone_number')
        user = CustomUser.objects.get(phone=phone_number)
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

            user_folder_path = os.path.join(settings.MEDIA_ROOT, f'user_{user_id}')
            application_folder_path = os.path.join(user_folder_path, f'application_{application.id}')
            os.makedirs(application_folder_path, exist_ok=True)

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
                    relative_file_path = f'user_{user_id}/application_{application.id}/document_{document.doc_id}/{file_name}'

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
        return render(request, "ApplicationForm/applicationFormIndex.html")