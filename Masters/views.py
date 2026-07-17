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
from django.http import FileResponse, Http404
import mimetypes
from django.utils.timezone import now
from django.db.models import Max

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
                        callproc('stp_insert_error_log', [upload_for, company_id,'',file_name,datetime.now().date(),str(r[0][0]),checksum_id])
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
    
def onetimepage(request):
    try:
        if request.method =="GET":
            services = service_master.objects.filter(ser_id__in=[1, 2, 3]).values_list('ser_id', 'ser_name')
            return render(request,'OneTimePage/onetimepage.html',{'services':services}) 
        elif request.method == "POST":
            service_db = request.POST.get('services')
            request.session['service_db'] = service_db
            return redirect(f'/citizenLoginAccount?service_db={service_db}') 
    
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), ''])
        logger.error(f"Error rendering onetimepage.html: {str(e)}")
        return HttpResponse("An error occurred while trying to load the page.", status=500)

# document Master

def documentMaster(request):
    try:
        if request.method == "GET":
            service_id = request.session.get("service_db")  # not used yet, keeping it

            # Fetch all active documents
            documents = document_master.objects.all().order_by('order_by')
            for doc in documents:
                doc.doc_id = encrypt_parameter(str(doc.doc_id))
                
            context = {
                'data': documents,
                'service_id': service_id
            }

            return render(request, 'Master/documentMaster.html', context)

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), ''])
        logger.error(f"Error rendering documentMaster: {str(e)}")
        return HttpResponse("An error occurred while trying to load the page.", status=500)

# Create Document 

def Create_Document_Master(request):
    try:
        if request.method == "GET":

            service_id = request.session.get("service_db")
            documents = document_master.objects.all().order_by('order_by')
            contractor_types = parameter_master.objects.filter(parameter_name='contractor Type')
            Product_types = parameter_master.objects.filter(parameter_name='Product')

            context = {
                'data': documents,
                'service_id': service_id,
                'contractor_types': contractor_types,
                'Product_types': Product_types,
            }

            return render(request, 'Master/Create_Document_Master.html', context)

        elif request.method == "POST":

            service_id = request.session.get("service_db")

            # SAME AS EDIT PAGE: service name cleaned
            service_obj = service_master.objects.using('default').filter(ser_id=service_id).first()
            service_name = service_obj.ser_name.replace(" ", "")

            doc_names = request.POST.getlist('doc_name[]')
            is_active_list = request.POST.getlist('is_active[]')
            is_mandatory_list = request.POST.getlist('is_mandatory[]')
            doc_types = request.POST.getlist('doc_type[]') if service_id in ['4', '5'] else []

            files = request.FILES.getlist('sample_file[]')
            user_id = request.session.get("user_id")

            # Get current last order_by
            last_order = document_master.objects.using(service_id).aggregate(
                Max('order_by')
            )['order_by__max'] or 0

            for i in range(len(doc_names)):

                uploaded_file = files[i] if i < len(files) else None
                final_relative_path = None

                # =======================================
                #   FILE SAVE LOGIC  (EDIT STYLE)
                # =======================================
                if uploaded_file:

                    next_order = last_order + i + 1

                    # Folder: MEDIA_ROOT/DownloadPDF/<ServiceName>/Document_<order>/
                    folder_path = os.path.join(
                        settings.MEDIA_ROOT,
                        "DownloadPDF",
                        service_name,
                        f"Document_{next_order}"
                    )

                    os.makedirs(folder_path, exist_ok=True)

                    # (Same as edit) – Save file inside folder
                    file_name = uploaded_file.name
                    absolute_path = os.path.join(folder_path, file_name)

                    with open(absolute_path, "wb+") as f:
                        for chunk in uploaded_file.chunks():
                            f.write(chunk)

                    # Relative path to store in DB
                    final_relative_path = f"DownloadPDF/{service_name}/Document_{next_order}/{file_name}"

                # =======================================
                #   SAVE DOCUMENT RECORD
                # =======================================
                document_master.objects.using(service_id).create(
                    doc_name=doc_names[i],
                    is_active=int(is_active_list[i]),
                    mandatory=int(is_mandatory_list[i]),
                    doc_type=doc_types[i] if service_id in ['4', '5'] else None,
                    doc_subpath=final_relative_path,   # <-- FIXED
                    created_at=now(),
                    created_by=user_id,
                    order_by=last_order + i + 1
                )

            messages.success(request, "Documents saved successfully.")
            return redirect('documentMaster')

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), ''])
        logger.error(f"Error rendering documentMaster: {str(e)}")
        return HttpResponse("An error occurred while trying to load the page.", status=500)


    
