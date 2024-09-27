import json
import pydoc
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login ,logout,get_user_model
from Account.forms import RegistrationForm
from Account.models import *
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
from .models import Log, CustomUser 

@login_required
def masters(request):
    Db.closeConnection()
    m = Db.get_connection()
    cursor=m.cursor()
    pre_url = request.META.get('HTTP_REFERER')
    header, data = [], []
    entity, type, name = '', '', ''
    global user
    user  = request.session.get('user_id', '')
    try:
         
        if request.method=="GET":
            entity = request.GET.get('entity', '')
            type = request.GET.get('type', '')
            cursor.callproc("stp_get_masters",[entity,type,'name',user])
            for result in cursor.stored_results():
                datalist1 = list(result.fetchall())
            name = datalist1[0][0]
            cursor.callproc("stp_get_masters", [entity, type, 'header',user])
            for result in cursor.stored_results():
                header = list(result.fetchall())
            cursor.callproc("stp_get_masters",[entity,type,'data',user])
            for result in cursor.stored_results():
                if (entity == 'em' or entity == 'sm' or entity == 'cm' or entity == 'menu' or entity == 'user') and type !='err': 
                    data = []
                    rows = result.fetchall()
                    for row in rows:
                        encrypted_id = encrypt_parameter(str(row[0]))
                        data.append((encrypted_id,) + row[1:])
                else: data = list(result.fetchall())

            cursor.callproc("stp_get_dropdown_values",['company'])
            for result in cursor.stored_results():
                company_names = list(result.fetchall())
            if entity == 'r' and type == 'i':
                cursor.callproc("stp_get_assigned_company",[user])
                for result in cursor.stored_results():
                    company_names = list(result.fetchall())
            if entity == 'r' and type == 'ed':
                month_year =str(request.GET.get('month', ''))
                if month_year == '':
                    year,month = '',''
                else: year,month = month_year.split('-')
                employee_id = request.GET.get('empid', '')
                cursor.callproc("stp_get_edit_roster",[employee_id,month,year,'1'])
                for result in cursor.stored_results():
                    data = list(result.fetchall())
                cursor.callproc("stp_get_edit_roster",[employee_id,month,year,'2'])
                for result in cursor.stored_results():
                    header = list(result.fetchall())
            if entity == 'urm' and (type == 'acu' or type == 'acr'):
                cursor.callproc("stp_get_access_control",[entity,type])
                for result in cursor.stored_results():
                    header = list(result.fetchall())
                cursor.callproc("stp_get_access_control",[entity,'comp'])
                for result in cursor.stored_results():
                    company_names = list(result.fetchall())
                cursor.callproc("stp_get_access_control",[entity,'site'])
                for result in cursor.stored_results():
                    data = list(result.fetchall())
                
        if request.method=="POST":
            entity = request.POST.get('entity', '')
            type = request.POST.get('type', '')
            if entity == 'r' and type == 'ed':
                ids = request.POST.getlist('ids[]', '')
                shifts = request.POST.getlist('shifts[]', '')
                for id,shift in zip(ids, shifts):
                    cursor.callproc("stp_post_roster",[id,shift])
                    for result in cursor.stored_results():
                        datalist = list(result.fetchall())
                if datalist[0][0] == "success":
                    messages.success(request, 'Data updated successfully !')
            if entity == 'urm' and (type == 'acu' or type == 'acr'):
                
                created_by = request.session.get('user_id', '')
                ur = request.POST.get('ur', '')
                selected_company_ids = list(map(int, request.POST.getlist('company_id')))
                selected_worksites  = request.POST.getlist('worksite')
                company_worksite_map = {}
                
                if not selected_company_ids or not selected_worksites:
                    messages.error(request, 'Company or worksite data is missing!')
                    return redirect(f'/masters?entity={entity}&type=urm')
                if type not in ['acu', 'acr'] or not ur:
                    messages.error(request, 'Invalid data received.')
                    return redirect(f'/masters?entity={entity}&type=urm')
                
                cursor.callproc("stp_get_company_worksite",[",".join(request.POST.getlist('company_id'))])
                for result in cursor.stored_results():
                    company_worksites  = list(result.fetchall())
                    
                for company_id, worksite_name in company_worksites:
                    if company_id not in company_worksite_map:
                        company_worksite_map[company_id] = []
                    company_worksite_map[company_id].append(worksite_name)
                
                filtered_combinations = []
                for company_id in selected_company_ids:
                    valid_worksites = company_worksite_map.get(company_id, [])
                    # Filter worksites that were actually selected by the user
                    selected_valid_worksites = [ws for ws in selected_worksites if ws in valid_worksites]
                    filtered_combinations.extend([(company_id, ws) for ws in selected_valid_worksites])
                    
                cursor.callproc("stp_delete_access_control",[type,ur])
                r=''
                for company_id, worksite in filtered_combinations:
                    cursor.callproc("stp_post_access_control",[type,ur,company_id,worksite,created_by])
                    for result in cursor.stored_results():
                            r = list(result.fetchall())
                type='urm'
                if r[0][0] == "success":
                    messages.success(request, 'Data updated successfully !')
                
            else : messages.error(request, 'Oops...! Something went wrong!')
                             
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        cursor.callproc("stp_error_log",[fun,str(e),user])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally:
        cursor.close()
        m.commit()
        m.close()
        Db.closeConnection()
        if request.method=="GET":
            return render(request,'Master/index.html', {'entity':entity,'type':type,'name':name,'header':header,'company_names':company_names,'data':data,'pre_url':pre_url})
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
    Db.closeConnection()
    m = Db.get_connection()
    cursor=m.cursor()
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
        cursor.callproc("stp_get_masters", [entity, type, 'sample_xlsx',user])
        for result in cursor.stored_results():
            columns = [col[0] for col in result.fetchall()]
        # columns = ['Column 1', 'Column 2', 'Column 3']
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
        cursor.callproc("stp_error_log",[fun,str(e),user])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally:
        cursor.close()
        m.commit()
        m.close()
        Db.closeConnection()
        return response      

