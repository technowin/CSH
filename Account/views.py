import json
import random
import string
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render,redirect
from django.contrib.auth import authenticate, login ,logout,get_user_model
from Account.forms import RegistrationForm
from Account.models import  CustomUser,user_dept_services, OTPVerification, password_storage
# import mysql.connector as sql
from Account.serializers import *
import Db 
import bcrypt
from django.contrib.auth.decorators import login_required
# from .models import SignUpModel
# from .forms import SignUpForm
from CSH.encryption import *
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph
from Account.utils import decrypt_email, encrypt_email
import traceback
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.backends import ModelBackend
from .db_utils import callproc
from django.utils import timezone
from Account.models import *
from Masters.models import *
from MenuManager.models import *
from django.db import IntegrityError
from django.urls import reverse
from django.http import HttpResponseBadRequest
import logging
import requests
from django.db import models
LiveURL = "https://www.cidcoindia.com/AapleMiddlewareAPI/api"
TestURL = "https://www.cidcoindia.com/AapleMiddlewareApiTest/api"
# Set up logging
logger = logging.getLogger(__name__)
import hashlib
logger = logging.getLogger("session_debug") 
from django.contrib.auth import login

def get_client_ip(request):
    """
    Returns the real client IP.
    Works correctly behind proxies / load balancers.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')

@csrf_exempt
def Login(request):
    try:
        if request.method == "GET":
            return render(request, 'Account/login.html')

        if request.method == "POST":
            username = request.POST.get('username')
            password = request.POST.get('password')

            user = authenticate(request, username=username, password=password)

            if not user:
                messages.error(request, 'Invalid credentials')
                return redirect('Login')
            
            # ✅ CRITICAL FIX: Create new session BEFORE login
            # This ensures fresh session for the authenticated user
            request.session.flush()  # Clear existing session first
            request.session.create()  # Create new empty session

            # ✅ login user
            login(request, user)

            # ✅ store only what is needed
            request.session["username"] = str(username)
            request.session["full_name"] = str(user.full_name)
            request.session["user_id"] = str(user.id)
            request.session["role_id"] = str(user.role_id)

            # Store browser fingerprint
            ua = request.META.get('HTTP_USER_AGENT', '')
            request.session['_ua_hash'] = hashlib.sha256(ua.encode()).hexdigest()
            request.session['_ua_raw'] = ua
            request.session['_ip'] = get_client_ip(request)

            # 🧹 clear flags
            request.session.pop('_session_expired', None)
            request.session.pop('_user_logged_out', None)
           
            return redirect('services')
                
    except Exception as e:
        print(f"Login error: {e}")
        messages.error(request, 'An error occurred during login')
        return redirect('Login')

def services(request):
    try:
        if request.method =="GET":
            service = callproc("stp_get_user_services",[request.user.id])
            return render(request,'Account/services.html',{'service':service}) 
        if request.method == "POST":
            service_db = request.POST.get('service')
            request.session['service_db'] = service_db
            
            request.session['admin_flow_completed'] = True
            
            # return redirect('index') 
            servicefetch = service_master.objects.using('default').get(ser_id=service_db)
            redirect_to = servicefetch.internal_page
            return redirect(redirect_to)
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), request.user.id])
        messages.error(request, 'Oops...! Something went wrong!')

def citizen_api(request):
    try:
        all_params = request.GET.dict()
        service_db = all_params.get('service', None)
        userId = all_params.get('UserID', None)
        trackId = all_params.get('TrackID', None)
        serviceId = all_params.get('ServiceID', None)
        request.session["service_db"]=(str(service_db))
        request.session["userId"]=(str(userId))
        request.session["trackId"]=(str(trackId))
        request.session["serviceId"]=(str(serviceId))
        user = get_user_info(request)
        userName,mobileno,emailId,fullname  = '','','',''
        if user and isinstance(user, list): 
            first_item = user[0]    
            userName = first_item.get("userName")
            mobileno = first_item.get("mobileno")
            emailId = first_item.get("emailId")
            fullname = first_item.get("fullname")

        from datetime import datetime
        existing_user = CustomUser.objects.using('default').filter(phone=mobileno, role_id=2).exists()
        exist_inservice = CustomUser.objects.using(service_db).filter(phone=mobileno, role_id=2).exists()
        exist_apidata = api_data.objects.using(service_db).filter(user_id=userId, track_id=trackId,service_id=serviceId).exists()
        user_id = None
        if not exist_apidata:
            api_ins = api_data.objects.using(service_db).create(
                    user_id=userId,track_id=trackId,service_id=serviceId,
                    user_name=userName,full_name=fullname,mobile_no=mobileno,email_id =emailId,
                    created_at=datetime.now(),created_by=str(mobileno),updated_at=datetime.now(),updated_by=str(mobileno)
                )
        else:
            api_data.objects.using(service_db).filter(
                user_id=userId, track_id=trackId, service_id=serviceId
            ).update(
                user_name=userName, full_name=fullname, mobile_no=mobileno, email_id=emailId,
                updated_at=datetime.now(), updated_by=str(user)
            )
        if not exist_inservice:
            if existing_user:
                user = CustomUser.objects.using('default').get(phone=mobileno, role_id=2)
                user_id = user.id
            else:
                user = CustomUser.objects.using('default').create(
                    full_name=fullname,email=emailId,phone=mobileno,
                    first_time_login=True,role_id=2
                )
                user_id = user.id
            if service_db:
                user, created = CustomUser.objects.using(service_db).get_or_create(
                    id=user_id,
                    defaults={
                        "full_name": fullname,
                        "email": emailId,
                        "phone": mobileno,
                        "first_time_login": True,
                        "role_id": 2
                    }
                )

            assigned_menus = RoleMenuMaster.objects.using(service_db).filter(role_id=2)
            for menu in assigned_menus:
                UserMenuDetails.objects.using(service_db).create(
                    user_id=user.id,menu_id=menu.menu_id,role_id=user.role_id
                )    
        else: user = CustomUser.objects.using(service_db).get(phone=mobileno, role_id=2)

        servicefetch = service_master.objects.using('default').get(ser_id=service_db)
        redirect_to = servicefetch.citizen_page
        # request.session.cycle_key()
        request.session["service_db"]=(str(service_db))
        request.session["userId"]=(str(userId))
        request.session["trackId"]=(str(trackId))
        request.session["serviceId"]=(str(serviceId))
        request.session["user_id"]=(str(user.id))
        request.session["role_id"] = str(user.role_id)
        request.session['full_name'] = user.full_name
        request.session['phone_number'] = mobileno

        ex_user = CustomUser.objects.using('default').filter(phone=mobileno, role_id=2).exists()
        ex_ser = CustomUser.objects.using(service_db).filter(phone=mobileno, role_id=2).exists()
        ex_api = api_data.objects.using(service_db).filter(user_id=userId, track_id=trackId,service_id=serviceId).exists()

        if ex_api and ex_ser and ex_user:
            return redirect(redirect_to)
        else: return Response({"error": "Oops...! Something went wrong!"},status=status.HTTP_400_BAD_REQUEST)

    
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),''])  
 
def generate_token():
    url = LiveURL + "/Account/GenerateToken"
    # url = TestURL + "/Account/GenerateToken"
    payload = json.dumps({"email": "cidco@gmail.com","password": "cidco@123"})
    headers = {'Content-Type': 'application/json'}
    response = requests.request("POST", url, headers=headers, data=payload)
    response_json = response.json()
    token = response_json.get("token")
    return token

def get_user_info(request):
    userId = request.session.get('userId', '')
    trackId = request.session.get('trackId', '')
    serviceId = request.session.get('serviceId', '')
    token = generate_token()
    url = LiveURL + "/RequestFromAapleSarkar/GetAapleSarkarUserInfo"
    # url = TestURL + "/RequestFromAapleSarkar/GetAapleSarkarUserInfo"
    payload = json.dumps({"userId": userId,"trackId": trackId,"serviceId": serviceId})
    headers = {'Content-Type': 'application/json',"Authorization": f"Bearer {token}"}
    response = requests.request("POST", url, headers=headers, data=payload)
    response_json = response.json()
    data = response_json.get("data")
    return data

def upd_citizen(request):
    service_db = request.session.get('service_db', '')
    mobileno = request.session.get('phone_number', '')
    userId = request.session.get('userId', '')
    trackId = request.session.get('trackId', '')
    serviceId = request.session.get('serviceId', '')
    applicationId = request.session.get('applicationId', '')
    w_id = request.session.get('workflow_id', '')
    f_id = request.session.get('form_id', '')
    f_user_id = request.session.get('form_user_id', '')
    status = request.session.get('application_status', '')
    rmks = request.session.get('remarks', '')
    timeline = '3'
   
    exist_apidata = api_data.objects.using(service_db).filter(user_id=userId,track_id=trackId,service_id=serviceId).exists()
    from datetime import datetime
    if not exist_apidata:
        api_ins = api_data.objects.using(service_db).create(
                user_id=userId,track_id=trackId,service_id=serviceId,
                application_no=applicationId,application_date=datetime.now(),
                application_status=status,remarks=rmks,service_days=timeline,
                workflow_id=w_id,form_id=f_id,form_user_id=f_user_id,
                created_at=datetime.now(),created_by=str(mobileno),updated_at=datetime.now(),updated_by=str(mobileno)
            )
    else:
        api_data.objects.using(service_db).filter(
            user_id=userId,track_id=trackId,service_id=serviceId
        ).update(
            application_no=applicationId,application_date=datetime.now(),
            application_status=status,remarks=rmks,service_days=timeline,
            workflow_id=w_id,form_id=f_id,form_user_id=f_user_id,
            updated_at=datetime.now(), updated_by=str(mobileno)
        )
    token = generate_token()
    url = LiveURL + "/RequestFromAapleSarkar/UpdateApplicationDetails"
    # url = TestURL + "/RequestFromAapleSarkar/UpdateApplicationDetails"
    payload = json.dumps({
        "userId": userId,
        "trackId":trackId,"serviceId": serviceId,
        "appstatus": status,"applicationId": applicationId,
        "serviceDays": timeline,"remark": "","rejectReason": rmks
    })
    headers = {'Content-Type': 'application/json',"Authorization": f"Bearer {token}"}
    response = requests.request("POST", url, headers=headers, data=payload)
    response_json = response.json()
    data = response_json.get("data")
    return data

def logoutView(request):
    try:
        dropdown = request.session.get('dropdown')
        normal = request.session.get('normal')
        
        if dropdown is not None:
            service_db = dropdown
            url = '/citizenLoginAccount'
        elif normal is not None:
            service_db = normal
            url = f'/citizenLoginAccount?service={service_db}'
        else:
            service_db = None
            url = '/citizenLoginAccount'
        
        logout(request)
        return redirect(url)
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name

def register_new_user(request):
    if request.method=="GET":
        id = request.GET.get('id', '0')
        roles = callproc("stp_get_dropdown_values",['roles'])
        user_list = callproc("stp_get_dropdown_values",['user'])
        department = callproc("stp_get_dropdown_values",['department'])
        service = callproc("stp_get_dropdown_values",['service'])
        
        if id != '0':
            id1 = decrypt_parameter(id)
            users = get_object_or_404(CustomUser, id=id1)
            user_dept_ser = user_dept_services.objects.using('default').filter(user_id=id1).first()
            full_name = users.full_name.split(" ", 1) 
            first_name = full_name[0] 
            last_name = full_name[1] if len(full_name) > 1 else ""  
            context = {'users':users,'first_name':first_name,'last_name':last_name,'roles':roles,'user_list':user_list,'department':department,'service':service,'user_dept_ser':user_dept_ser}
            
        else:
            context = {'id':id,'roles': roles,'department':department,'service':service,'user_list':user_list}
        return render(request,'Account/register_new_user.html',context)

    if request.method == "POST":
        id = request.POST.get('id', '')
        try:  
            if id == '0':                
                firstname = request.POST.get('firstname')
                lastname = request.POST.get('lastname')
                email = request.POST.get('email')
                password = request.POST.get('password') 
                phone = request.POST.get('mobileNumber')
                role_id = request.POST.get('role_id')
                # superior_id = request.POST.get('superior_id')
                department = request.POST.get('department')
                service_db = request.POST.get('service', 'default')
                full_name = f"{firstname} {lastname}"
                if role_id and role_id != '2':
                    phone = email
                # superior_id=superior_id
                existing_user = CustomUser.objects.using('default').filter(email=email, phone=phone, role_id=role_id).exists()
                exist_inservice = CustomUser.objects.using(service_db).filter(email=email, phone=phone, role_id=role_id).exists()
                if exist_inservice:
                    messages.error(request, "A user with the same email, phone, and role already exists.")
                    return redirect('/register_new_user?id=0')
                else:
                    from django.db import transaction

                    user = CustomUser(
                        full_name=full_name,email=email,phone=phone,role_id=role_id
                    )
                    user.username = user.email
                    user.is_active = True 
                    try:
                        validate_password(password, user=user)
                        user.set_password(password)
                        if existing_user:
                            user = CustomUser.objects.using('default').get(email=email, phone=phone, role_id=role_id)
                            user_id = user.id
                        else:
                            with transaction.atomic(using='default'):
                                user.save(using='default') 
                                password_storage.objects.using('default').create(
                                    user_id=user.id,
                                    passwordText=password
                                )
                            user_id = user.id
                        if department:
                            user_dept_services.objects.using('default').get_or_create(
                                user_id=user_id,department_id=int(department),service_id=int(service_db)
                            )
                        if service_db:
                            user.id = user_id
                            with transaction.atomic(using=service_db):
                                user.save(using=service_db)
                                password_storage.objects.using(service_db).create(
                                    user_id=user.id,
                                    passwordText=password
                                )
                        assigned_menus = RoleMenuMaster.objects.using(service_db).filter(role_id=role_id)
                        for menu in assigned_menus:
                            UserMenuDetails.objects.using(service_db).create(
                                user_id=user.id,
                                menu_id=menu.menu_id,
                                role_id=role_id
                        )

                        messages.success(request, "User registered successfully!")

                    except ValidationError as e:
                        messages.error(request, ' '.join(e.messages))
                    
            else:
                firstname = request.POST.get('firstname')
                lastname = request.POST.get('lastname')
                email = request.POST.get('email')
                full_name = f"{firstname} {lastname}"
                phone = request.POST.get('mobileNumber')
                role_id = request.POST.get('role_id')
                # superior_id = request.POST.get('superior_id')
                if role_id and role_id != '2':
                    phone = email

                user = CustomUser.objects.get(id=id)
                user.full_name = full_name
                user.email = email
                user.phone = phone
                user.role_id = role_id
                # user.superior_id = superior_id
                user.save()
                from django.utils import timezone
                department = request.POST.get('department')
                service_db = request.POST.get('service', 'default')
                if department:
                    obj, created = user_dept_services.objects.using('default').update_or_create(
                        user_id=id,
                        department_id=department,
                        service_id=service_db,
                        defaults={
                            'updated_at': timezone.now(),
                            'updated_by': id,
                        }
                    )

                messages.success(request, "User details updated successfully!")
            return redirect('/masters?entity=user&type=i')


        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            fun = tb[0].name
            callproc("stp_error_log",[fun,str(e),request.user.id])  
            print(f"error: {e}")
            messages.error(request, 'Oops...! Something went wrong!')
            response = {'result': 'fail','messages ':'something went wrong !'}   

def forgot_password(request):
    try:
        if request.method =="GET":
            type = request.GET.get('type')
            return render(request,'Account/forgot-password.html',{'type':type}) 
        if request.method == "POST":
            email = request.POST.get('email')
            if CustomUser.objects.filter(email=email).exists():
                messages.success(request, 'User id valid...Please update your password')
                type = 'pass'
            else:
                messages.error(request, 'User does not exist.Please Enter Correct Email.')
                type='email'
            return render(request,'Account/forgot-password.html',{'type':type,'email':email}) 

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), request.user.id])
        messages.error(request, 'Oops...! Something went wrong!')

# def logoutView(request):
#     logout(request)
#     return redirect("Account")  

def home(request):
    return render(request,'Account/home.html') 

@login_required
def search(request):
    results = []
    try:
        query = request.GET.get('q')
        if query != "":
           results = callproc("stp_get_application_search",[query])        
    except Exception as e:
        print("error-"+e)
    finally:
        return render(request, 'Bootstrap/search_results.html', {'query': query, 'results': results})

@login_required       
def change_password(request):
    try:
        if request.method == "POST":
            password = request.POST.get('password')  # The password entered by the user
            username = request.session.get('username', '')  # The username from the session
            user = CustomUser.objects.get(email=username)
            if check_password(password, user.password):
                status = "1"
            else:
                status = "0" 

    except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            fun = tb[0].name
            callproc("stp_error_log",[fun,str(e),request.user.id])  
            print(f"error: {e}")
            messages.error(request, 'Oops...! Something went wrong!')
            response = {'result': 'fail','messages ':'something went wrong !'}
    finally:
        if request.method == "GET":
            return render(request,'Account/change_password.html')
        else:
           return JsonResponse({'status': status})
        
@login_required
def reset_password(request):
    try:
        email = request.POST.get('email')
        if not email:
            email = request.session.get('username', '')
        password = request.POST.get('password')
        user = CustomUser.objects.get(email=email)
        # Update password
        user.set_password(password)
        user.save()
        messages.success(request, 'Password has been successfully updated.')

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), request.user.id])
        messages.error(request, 'Oops...! Something went wrong!')
    
    finally:
        return redirect( f'change_password')
    
@login_required    
def forget_password_change(request):
    try:
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = CustomUser.objects.get(email=email)
        user.set_password(password)
        user.save()
        messages.success(request, 'Password has been successfully updated.')

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), request.user.id])
        messages.error(request, 'Oops...! Something went wrong!')
    
    finally:
        return redirect( f'Login')
        
def dashboard(request):
    return render(request,'Bootstrap/index.html') 

def buttons(request):
    return render(request,'Bootstrap/buttons.html') 

def cards(request):
    return render(request,'Bootstrap/cards.html') 

def utilities_color(request):
    return render(request,'Bootstrap/utilities-color.html') 

def utilities_border(request):
    return render(request,'Bootstrap/utilities-border.html') 

def utilities_animation(request):
    return render(request,'Bootstrap/utilities-animation.html') 

def utilities_other(request):
    return render(request,'Bootstrap/utilities-other.html') 

def error_page(request):
    return render(request,'Bootstrap/404.html')

def blank(request):
    return render(request,'Bootstrap/blank.html')

def charts(request):
    return render(request,'Bootstrap/charts.html')

def tables(request):
    return render(request,'Bootstrap/tables.html')

def citizenLoginAccount(request):
    try:
        if request.GET.get('expired'):
            messages.warning(request, "Your session has expired. Please login again.")
            
        if request.method == "GET":
            # request.session.flush()            
            # service_db = request.GET.get('service_db')
            
            service = request.GET.get('service')
            
            # if service is None or service.strip().lower() == "none":
            #     service = request.session.get('service')  
            
            request.session['service'] = service
            
            ServiceType = service_master.objects.using('default').values_list("ser_id", "ser_name")

            return render(request, 'citizenAccount/citizenLogin.html',{'service':service, "parameter":ServiceType})

        elif request.method == "POST":

            service_db = request.POST.get('services')
            service = request.POST.get('service')
            request.session['dropdown'] = service_db
            request.session['normal'] = service
            if service is None or service == "":
                service_db = service_db
            else: service_db = service
            request.session['service_db'] = service_db
            request.session['service'] = service_db
            phone_number = request.POST.get('username', '').strip()


            if phone_number:
                
                # if CustomUser.objects.filter(phone=phone_number, role_id=2).exists():
                #     request.session['phone_number'] = phone_number
                #     return redirect(f'/OTPScreen?service_db={service_db}')
                
                if CustomUser.objects.using(service_db).filter(phone=phone_number, role_id=2).exists():
                    request.session['phone_number'] = phone_number
                    return redirect(f'/OTPScreen?service_db={service_db}')
                else:
                    messages.warning(request, "The phone number entered is not registered. Please register yourself.")
                    return redirect(f'/citizenRegisterAccount?service_db={service_db}')

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),''])  
        messages.error(request, 'Oops...! Something went wrong!')
        return redirect(f'/citizenRegisterAccount?service_db={service_db}')
        
@csrf_exempt
def citizenRegisterAccount(request):
    context = {
        'firstName': '','lastName': '','email': '', 'mobileNumber': ''
    }
    try:
        if request.method == "GET":
            # service_db = request.GET.get('service_db')
            service_db = request.session['service']
            
            if service_db is None or service_db.strip().lower() == "none":
                service_db = ""
            
            ServiceType = service_master.objects.using('default').values_list("ser_id", "ser_name")
            
            context['service_db'] = service_db
            context['parameter'] = ServiceType
            return render(request, 'citizenAccount/citizenRegister.html', context)

        elif request.method == "POST":
            service_db = request.POST.get('service_db')
            request.session['service_db'] = service_db
            first_name = request.POST.get('firstname').strip()
            last_name = request.POST.get('lastname').strip()
            email = request.POST.get('email').strip()
            mobile_number = request.POST.get('mobileNumber').strip()

            if CustomUser.objects.filter(phone=mobile_number, role_id=2 ).exists():
                messages.warning(request, "This mobile number is already registered. Please LogIn.")
                return redirect(f'/citizenRegisterAccount?service_db={service_db}') 
            # elif CustomUser.objects.filter(email=email, role_id=2).exists():
            #     messages.warning(request, "This emailId is already registered. ")
            #     return redirect(f'/citizenRegisterAccount?service_db={service_db}') 
            else:
                request.session['first_name'] = first_name
                request.session['last_name'] = last_name
                request.session['email'] = email
                request.session['mobile_number'] = mobile_number
                return redirect(f'/OTPScreenRegistration?service_db={service_db}')
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),''])  
        messages.error(request, 'Oops...! Something went wrong!')
        return redirect(f'/citizenRegisterAccount?service_db={service_db}')
    
@csrf_exempt
def OTPScreen(request):
    
    if request.method == "GET":
        service_db = request.GET.get('service_db')
        request.session['service_db'] = service_db
        phone_number = request.session.get('phone_number')
        sms_templates = smstext.objects.all()
        
        try:

            servicefetch = service_master.objects.using('default').get(ser_id=service_db)
            ser_name = servicefetch.ser_name

            otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            # otp ='123456'
            OTPVerification.objects.create(
                mobile=phone_number,
                otp_text=otp,
                created_at=timezone.now()
            )
            
            if sms_templates:
                template_id = sms_templates[0].template_id 
                message = sms_templates[0].template_name 
                
                action = "Login"  
                service = ser_name  

                message = format_message(message, otp, action, service)
                send_sms(phone_number, message, template_id)
            
            messages.success(request, "OTP sent successfully!")
        except Exception as e:
            messages.error(request, "Failed to send OTP. Please try again.")
            tb = traceback.extract_tb(e.__traceback__)
            fun = tb[0].name
            callproc("stp_error_log",[fun,str(e),''])  
        return render(request, 'OTPScreen/OTPScreen.html',{'service_db':service_db})

def format_message(template, otp_value, action, service):
    message = template.replace("@otp", otp_value)
    message = message.replace("@action", action)
    message = message.replace("@service", service)
    return message

def send_sms(mobile, message, template_id): 
    try:
        url = (
            f"https://push3.aclgateway.com/servlet/com.aclwireless.pushconnectivity.listeners.TextListener"
            f"?appid=MahaITcidc&userId=MahaITcidc&pass=mitcidc_10&contenttype=1"
            f"&from=MAHGOV&to={mobile}&text={message}&alert=1&selfid=true&dlrreq=true"
            f"&intflag=false&dtm={template_id}"
        )
        response = requests.get(url)
        print(response.text)
        
        sms_log(response, mobile, message, template_id)
        
    except Exception as e:
        messages.error("Failed to send OTP. Please try again.")

# Optimized SMS log function
def sms_log(response, mobile, message, template_id):
    try:
        content = response.text or ""
        content_type = response.headers.get('Content-Type', '')
        response_status = response.status_code or ""
        is_successful = response.ok
        response_url = getattr(response, 'url', '')
        status_description = response.reason or str(response.status_code)
        unique_id = '' 
        user_id = '1' 

        logging.info(f"SMS sent to {mobile} with status {response_status} and content: {content}")

        smslog.objects.create(
            mobile=mobile or '',
            message=message or '',
            user_id=user_id,
            content=content,
            status=response_status,
            unique_id=unique_id,
            content_type=content_type,
            response_status=response_status,
            is_successful=is_successful,
            response_url=response_url,
            status_description=status_description,
            template_id=template_id or ''
        )
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),''])  
        messages.error('Oops...! Something went wrong!')
                
@csrf_exempt
def OTPScreenPost(request):
    if request.method == "POST":
        phone_number = request.session.get('phone_number')  
        entered_otp = request.POST.get('otp')
        service_db = request.POST.get('service_db')
        request.session['service_db'] = service_db

        if not phone_number:
            messages.error(request, "Phone number not found. Please log in again.")
            return redirect(f'/citizenLoginAccount?service_db={service_db}')

        try:
            otp_record = OTPVerification.objects.filter(mobile=phone_number).order_by('-id').first()
            
            if otp_record and otp_record.otp_text == entered_otp:
                otp_record.delete()

                user = CustomUser.objects.get(phone=phone_number, role_id=2)
                servicefetch = service_master.objects.using('default').get(ser_id=service_db)
                redirect_to = servicefetch.citizen_page
                
                # request.session.cycle_key()
                request.session["user_id"]=(str(user.id))
                request.session["role_id"] = str(user.role_id)
                request.session['full_name'] = user.full_name
                request.session['phone_number'] = phone_number
                request.session['citizen_page'] = redirect_to
                request.session['otp_verified'] = True
                
                ua = request.META.get('HTTP_USER_AGENT', '')
                ip = get_client_ip(request)

                request.session['_ua_hash'] = hashlib.sha256(ua.encode()).hexdigest()
                request.session['_ua_raw'] = ua
                request.session['_ip'] = ip
                
                if '_session_expired' in request.session:
                    del request.session['_session_expired']
                if '_user_logged_out' in request.session:
                    del request.session['_user_logged_out']
                
                messages.success(request, "OTP verified successfully!")
                return redirect(redirect_to)
            else:
                messages.error(request, "Invalid OTP. Please try again.")
                return redirect(f'/citizenLoginAccount?service_db={service_db}')

        except OTPVerification.DoesNotExist:
            messages.error(request, "No OTP record found. Please request a new OTP.")
            return redirect(f'/citizenLoginAccount?service_db={service_db}')
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            fun = tb[0].name
            callproc("stp_error_log", [fun, str(e), ''])
            logger.error(f"Error rendering onetimepage.html: {str(e)}")
            return HttpResponse("An error occurred while trying to load the page.", status=500)

    return render(request, 'citizenAccount/citizenLogin.html', {'error': 'Invalid request method.','service_db':service_db})

@csrf_exempt
def checkmobilenumber(request):
    if request.method == "POST":
        data = json.loads(request.body)
        mobile_number = data.get('mobileNumber')
        try:
            user = CustomUser.objects.get(phone=mobile_number)
            return JsonResponse({'exists': True})
        except CustomUser.DoesNotExist:
            otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            print(f"Sending OTP {otp} to {mobile_number}")
            
            OTPVerification.objects.create(
                mobile=mobile_number,  
                otp_text=otp,
                created_at=timezone.now()
            )

            return JsonResponse({'exists': False, 'otp_sent': True})

# OTP For Registration
@csrf_exempt
def OTPScreenRegistration(request):
    if request.method == "GET":
        service_db = request.GET.get('service_db')
        request.session['service_db'] = service_db
        phone_number = request.session.get('mobile_number')
        sms_templates = smstext.objects.all()
        
        if not phone_number:
            messages.error(request, "Phone number is required.")
            return redirect(f'/citizenRegisterAccount?service_db={service_db}')

        servicefetch = service_master.objects.using('default').get(ser_id=service_db)
        ser_name = servicefetch.ser_name
        
        otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        # otp ='123456'
        try:
            OTPVerification.objects.create(
                mobile=phone_number,
                otp_text=otp,
                created_at=timezone.now()
            )
            
            if sms_templates:
                template_id = sms_templates[0].template_id
                message = sms_templates[0].template_name
                
                action = "Registration"
                service = ser_name
                
                message = format_message(message, otp, action, service)
                
                send_sms(phone_number, message, template_id)
            
            messages.success(request, "OTP sent successfully!")
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            fun = tb[0].name
            callproc("stp_error_log", [fun, str(e), 'user'])  
            messages.error(request, f"Failed to send OTP. Error: {str(e)}")
        
        return render(request, 'OTPScreen/OTPScreenRegistration.html',{'service_db':service_db})

@csrf_exempt
def verify_otp(request):
    if request.method == "POST":
        phone_number = request.session.get('mobile_number')
        first_name = request.session.get('first_name')
        last_name = request.session.get('last_name')
        email = request.session.get('email')
        entered_otp = request.POST.get('otp')
        service_db = request.POST.get('service_db')
        request.session['service_db'] = service_db
        if not phone_number:
            messages.error(request, "Phone number not found. Please log in again.")
            return redirect(f'/citizenRegisterAccount?service_db={service_db}')

        try:
            otp_record = OTPVerification.objects.filter(mobile=phone_number).order_by('-id').first()

            if otp_record and otp_record.otp_text == entered_otp:
                otp_record.delete()
                role_id = roles.objects.get(id=2)

                if CustomUser.objects.filter(role_id=2, phone=phone_number ).exists():
                    messages.error(request, "An account with this details already exists.")
                    context = {
                        'firstName': first_name,
                        'lastName': last_name,
                        'email': email,
                        'mobileNumber': phone_number,'service_db':service_db
                    }
                    return render(request, 'citizenAccount/citizenRegister.html', context)

                # if CustomUser.objects.using('default').filter(email=email, role_id=2).exists():
                #     messages.warning(request, "This email is already registered.")
                #     return redirect(f'/citizenRegisterAccount?service_db={service_db}')
                
                existing_user = CustomUser.objects.using('default').filter(phone=phone_number, role_id=role_id.id).exists()
                exist_inservice = CustomUser.objects.using(service_db).filter(phone=phone_number, role_id=role_id.id).exists()
                user_id = None
                if exist_inservice:
                    messages.error(request, "A user with the same email, phone, and role already exists.")
                    return redirect(f'/citizenRegisterAccount?service_db={service_db}')
                else:
                    if existing_user:
                        user = CustomUser.objects.using('default').get(phone=phone_number, role_id=role_id.id)
                        user_id = user.id
                    else:
                        user = CustomUser.objects.using('default').create(
                            full_name=f"{first_name} {last_name}",
                            email=email,
                            phone=phone_number,
                            first_time_login=True,
                            role_id=role_id.id
                        )
                        user_id = user.id

                    if service_db:
                        user = CustomUser.objects.using(service_db).create(
                            id = user_id,
                            full_name=f"{first_name} {last_name}",
                            email=email,
                            phone=phone_number,
                            first_time_login=True,
                            role_id=role_id.id
                        )

                    assigned_menus = RoleMenuMaster.objects.using(service_db).filter(role_id=role_id.id)
                    for menu in assigned_menus:
                        UserMenuDetails.objects.using(service_db).create(
                            user_id=user.id,
                            menu_id=menu.menu_id,
                            role_id=user.role_id
                        )

                request.session['user_id'] = user.id
                request.session['phone_number'] = phone_number

                messages.success(request, "Registered successfully! OTP verified.")
                return redirect(f'/citizenLoginAccount?service={service_db}')
                # return redirect(f'/citizenLoginAccount?service_db={service_db}')

            else:
                messages.error(request, "Invalid OTP. Please try again.")
                context = {
                    'firstName': first_name,
                    'lastName': last_name,
                    'email': email,
                    'mobileNumber': phone_number,'service_db':service_db
                }
                return render(request, 'citizenAccount/citizenRegister.html', context)

        except OTPVerification.DoesNotExist:
            messages.error(request, "Invalid OTP. Please try again.")
            context = {
                'firstName': first_name,
                'lastName': last_name,
                'email': email,
                'mobileNumber': phone_number,'service_db':service_db
            }
            return render(request, 'citizenAccount/citizenRegister.html', context)
        
        except Exception as e:
            messages.error(request, "The mobile number you entered already exists. Please try again with a different number.")
            context = {
                'firstName': first_name,
                'lastName': last_name,
                'email': email,
                'mobileNumber': phone_number,'service_db':service_db
            }
            return render(request, 'citizenAccount/citizenRegister.html', context)

    return render(request, 'OTPScreen/OTPScreenRegistration.html', {'error': 'Invalid request method.','service_db':service_db})

@csrf_exempt
def aple_sarkar_Register(request):
    context = {
        'firstName': '', 'lastName': '', 'email': '', 'mobileNumber': ''
    }

    try:
        if request.method == "GET":
            service_db = request.GET.get('service_db')
            request.session['service_db'] = service_db
            context['service_db'] = service_db
            return render(request, 'citizenAccount/aplesarkarRegister.html', context)

        elif request.method == "POST":
            service_db = request.POST.get('service_db')
            request.session['service_db'] = service_db
            first_name = request.POST.get('firstname').strip()
            last_name = request.POST.get('lastname').strip()
            email = request.POST.get('email').strip()
            mobile_number = request.POST.get('mobileNumber').strip()

            if CustomUser.objects.filter(phone=mobile_number, role_id=2).exists():
                messages.warning(request, "This mobile number is already registered. Please LogIn.")
                return redirect(f'/aple_sarkar_Register?service_db={service_db}') 
            # elif CustomUser.objects.filter(email=email, role_id=2).exists():
            #     messages.warning(request, "This emailId is already registered.")
            #     return redirect(f'/aple_sarkar_Register?service_db={service_db}') 
            else:
                request.session['first_name'] = first_name
                request.session['last_name'] = last_name
                request.session['email'] = email
                request.session['mobile_number'] = mobile_number
                return redirect(f'/OTPScreenRegistration?service_db={service_db}')

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),mobile_number])  
        messages.error(request, 'Oops...! Something went wrong!')
        
def aple_sarkar_Login(request):
    try:
        if request.method == "GET":
            request.session.flush()            
            service_db = request.GET.get('service_db')
            request.session['service_db'] = service_db
            return render(request, 'citizenAccount/aplesarkarLogin.html',{'service_db':service_db})

        elif request.method == "POST":
            service_db = request.POST.get('service_db')
            request.session['service_db'] = service_db
            phone_number = request.POST.get('username', '').strip()

            if phone_number:
                if CustomUser.objects.filter(phone=phone_number, role_id=2).exists():
                    request.session['phone_number'] = phone_number
                    return redirect(f'/OTPScreen?service_db={service_db}')
                else:
                    messages.warning(request, "The phone number entered is not registered. Please register yourself.")
                    return redirect(f'/aple_sarkar_Register?service_db={service_db}')

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),phone_number])  
        messages.error(request, 'Oops...! Something went wrong!')
        return redirect(f'/aple_sarkar_Register?service_db={service_db}')