# Edit Document

def Edit_Document_master(request):
    try:
        if request.method == "GET":
            service_id = request.session.get("service_db")
            document_id = decrypt_parameter(str(request.GET.get("doc_id")))
            contractor_types = parameter_master.objects.filter(parameter_name='contractor Type')
            Product_types = parameter_master.objects.filter(parameter_name='Product')

            if not document_id:
                return HttpResponse("Document ID not provided.", status=400)

            document = get_object_or_404(document_master, doc_id=document_id)
            document.doc_id = encrypt_parameter(str(document.doc_id))

            if document.doc_subpath:
                clean_path = document.doc_subpath.replace("\\", "/")
                document.encrypted_subpath = encrypt_parameter(clean_path)
            else:
                document.encrypted_subpath = None
                
            context = {
                'service_id': service_id,
                'document': document,
                'contractor_types': contractor_types,
                'Product_types': Product_types,
                'MEDIA_URL': settings.MEDIA_URL,  # add this
            }

            return render(request, 'Master/Edit_Document_master.html', context)

        elif request.method == "POST":
            
            document_id = decrypt_parameter(str(request.POST.get("doc_id")))

            if not document_id:
                return HttpResponse("Document ID missing.", status=400)

            document = get_object_or_404(document_master, doc_id=document_id)

            # Grab session + form data
            service_id = request.session.get("service_db")
            updated_by = request.session.get("user_id")

            doc_name = request.POST.get("doc_name", "").strip()
            is_active = request.POST.get("is_active") == "1"
            mandatory = request.POST.get("mandatory") == "1"

            # Update document fields
            document.doc_name = doc_name
            document.is_active = is_active
            document.mandatory = mandatory
            document.updated_by = updated_by
            document.updated_at = now()

            if service_id in ['4', '5']:
                doc_type = request.POST.get("doc_type", "").strip()
                document.doc_type = doc_type

            # --- Handle file upload ---
            uploaded_file = request.FILES.get("sample_doc")
            if uploaded_file:
                if uploaded_file.size > 5 * 1024 * 1024:
                    return HttpResponse("File size exceeds 5 MB.", status=400)

                # Get service name from service_master using default DB
                from .models import service_master
                service_obj = service_master.objects.using('default').filter(ser_id=service_id).first()
                if not service_obj:
                    return HttpResponse("Service not found.", status=400)

                service_name = service_obj.ser_name.replace(" ", "")  # Remove spaces

                # Build upload path
                upload_dir = os.path.join(settings.MEDIA_ROOT, "DownloadPDF", service_name, f"Document_{document_id}")
                os.makedirs(upload_dir, exist_ok=True)

                fs = FileSystemStorage(location=upload_dir)
                filename = fs.save(uploaded_file.name, uploaded_file)

                # Save relative file path in doc_subpath column
                document.doc_subpath = os.path.join("DownloadPDF", service_name, f"Document_{document_id}", filename)

            document.save()
            return redirect('documentMaster')


    except Exception as e:
        return HttpResponse(f"An error occurred: {str(e)}", status=500)


import json
import traceback
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from django.apps import apps
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
import openpyxl
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.styles import numbers
from io import BytesIO

# Helper functions
def get_model_for_service(service_id, model_name):
    """
    Dynamically get the model class for the given service and model name
    """
    try:
        service_to_app = {
            '1': 'DrainageConnection',
            '2': 'TreeCutting', 
            '3': 'TreeTrimming',
            '4': 'ContractRegistration',
            '5': 'ProductApproval'
        }
        
        # For status_master - it's in Masters app
        if model_name == 'status_master':
            try:
                model = apps.get_model('Masters', 'status_master')
                return model
            except LookupError:
                try:
                    model = apps.get_model('Masters', 'StatusMaster')
                    return model
                except LookupError:
                    return None
        
        # For other models, get from service app
        app_label = service_to_app.get(str(service_id))
        if not app_label:
            return None
        
        try:
            model = apps.get_model(app_label, model_name)
            return model
        except LookupError:
            try:
                model_class_name = ''.join(word.capitalize() for word in model_name.split('_'))
                model = apps.get_model(app_label, model_class_name)
                return model
            except LookupError:
                return None
    except Exception:
        return None