@login_required  
def roster_upload(request):
    Db.closeConnection()
    m = Db.get_connection()
    cursor = m.cursor()
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
                cursor.callproc("stp_get_masters", [entity, type, 'sample_xlsx',user])
                for result in cursor.stored_results():
                    start_columns = [col[0] for col in result.fetchall()]

                if not all(col in df.columns for col in start_columns + date_columns):
                    messages.error(request, 'Oops...! The uploaded Excel file does not contain the required columns.!')
                    return redirect(f'/masters?entity={entity}&type={type}')
                
                cursor.callproc('stp_insert_checksum', ('roster',company_id,month,year,file_name))
                for result in cursor.stored_results():
                    c = list(result.fetchall())
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
                        cursor.callproc('stp_insert_roster', params)
                        for result in cursor.stored_results():
                            r = list(result.fetchall())
                        if r[0][0] not in ("success", "updated"):
                            if worksite not in worksites:
                                worksites.append(worksite)
                            error_message = str(r[0][0])
                            error_params = ('roster', company_id,worksite,file_name,shift_date,error_message,checksum_id)
                            cursor.callproc('stp_insert_error_log', error_params)
                            messages.error(request, "Errors occurred during upload. Please check error logs.")
                    if r[0][0] == "success": success_count += 1
                    elif r[0][0] == "updated": update_count += 1  
                    else: error_count += 1
                checksum_msg = f"Total Rows Processed: {total_rows}, Successful Entries: {success_count}, Updates: {update_count}, Errors: {error_count}"
                cursor.callproc('stp_update_checksum', ('roster',company_id,', '.join(worksites),month,year,file_name,checksum_msg,error_count,update_count,checksum_id))
                if error_count == 0 and update_count == 0 and success_count > 0:
                    messages.success(request, f"All data uploaded successfully!.")
                elif error_count == 0 and success_count == 0 and update_count > 0:
                    messages.warning(request, f"All data updated successfully!.")
                else:
                    messages.warning(request, f"The upload processed {total_rows} rows, resulting in {success_count} successful entries, {update_count} updates, and {error_count} errors; please check the error logs for details.")
                    
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            fun = tb[0].name
            cursor.callproc("stp_error_log", [fun, str(e), user])  
            messages.error(request, 'Oops...! Something went wrong!')
            m.commit()   

        finally:
            cursor.close()
            m.close()
            Db.closeConnection()
            return redirect(f'/masters?entity={entity}&type={type}')     
        