def get_service_name(service_id):
    try:
        service_names = {
            '1': 'Drainage Connection',
            '2': 'Tree Cutting',
            '3': 'Tree Trimming', 
            '4': 'Contract Registration',
            '5': 'Product Approval'
        }
        return service_names.get(str(service_id), 'Unknown Service')
    except Exception:
        return 'Unknown Service'

def get_service_db_name(service_id):
    try:
        db_mapping = {
            '1': '1',
            '2': '2',
            '3': '3',
            '4': '4',
            '5': '5'
        }
        return db_mapping.get(str(service_id), 'default')
    except Exception:
        return 'default'

def get_service_color(service_id):
    try:
        colors = {
            '1': '#3498db',
            '2': '#2ecc71',
            '3': '#f39c12',
            '4': '#9b59b6',
            '5': '#e74c3c'
        }
        return colors.get(str(service_id), '#2c3e50')
    except Exception:
        return '#2c3e50'

# ========== MAIN DASHBOARD VIEW ==========
def service_dashboard(request):
    try:
        service_id = request.session.get("service_db")
        
        if not service_id:
            return render(request, 'Master/no_service.html', {
                'message': 'Please select a service first'
            })
        
        # Get models
        ApplicationForm = get_model_for_service(service_id, 'application_form')
        StatusMaster = get_model_for_service(service_id, 'status_master')
        
        if not ApplicationForm:
            return render(request, 'Master/error.html', {
                'message': 'Application form model not found'
            })
        
        db_alias = get_service_db_name(service_id)
        service_name = get_service_name(service_id)
        service_color = get_service_color(service_id)
        
        # Get filter parameters from request
        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')
        
        # Base queryset
        try:
            applications = ApplicationForm.objects.using(db_alias).all()
        except Exception as e:
            print(f"Error getting applications: {e}")
            applications = ApplicationForm.objects.using(db_alias).none()
        
        # Apply date filters if provided
        try:
            if from_date:
                try:
                    from_date_obj = datetime.strptime(from_date, '%Y-%m-%d')
                    applications = applications.filter(created_at__gte=from_date_obj)
                except ValueError:
                    pass
            
            if to_date:
                try:
                    to_date_obj = datetime.strptime(to_date, '%Y-%m-%d')
                    to_date_obj = to_date_obj + timedelta(days=1)
                    applications = applications.filter(created_at__lt=to_date_obj)
                except ValueError:
                    pass
        except Exception as e:
            print(f"Error applying date filters: {e}")
        
        try:
            total_applications = applications.count()
        except Exception:
            total_applications = 0
        
        # ========== GET STATUSES FROM SERVICE DB ==========
        status_distribution = {}
        status_colors = {}
        status_labels = []
        status_values = []
        status_color_list = []
        
        try:
            if StatusMaster:
                try:
                    statuses = StatusMaster.objects.using(db_alias).all()
                    
                    for status in statuses:
                        try:
                            count = applications.filter(status=status).count()
                            status_name = status.status_name if status.status_name else 'Unknown'
                            status_distribution[status_name] = count
                            status_colors[status_name] = status.status_color or '#6c757d'
                        except Exception as e:
                            print(f"Error processing status {status}: {e}")
                            continue
                    
                    status_labels = list(status_distribution.keys())
                    status_values = list(status_distribution.values())
                    status_color_list = [status_colors.get(label, '#6c757d') for label in status_labels]
                    
                except Exception as e:
                    print(f"Error getting statuses: {e}")
        except Exception as e:
            print(f"Status processing error: {e}")
        
        # Calculate counts
        approved_count = 0
        pending_count = 0
        rejected_count = 0
        
        try:
            for status_name, count in status_distribution.items():
                try:
                    lower_status = status_name.lower()
                    if 'approved' in lower_status or 'issued' in lower_status or 'certificate' in lower_status:
                        approved_count += count
                    elif 'pending' in lower_status or 'process' in lower_status or 'forward' in lower_status:
                        pending_count += count
                    elif 'rejected' in lower_status or 'refused' in lower_status:
                        rejected_count += count
                except Exception as e:
                    print(f"Error calculating counts for {status_name}: {e}")
                    continue
        except Exception as e:
            print(f"Count calculation error: {e}")
        
        # ========== DAILY DATA ==========
        date_range = []
        
        try:
            if from_date and to_date:
                try:
                    start_date = datetime.strptime(from_date, '%Y-%m-%d')
                    end_date = datetime.strptime(to_date, '%Y-%m-%d')
                    days_diff = (end_date - start_date).days
                    
                    if days_diff > 60:
                        start_date = end_date - timedelta(days=60)
                    
                    current_date = start_date
                    while current_date <= end_date:
                        try:
                            day_start = datetime(current_date.year, current_date.month, current_date.day)
                            day_end = day_start + timedelta(days=1)
                            
                            day_count = applications.filter(
                                created_at__gte=day_start,
                                created_at__lt=day_end
                            ).count()
                            
                            date_range.append({
                                'date': current_date.strftime('%Y-%m-%d'),
                                'volume': day_count
                            })
                        except Exception as e:
                            print(f"Error processing date {current_date}: {e}")
                        current_date += timedelta(days=1)
                        
                except ValueError:
                    date_range = get_default_daily_data(applications)
            else:
                date_range = get_default_daily_data(applications)
        except Exception as e:
            print(f"Error generating daily data: {e}")
            date_range = get_default_daily_data(applications)
        
        # ========== TABLE DATA ==========
        table_data = []
        table_fields = []
        
        try:
            all_applications = applications.order_by('-created_at')
            
            if service_id == '1':
                table_fields = ['request_no', 'name_of_premises', 'plot_no', 'sector_no', 'node', 'name_of_owner', 'status', 'created_at']
            elif service_id == '2':
                table_fields = ['request_no', 'name_of_applicant', 'plot_no', 'survey_no', 'address', 'total_existing_no_of_trees', 'status', 'created_at']
            elif service_id == '3':
                table_fields = ['request_no', 'name_of_applicant', 'plot_no', 'survey_no', 'address', 'total_trees_to_trim', 'status', 'created_at']
            elif service_id == '4':
                table_fields = ['request_no', 'company_name', 'contractor_type', 'gstin', 'contact_person_name', 'mobile_no', 'status', 'created_at']
            elif service_id == '5':
                table_fields = ['request_no', 'product_type', 'factory_name', 'gstin', 'contact_person_name', 'mobile_no', 'status', 'created_at']
            else:
                table_fields = ['request_no', 'status', 'created_at']
            
            for app in all_applications:
                try:
                    row = {'id': app.id}
                    for field in table_fields:
                        try:
                            if field == 'status':
                                row['status'] = app.status.status_name if app.status else 'N/A'
                                row['status_color'] = app.status.status_color if app.status else '#6c757d'
                            elif field == 'created_at':
                                row['created_at'] = app.created_at.strftime('%Y-%m-%d %H:%M') if app.created_at else '-'
                            else:
                                value = getattr(app, field, None)
                                row[field] = str(value) if value is not None and value != '' else '-'
                        except Exception as e:
                            print(f"Error processing field {field} for app {app.id}: {e}")
                            row[field] = '-'
                    table_data.append(row)
                except Exception as e:
                    print(f"Error processing app {app}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error generating table data: {e}")
            table_data = []
            table_fields = ['request_no', 'status', 'created_at']
        
        username = request.session.get('username', 'User')
        user_id = request.session.get('user_id', 1)
        role_id = request.session.get('role_id', 1)
        
        # ========== MONTHLY TREND DATA ==========
        monthly_data = []
        today = timezone.now()

        for i in range(11, -1, -1):
            month_start = today.replace(day=1) - timedelta(days=30*i)
            month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            
            month_count = applications.filter(
                created_at__gte=month_start,
                created_at__lt=month_end + timedelta(days=1)
            ).count()
            
            monthly_data.append({
                'month': month_start.strftime('%b %Y'),
                'count': month_count
            })
        
        context = {
            'service_id': service_id,
            'service_name': service_name,
            'service_color': service_color,
            'total_applications': total_applications,
            'approved_count': approved_count,
            'pending_count': pending_count,
            'rejected_count': rejected_count,
            'status_distribution': json.dumps({
                'labels': status_labels,
                'values': status_values,
                'colors': status_color_list
            }),
            'daily_data': json.dumps(date_range),
            'table_data': table_data,
            'table_fields': table_fields,
            'username': username,
            'user_id': user_id,
            'role_id': role_id,
            'from_date': from_date if from_date else '',
            'to_date': to_date if to_date else '',
            'monthly_data': json.dumps(monthly_data)
        }
        
        return render(request, 'Master/dashboard.html', context)
        
    except Exception as e:
        print(f"Error in dashboard: {str(e)}")
        print(traceback.format_exc())
        messages.error(request, 'Oops...! Something went wrong!')
        return render(request, 'Master/error.html', {
            'message': f'Error: {str(e)}'
        })

def get_default_daily_data(applications):
    try:
        date_range = []
        today = timezone.now()
        end_date = today
        start_date = today - timedelta(days=29)
        current_date = start_date
        while current_date <= end_date:
            try:
                day_start = datetime(current_date.year, current_date.month, current_date.day)
                day_end = day_start + timedelta(days=1)
                day_count = applications.filter(
                    created_at__gte=day_start,
                    created_at__lt=day_end
                ).count()
                date_range.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'volume': day_count
                })
            except Exception as e:
                print(f"Error processing date {current_date}: {e}")
            current_date += timedelta(days=1)
        return date_range
    except Exception:
        return []

# ========== GET APPLICATION DETAIL FOR MODAL ==========
def get_application_detail(request, app_id):
    """
    API to get detailed application data for modal popup
    """
    try:
        service_id = request.session.get("service_db")
        
        if not service_id:
            return JsonResponse({'error': 'No service selected'}, status=400)
        
        ApplicationForm = get_model_for_service(service_id, 'application_form')
        WorkflowHistory = get_model_for_service(service_id, 'workflow_history')
        
        # Get CustomUser from Account app
        try:
            CustomUser = apps.get_model('Account', 'CustomUser')
        except LookupError:
            try:
                CustomUser = apps.get_model('Account', 'customuser')
            except LookupError:
                CustomUser = None
        
        if not ApplicationForm:
            return JsonResponse({'error': 'Model not found'}, status=404)
        
        db_alias = get_service_db_name(service_id)
        service_name = get_service_name(service_id)
        
        try:
            application = ApplicationForm.objects.using(db_alias).get(id=app_id)
        except ApplicationForm.DoesNotExist:
            return JsonResponse({'error': 'Application not found'}, status=404)
        
        # Get all user IDs from application fields
        user_ids = set()
        
        # Check created_by and updated_by
        if application.created_by:
            try:
                user_ids.add(int(application.created_by))
            except (ValueError, TypeError):
                pass
        if application.updated_by:
            try:
                user_ids.add(int(application.updated_by))
            except (ValueError, TypeError):
                pass
        
        # Get all fields and their values
        app_data = {}
        for field in application._meta.get_fields():
            if field.name in ['status', 'form_user']:
                continue
            value = getattr(application, field.name, None)
            if value is not None:
                if isinstance(value, datetime):
                    app_data[field.name] = value.strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(value, bool):
                    app_data[field.name] = 'Yes' if value else 'No'
                else:
                    app_data[field.name] = str(value)
            else:
                app_data[field.name] = '-'
        
        # Add status
        app_data['status'] = application.status.status_name if application.status else 'N/A'
        app_data['status_color'] = application.status.status_color if application.status else '#6c757d'
        app_data['request_no'] = application.request_no if application.request_no else 'N/A'
        
        # Fetch user names from Account app
        user_names = {}
        if CustomUser and user_ids:
            try:
                users = CustomUser.objects.using('default').filter(id__in=user_ids)
                for user in users:
                    user_names[user.id] = user.full_name if user.full_name else user.phone
                print(f"Found {len(user_names)} users from Account app")
            except Exception as e:
                print(f"Error fetching users from Account app: {e}")
        
        # Replace created_by and updated_by with names
        if app_data.get('created_by') and app_data['created_by'] != '-':
            try:
                created_by_id = int(app_data['created_by'])
                app_data['created_by'] = user_names.get(created_by_id, app_data['created_by'])
            except (ValueError, TypeError):
                pass
        
        if app_data.get('updated_by') and app_data['updated_by'] != '-':
            try:
                updated_by_id = int(app_data['updated_by'])
                app_data['updated_by'] = user_names.get(updated_by_id, app_data['updated_by'])
            except (ValueError, TypeError):
                pass
        
        # ========== GET WORKFLOW HISTORY WITH USER NAMES ==========
        workflow_data = []
        if WorkflowHistory:
            history = WorkflowHistory.objects.using(db_alias).filter(
                form_id=application,
                request_no__isnull=False
            ).exclude(
                request_no=''
            ).order_by('-updated_at')[:20]
            
            # Get all user IDs from workflow history
            workflow_user_ids = set()
            for record in history:
                if record.send_forward:
                    try:
                        workflow_user_ids.add(int(record.send_forward))
                    except (ValueError, TypeError):
                        pass
                if record.pre_user:
                    try:
                        workflow_user_ids.add(int(record.pre_user))
                    except (ValueError, TypeError):
                        pass
            
            # Fetch workflow user names
            workflow_user_names = {}
            if CustomUser and workflow_user_ids:
                try:
                    users = CustomUser.objects.using('default').filter(id__in=workflow_user_ids)
                    for user in users:
                        workflow_user_names[user.id] = user.full_name if user.full_name else user.phone
                except Exception as e:
                    print(f"Error fetching workflow users: {e}")
            
            for record in history:
                # Get user names
                send_forward_name = '-'
                pre_user_name = '-'
                
                if record.send_forward:
                    try:
                        send_forward_id = int(record.send_forward)
                        send_forward_name = workflow_user_names.get(send_forward_id, str(record.send_forward))
                    except (ValueError, TypeError):
                        send_forward_name = str(record.send_forward)
                
                if record.pre_user:
                    try:
                        pre_user_id = int(record.pre_user)
                        pre_user_name = workflow_user_names.get(pre_user_id, str(record.pre_user))
                    except (ValueError, TypeError):
                        pre_user_name = str(record.pre_user)
                
                status_name = record.status.status_name if record.status else 'N/A'
                
                workflow_data.append({
                    'level': record.level or '-',
                    'status': status_name,
                    'send_forward': send_forward_name,
                    'pre_user': pre_user_name,
                    'created_at': record.created_at.strftime('%Y-%m-%d %H:%M:%S') if record.created_at else '-',
                    'updated_at': record.updated_at.strftime('%Y-%m-%d %H:%M:%S') if record.updated_at else '-',
                })
        
        return JsonResponse({
            'application': app_data,
            'workflow_history': workflow_data,
            'service': service_name
        })
        
    except Exception as e:
        import traceback
        print(f"Error in get_application_detail: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)

# ========== EXPORT TO EXCEL - WITH DATE FILTER ==========
def export_to_excel(request):
    """
    Export all applications for the current service to Excel with date filter
    """
    try:
        service_id = request.session.get("service_db")
        
        if not service_id:
            return HttpResponse('No service selected', status=400)
        
        ApplicationForm = get_model_for_service(service_id, 'application_form')
        
        if not ApplicationForm:
            return HttpResponse('Model not found', status=404)
        
        db_alias = get_service_db_name(service_id)
        service_name = get_service_name(service_id)
        
        # Get filter parameters from GET request
        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')
        
        print(f"=== Export Excel ===")
        print(f"From Date: {from_date}")
        print(f"To Date: {to_date}")
        
        # Base queryset
        applications = ApplicationForm.objects.using(db_alias).all()
        
        # Apply date filters ONLY if provided
        if from_date:
            try:
                from_date_obj = datetime.strptime(from_date, '%Y-%m-%d')
                applications = applications.filter(created_at__gte=from_date_obj)
                print(f"Applied from_date filter: {from_date}")
            except ValueError as e:
                print(f"Error parsing from_date: {e}")
        
        if to_date:
            try:
                to_date_obj = datetime.strptime(to_date, '%Y-%m-%d')
                to_date_obj = to_date_obj + timedelta(days=1)
                applications = applications.filter(created_at__lt=to_date_obj)
                print(f"Applied to_date filter: {to_date}")
            except ValueError as e:
                print(f"Error parsing to_date: {e}")
        
        # Order by created_at descending
        applications = applications.order_by('-created_at')
        
        total_count = applications.count()
        print(f"Total records exported: {total_count}")
        
        # ========== GET USER NAMES FROM ACCOUNT APP ==========
        try:
            CustomUser = apps.get_model('Account', 'CustomUser')
        except LookupError:
            try:
                CustomUser = apps.get_model('Account', 'customuser')
            except LookupError:
                CustomUser = None
        
        # Collect all user IDs from applications
        user_ids = set()
        for app in applications:
            if app.created_by:
                try:
                    user_ids.add(int(app.created_by))
                except (ValueError, TypeError):
                    pass
            if app.updated_by:
                try:
                    user_ids.add(int(app.updated_by))
                except (ValueError, TypeError):
                    pass
        
        # Fetch user names
        user_names = {}
        if CustomUser and user_ids:
            try:
                users = CustomUser.objects.using('default').filter(id__in=user_ids)
                for user in users:
                    user_names[user.id] = user.full_name if user.full_name else user.phone
                print(f"Found {len(user_names)} users for Excel export")
            except Exception as e:
                print(f"Error fetching users for Excel: {e}")
        
        # Get fields - exclude status and form_user
        fields = []
        for field in ApplicationForm._meta.get_fields():
            if field.name not in ['status', 'form_user'] and not field.is_relation:
                fields.append(field.name)
        
        # Create workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Applications"
        
        # Styles
        header_font = Font(bold=True, color="FFFFFF", size=11)
        header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        cell_alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        
        # Add headers
        for col, field in enumerate(fields, 1):
            cell = ws.cell(row=1, column=col)
            cell.value = field.replace('_', ' ').title()
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = thin_border
        
        # Add data with user names
        for row, app in enumerate(applications, 2):
            for col, field in enumerate(fields, 1):
                cell = ws.cell(row=row, column=col)
                value = getattr(app, field, None)
                
                # ========== CONVERT USER IDs TO NAMES ==========
                if field == 'created_by' or field == 'updated_by':
                    if value:
                        try:
                            user_id = int(value)
                            value = user_names.get(user_id, str(value))
                        except (ValueError, TypeError):
                            value = str(value) if value else '-'
                    else:
                        value = '-'
                elif isinstance(value, datetime):
                    value = value.strftime('%Y-%m-%d %H:%M:%S')
                elif value is None:
                    value = '-'
                else:
                    value = str(value)
                
                cell.value = value
                cell.alignment = cell_alignment
                cell.border = thin_border
        
        # Auto-adjust column widths
        for col in range(1, len(fields) + 1):
            column_letter = get_column_letter(col)
            max_length = 0
            for row in range(1, min(ws.max_row + 1, 50)):
                cell_value = ws.cell(row=row, column=col).value
                if cell_value:
                    max_length = max(max_length, len(str(cell_value)))
            adjusted_width = min(max_length + 5, 50)
            ws.column_dimensions[column_letter].width = max(adjusted_width, 15)
        
        # Add filter
        ws.auto_filter.ref = ws.dimensions
        
        # Freeze header row
        ws.freeze_panes = 'A2'
        
        # Create response
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        
        # Add date range to filename if filtered
        if from_date and to_date:
            filename = f'{service_name}_Applications_{from_date}_to_{to_date}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        elif from_date:
            filename = f'{service_name}_Applications_From_{from_date}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        elif to_date:
            filename = f'{service_name}_Applications_To_{to_date}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        else:
            filename = f'{service_name}_Applications_All_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        wb.save(response)
        return response
        
    except Exception as e:
        import traceback
        print(f"Error in export_to_excel: {str(e)}")
        print(traceback.format_exc())
        return HttpResponse(f'Error: {str(e)}', status=500)