@login_required        
def site_master(request):
    Db.closeConnection()
    m = Db.get_connection()
    cursor=m.cursor()
    global user
    user  = request.session.get('user_id', '')
    try:
        
        if request.method == "GET":
            cursor.callproc("stp_get_roster_type")
            for result in cursor.stored_results():
                roster_types = list(result.fetchall())
                # Call stored procedure to get company names
            cursor.callproc("stp_get_company_names")
            for result in cursor.stored_results():
                company_names = list(result.fetchall())
            site_id = request.GET.get('site_id', '')
            if site_id == "0":
                if request.method == "GET":
                    context = {'company_names': company_names, 'roster_type': roster_types,'site_id':site_id}

            else:
                site_id1 = request.GET.get('site_id', '')
                site_id = decrypt_parameter(site_id1)
                cursor.callproc("stp_edit_site_master", (site_id,)) 
                for result in cursor.stored_results():
                    data = result.fetchall()[0]  
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
                
                cursor.callproc("stp_insert_site_master", params)
                for result in cursor.stored_results():
                        datalist = list(result.fetchall())
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
                    cursor.callproc("stp_update_site_master",params) 
                    messages.success(request, "Data updated successfully...!")

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        cursor.callproc("stp_error_log", [fun, str(e), user])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally:
        cursor.close()
        m.commit()
        m.close()
        Db.closeConnection()
            
        if request.method=="GET":
            return render(request, "Master/site_master.html", context)
        elif request.method=="POST":  
            return redirect( f'/masters?entity=sm&type=i')
        
@login_required      
def company_master(request):
    Db.closeConnection()
    m = Db.get_connection()
    cursor=m.cursor()
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
                cursor.callproc("stp_edit_company_master", (company_id,))  # Note the comma to make it a tuple
                for result in cursor.stored_results():
                    data = result.fetchall()[0]  
                        
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
                cursor.callproc("stp_insert_company_master", params)
                for result in cursor.stored_results():
                        datalist = list(result.fetchall())
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
                cursor.callproc("stp_update_company_master",params) 
                messages.success(request, "Data updated successfully ...!")
                
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        cursor.callproc("stp_error_log", [fun, str(e), user])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally:
        cursor.close()
        m.commit()
        m.close()
        Db.closeConnection()

        encrypted_id = encrypt_parameter(company_id)
            
        if request.method=="GET":
            return render(request, "Master/company_master.html", context)
        elif request.method == "POST":
            return redirect(f'/masters?entity=cm&type=i')

@login_required        
def employee_master(request):
    Db.closeConnection()
    m = Db.get_connection()
    cursor=m.cursor()
    global user
    user  = request.session.get('user_id', '')
    try:
        
        if request.method == "GET":
            id = request.GET.get('id', '')
            

            cursor.callproc("stp_get_employee_status")
            for result in cursor.stored_results():
                employee_status = list(result.fetchall())
            cursor.callproc("stp_get_dropdown_values",('site',))
            for result in cursor.stored_results():
                site_name = list(result.fetchall())
            if id == "0":
                if request.method == "GET":
                    context = {'id':id, 'employee_status':employee_status, 'employee_status_id': '','site_name':site_name}

            else:
                id1 = request.GET.get('id', '')
                id = decrypt_parameter(id1)
                cursor.callproc("stp_edit_employee_master", (id,))
                for result in cursor.stored_results():
                    data = result.fetchall()[0]  
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
                
                cursor.callproc("stp_insert_employee_master", params)
                for result in cursor.stored_results():
                        datalist = list(result.fetchall())
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
                cursor.callproc("stp_update_employee_master",params) 
                messages.success(request, "Data successfully Updated!")

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        cursor.callproc("stp_error_log", [fun, str(e), user])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally:
        cursor.close()
        m.commit()
        m.close()
        Db.closeConnection()
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
            Db.closeConnection()
            m = Db.get_connection()
            cursor = m.cursor()
            entity = request.POST.get('entity', '')
            type = request.POST.get('type', '')
            company_id = request.POST.get('company_id', None)
            cursor.callproc("stp_get_masters", [entity, type, 'sample_xlsx',user])
            for result in cursor.stored_results():
                columns = [col[0] for col in result.fetchall()]
            if not all(col in df.columns for col in columns):
                messages.error(request, 'Oops...! The uploaded Excel file does not contain the required columns.!')
                return redirect(f'/masters?entity={entity}&type={type}')
            upload_for = {'em': 'employee master','sm': 'site master','cm': 'company master','r': 'roster'}[entity]
            cursor.callproc('stp_insert_checksum', (upload_for,company_id,str(datetime.now().month),str(datetime.now().year),file_name))
            for result in cursor.stored_results():
                c = list(result.fetchall())
            checksum_id = c[0][0]

            if entity == 'em':
                for index,row in df.iterrows():
                    params = tuple(str(row.get(column, '')) for column in columns)
                    cursor.callproc('stp_insert_employee_master', params)
                    for result in cursor.stored_results():
                            r = list(result.fetchall())
                    if r[0][0] not in ("success", "updated"):
                        cursor.callproc('stp_insert_error_log', [upload_for, company_id,'',file_name,datetime.now().date(),str(r[0][0]),checksum_id])
                    if r[0][0] == "success": success_count += 1 
                    elif r[0][0] == "updated": update_count += 1  
                    else: error_count += 1
            elif entity == 'sm':
                for index,row in df.iterrows():
                    params = tuple(str(row.get(column, '')) for column in columns)
                    params += (str(company_id),)
                    cursor.callproc('stp_insert_site_master', params)
                    for result in cursor.stored_results():
                            r = list(result.fetchall())
                    if r[0][0] not in ("success", "updated"):
                        cursor.callproc('stp_insert_error_log', [upload_for, company_id,'',file_name,datetime.now().date(),str(r[0][0]),checksum_id])
                    if r[0][0] == "success": success_count += 1 
                    elif r[0][0] == "updated": update_count += 1  
                    else: error_count += 1
            elif entity == 'cm':
                for index,row in df.iterrows():
                    params = tuple(str(row.get(column, '')) for column in columns)
                    cursor.callproc('stp_insert_company_master', params)
                    for result in cursor.stored_results():
                            r = list(result.fetchall())
                    if r[0][0] not in ("success", "updated"):
                        cursor.callproc('stp_insert_error_log', [upload_for, company_id,'',file_name,datetime.now().date(),str(r[0][0]),checksum_id])
                    if r[0][0] == "success": success_count += 1 
                    elif r[0][0] == "updated": update_count += 1  
                    else: error_count += 1
            checksum_msg = f"Total Rows Processed: {total_rows}, Successful Entries: {success_count}" f"{f', Updates: {update_count}' if update_count > 0 else ''}" f"{f', Errors: {error_count}' if error_count > 0 else ''}"
            cursor.callproc('stp_update_checksum', (upload_for,company_id,'',str(datetime.now().month),str(datetime.now().year),file_name,checksum_msg,error_count,update_count,checksum_id))
            if error_count == 0 and update_count == 0 and success_count > 0:
                messages.success(request, f"All data uploaded successfully!.")
            elif error_count == 0 and success_count == 0 and update_count > 0:
                messages.warning(request, f"All data updated successfully!.")
            else:messages.warning(request, f"The upload processed {total_rows} rows, resulting in {success_count} successful entries"  f"{f', {update_count} updates' if update_count > 0 else ''}" f", and {error_count} errors; please check the error logs for details.")
                   
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            fun = tb[0].name
            cursor.callproc("stp_error_log", [fun, str(e), user])  
            messages.error(request, 'Oops...! Something went wrong!')
            m.commit()   
        finally:
            cursor.close()
            m.close()
            Db.closeConnection()
            return redirect(f'/masters?entity={entity}&type=i')

def get_access_control(request):
    Db.closeConnection()
    m = Db.get_connection()
    cursor=m.cursor()
    company = []
    worksite = []
    global user
    user  = request.session.get('user_id', '')
    try:
        if request.method == "POST":
            type = request.POST.get('type','')
            ur = request.POST.get('ur', '')
            cursor.callproc("stp_get_access_control_val", [type,ur,'company'])
            for result in cursor.stored_results():
                company = list(result.fetchall())
            cursor.callproc("stp_get_access_control_val", [type,ur,'worksite'])
            for result in cursor.stored_results():
                worksite = list(result.fetchall())
            if type == 'worksites':
                company_id = request.POST.getlist('company_id','')
                company_ids = ','.join(company_id)
                cursor.callproc("stp_get_access_control_val", [type,company_ids,'worksites'])
                for result in cursor.stored_results():
                    worksite = list(result.fetchall())
                    
            response = {'result': 'success', 'company': company, 'worksite': worksite}
        else: response = {'result': 'fail', 'message': 'Invalid request method'}

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        cursor.callproc("stp_error_log", [tb[0].name, str(e), user])
        print(f"error: {e}")
        response = {'result': 'fail', 'message': 'Something went wrong!'}

    finally:
        cursor.close()
        m.close()
        Db.closeConnection()
        return JsonResponse(response)
