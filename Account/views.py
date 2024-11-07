import json
import random
import string
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render,redirect
from django.contrib.auth import authenticate, login ,logout,get_user_model
from Account.forms import RegistrationForm
from Account.models import  CustomUser,user_dept_services,MenuMaster,RoleMenuMaster,UserMenuDetails, OTPVerification, password_storage
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
from django.db import IntegrityError
from django.urls import reverse
from django.http import HttpResponseBadRequest
import logging
import requests
from django.db import models

# Set up logging
logger = logging.getLogger(__name__)

@csrf_exempt
def Login(request):
    if request.method=="GET":
       request.session.flush()
       return render(request,'Account/login.html')
    
    if request.method=="POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            request.session.cycle_key()
            request.session["username"]=(str(username))
            request.session["full_name"]=(str(user.full_name))
            request.session["user_id"]=(str(user.id))
            request.session["role_id"] = str(user.role_id)
            
            if remember_me == 'on':
                request.session.set_expiry(1209600)  # 2 weeks
            else:
                request.session.set_expiry(0)  # Browser close
            return redirect('services') 
        else:
            messages.error(request, 'Invalid Credentials')
            return redirect("Account")

def services(request):
    try:
        if request.method =="GET":
            service = callproc("stp_get_user_services",[request.user.id])
            return render(request,'Account/services.html',{'service':service}) 
        if request.method == "POST":
            service_db = request.POST.get('service')
            request.session['service_db'] = service_db
            return redirect('index') 
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), request.user.id])
        messages.error(request, 'Oops...! Something went wrong!')

def logoutView(request):
    logout(request)
    return redirect("Account")  

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
            user_dept_ser =user_dept_services.objects.using('default').filter(user_id=id1) 
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
                # superior_id=superior_id
                user = CustomUser(
                    full_name=full_name,email=email,phone=phone,role_id=role_id
                )
                user.username = user.email
                user.is_active = True 
                try:
                    validate_password(password, user=user)
                    user.set_password(password)
                    user.save(using='default')
                    password_storage.objects.using('default').create(user=user, passwordText=password)
                    user_dept_services.objects.using('default').get_or_create(
                        user_id=user.id,department_id=department,service_id=service_db,
                        defaults={ 'created_at': timezone.now(),  'created_by': request.user.id }
                    )
                    if service_db:
                        user.save(using=service_db)
                        password_storage.objects.using(service_db).create(user=user, passwordText=password)

                    assigned_menus = RoleMenuMaster.objects.filter(role_id=role_id)
                    for menu in assigned_menus:
                        UserMenuDetails.objects.create(
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

                user = CustomUser.objects.get(id=id)
                user.full_name = full_name
                user.email = email
                user.phone = phone
                user.role_id = role_id
                # user.superior_id = superior_id
                user.save()

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


def logoutView(request):
    logout(request)
    return redirect("Account")  

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
def menu_admin(request):
    pre_url = request.META.get('HTTP_REFERER')
    header = []
    data = []
    name = ''
    entity = ''
    type = ''
    global user
    user  = request.session.get('user_id', '')
    try:
       
        if request.method=="GET":
            entity = request.GET.get('entity', '')
            type = request.GET.get('type', '')
            datalist1 = callproc("stp_get_masters",[entity,type,'name',user])
            name = datalist1[0][0]
            header = callproc("stp_get_masters", [entity, type, 'header',user])
            rows = callproc("stp_get_masters",[entity,type,'data',user])
            # Encrypt each row's ID before rendering
            data = []
            for row in rows:
                encrypted_id = encrypt_parameter(str(row[0]))
                data.append((encrypted_id,) + row[1:])

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),request.user.id])  
        print(f"error: {e}")
        messages.error(request, 'Oops...! Something went wrong!')
        response = {'result': 'fail','messages ':'something went wrong !'}   
    finally:
        if request.method=="GET":
            return render(request,'Master/menu_admin.html', {'entity':entity,'type':type,'name':name,'header':header,'data':data,'pre_url':pre_url})
        elif request.method=="POST":  
            new_url = f'/masters?entity={entity}&type={type}'
            return redirect(new_url) 
        
@login_required        
def delete_menu(request):
    try:
        type = request.GET.get('type', '')
        if request.method == "POST" and type == 'delete':
            menu_id1 = request.POST.get('menu_id', '')
            menu_id = decrypt_parameter(menu_id1)
            try:
                menu = get_object_or_404(MenuMaster, menu_id=menu_id)
                menu.delete()
        
                return JsonResponse({'success': True, 'message': 'Menu Successfully Deleted!'})
            except Exception as e:
                print(f"An error occurred: {e}")
                return JsonResponse({'success': False, 'message': 'An error occurred while deleting the menu.'})
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        callproc("stp_error_log", [tb[0].name, str(e), request.user.id])
        print(f"error: {e}")
        messages.error(request, 'Oops...! Something went wrong!')
        response = {'result': 'fail', 'messages': 'something went wrong!'}

    finally:
        return JsonResponse({'success': False, 'message': 'Invalid request method.'})


@login_required
def menu_master(request):
    try:
        type = request.GET.get('type', '')
        if request.method == "POST" and type == 'delete':
            menu_id = request.POST.get('menu_id', '')
            try:
                menu = get_object_or_404(MenuMaster, menu_id=menu_id)
                menu.delete()
        
                return JsonResponse({'success': True, 'message': 'Menu Successfully Deleted!'})
            except Exception as e:
                print(f"An error occurred: {e}")
                return JsonResponse({'success': False, 'message': 'An error occurred while deleting the menu.'})


        if request.method == "GET":
            menu_id = request.GET.get('menu_id', '')
            if menu_id != '0':
                menu_id1 = decrypt_parameter(menu_id)
            menu = callproc("stp_get_dropdown_values",['menu'])
            roles = callproc("stp_get_dropdown_values",['roles'])
            users = callproc("stp_get_dropdown_values",['user'])

            if menu_id != '0':
                menus = get_object_or_404(MenuMaster, menu_id=menu_id1)

        elif request.method == "POST" and type == 'create':
            menu_id = request.POST.get('menu_id', '')
            if menu_id != '0':
                menu_id1 = decrypt_parameter(menu_id)
            fields = ['menu_name', 'menu_action', 'parent', 'menu_parent', 'sub_parent', 'sub_menu_parent', 'sub_parent1', 'sub_menu_parent1']
            menu_name, menu_action, parent, menu_parent, sub_parent, sub_menu_parent, sub_parent1, sub_menu_parent1= [request.POST.get(field, '') for field in fields]

            menu_parent_id = menu_parent if menu_parent else -1
            sub_menu_id = sub_menu_parent if sub_menu_parent else -1
            sub_menu_id1 = sub_menu_parent1 if sub_menu_parent1 else -1
            menu_action_value = menu_action if menu_action else '#'


            user_id = request.session.get('user_id', '')

            # if user_id:
            #     try:
            #         user = CustomUser.objects.get(id=user_id)
            #     except CustomUser.DoesNotExist:
            #         user = None

            if menu_id == '0':
                menu_count = MenuMaster.objects.count() + 1
                icon = 'fas fa ' + request.POST.get('menu_icon','')

                try:
                    MenuMaster.objects.create(
                        menu_name=menu_name, menu_action=menu_action_value, menu_is_parent=parent,
                        menu_parent_id=menu_parent_id, is_sub_menu=sub_parent, sub_menu=sub_menu_id,
                        is_sub_menu2=sub_parent1, sub_menu2=sub_menu_id1, menu_order=menu_count,menu_icon=icon,created_by=user_id)
                    messages.success(request, "Menu Successfully Created!")
                except Exception as e:
                    print(f"An error occurred: {e}")
            else:
                try:
                    MenuMaster.objects.filter(menu_id=menu_id1).update(
                        menu_name=menu_name,
                        menu_action=menu_action_value,
                        menu_is_parent=parent,
                        menu_parent_id=menu_parent_id,
                        is_sub_menu=sub_parent,
                        sub_menu=sub_menu_id,
                        is_sub_menu2=sub_parent1,
                        sub_menu2=sub_menu_id1,
                        updated_by=user_id
                    )
                    messages.success(request, "Menu Successfully Updated!")

                except Exception as e:
                    print(f"An error occurred: {e}")
                    messages.error(request, "An error occurred while updating the menu.")

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        callproc("stp_error_log", [tb[0].name, str(e), request.user.id])
        print(f"error: {e}")
        messages.error(request, 'Oops...! Something went wrong!')
        response = {'result': 'fail', 'messages': 'something went wrong!'}

    finally:
        if request.method == "GET":
            return render(request, 'Master/menu_master.html', {'menu': menu,'type': type,'roles': roles, 'users': users,'menu_id': menu_id,'order': 'order' if type == 'order' else None,'menus': menus if menu_id != '0' else None})
        elif request.method == "POST":
            return redirect('/menu_admin?entity=menu&type=i')
        
@login_required
def assign_menu(request):
    try:  
       if request.method == "POST":
        type= request.POST.get('type','')
        if type ==  'role':
            user_id = request.session.get('user_id', '')
            if user_id:
                try:
                    user = CustomUser.objects.get(id=user_id)
                except CustomUser.DoesNotExist:
                    user = None
            roleId = request.POST.get('role_id', '')
            menuIds = request.POST.getlist('menu_list')  

            try:
                RoleMenuMaster.objects.filter(role_id=roleId).delete()
                
                for menu_id in menuIds:
                    RoleMenuMaster.objects.create(
                        role_id=roleId,
                        menu_id=menu_id,
                        created_by = user
                    )
            except Exception as e:
                print(f"An error occurred: {e}")
                messages.error(request, "An error occurred while updating menus.")

            try:
                UserMenuDetails.objects.filter(role_id=roleId).delete()

                users = CustomUser.objects.filter(role_id=roleId)

                for user in users:
                    for menu_id in menuIds:
                        UserMenuDetails.objects.create(
                            user_id=user.id,
                            menu_id=menu_id,
                            role_id=roleId,
                            created_by = user
                        )
                
                messages.success(request, "Menus successfully Assigned to Selected Role!")
            
            except Exception as e:
                print(f"An error occurred: {e}")
                messages.error(request, "An error occurred while updating menus.")

        if type == 'user':
            userId = request.POST.get('user_id', '')
            menuIds = request.POST.getlist('menu_list') 

            try:
                user_id = request.session.get('user_id', '')
                if user_id:
                    try:
                        user = CustomUser.objects.get(id=user_id)
                    except CustomUser.DoesNotExist:
                        user = None
                user = CustomUser.objects.get(id=userId)
                roleId = user.role_id

                existing_count = UserMenuDetails.objects.filter(user_id=userId).count()

                if existing_count > 0:
                    UserMenuDetails.objects.filter(user_id=userId).delete()
                
                for menu_id in menuIds:
                    UserMenuDetails.objects.create(
                        user_id=userId,
                        menu_id=menu_id,
                        role_id=roleId,
                        created_by = user
                    )

                messages.success(request, "User menu details successfully updated!")

            except CustomUser.DoesNotExist:
                messages.error(request, "User does not exist.")
            except Exception as e:
                print(f"An error occurred: {e}")
                messages.error(request, "An error occurred while updating user menu details.")

            

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        callproc("stp_error_log", [tb[0].name, str(e), request.user.id])
        print(f"error: {e}")
        messages.error(request, 'Oops...! Something went wrong!')
        response = {'result': 'fail', 'messages': 'something went wrong!'}

    finally:
        if request.method == "POST":
            return redirect('/menu_admin?entity=menu&type=i')
    
@login_required    
def get_assigned_values(request):
    menu_array = []
    try:
        if request.method == "POST":
            data_type = request.POST.get('type','')
            selected_id = request.POST.get('id', '')
            menu_array= callproc("stp_get_assign_menu_values", [selected_id, data_type])
            response = {'result': 'success', 'menu_array': menu_array}
        else:
            response = {'result': 'fail', 'message': 'Invalid request method'}
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        callproc("stp_error_log", [tb[0].name, str(e), request.user.id])
        print(f"error: {e}")
        response = {'result': 'fail', 'message': 'Something went wrong!'}
    finally:
        return JsonResponse(response)

@login_required
def menu_order(request):
    pre_url = request.META.get('HTTP_REFERER')
    header = []
    data = []
    name = ''
    entity = ''
    type = ''
    
    try:
        if request.user.is_authenticated ==True:                
                global user
                user = request.user.id   

        if request.method=="GET":
            type = request.GET.get('type', '')
            menu_id = request.GET.get('menu_id', '')
            menu_id1 = decrypt_parameter(menu_id)
            data = callproc("stp_get_menu_order",[menu_id1])
           
        if request.method=="POST":
             for key, value in request.POST.items():
                if key.startswith('menu_order_'):
                    try:
                        row_number = key.split('_')[2]  
                        menu_id = request.POST.get(f'menu_id_{row_number}')
                        menu_item = MenuMaster.objects.get(menu_id=menu_id)
                        menu_item.menu_order = value
                        menu_item.save()
                        messages.success(request, "Menu Order Succesfully Updated!")
                        
                    except Exception as e:
                        print(f"An error occurred: {e}")
                        messages.error(request, "An error occurred while updating the menu.")
                 
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),request.user.id])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally:
        if request.method=="GET":
            return render(request,'Master/menu_master.html', {'type':type,'name':name,'header':header,'data':data})
        elif request.method=="POST":  
            new_url = f'/menu_admin?entity=menu&type=i'
            return redirect(new_url) 

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
        if request.method == "GET":
            request.session.flush()            
            service_db = request.GET.get('service_db')
            request.session['service_db'] = service_db
            return render(request, 'citizenAccount/citizenLogin.html',{'service_db':service_db})

        elif request.method == "POST":
            service_db = request.POST.get('service_db')
            request.session['service_db'] = service_db
            phone_number = request.POST.get('username', '').strip()


            if phone_number:
                if CustomUser.objects.filter(phone=phone_number).exists():
                    request.session['phone_number'] = phone_number
                    return redirect(f'/OTPScreen?service_db={service_db}')
                else:
                    messages.warning(request, "The phone number entered is not registered. Please register yourself.")
                    return redirect(f'/citizenRegisterAccount?service_db={service_db}')

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),user])  
        messages.error(request, 'Oops...! Something went wrong!')
        return redirect(f'/citizenRegisterAccount?service_db={service_db}')
        
@csrf_exempt
def citizenRegisterAccount(request):
    context = {
        'firstName': '','lastName': '','email': '', 'mobileNumber': ''
    }

    if request.method == "GET":
        service_db = request.GET.get('service_db')
        request.session['service_db'] = service_db
        context['service_db'] = service_db
        return render(request, 'citizenAccount/citizenRegister.html', context)

    elif request.method == "POST":
        service_db = request.POST.get('service_db')
        request.session['service_db'] = service_db
        first_name = request.POST.get('firstname').strip()
        last_name = request.POST.get('lastname').strip()
        email = request.POST.get('email').strip()
        mobile_number = request.POST.get('mobileNumber').strip()

        if CustomUser.objects.filter(phone=mobile_number).exists():
            messages.warning(request, "This mobile number is already registered. Please LogIn.")
            return redirect(f'/citizenRegisterAccount?service_db={service_db}') 
        elif CustomUser.objects.filter(email=email).exists():
            messages.warning(request, "This emailId is already registered. ")
            return redirect(f'/citizenRegisterAccount?service_db={service_db}') 
        else:
            request.session['first_name'] = first_name
            request.session['last_name'] = last_name
            request.session['email'] = email
            request.session['mobile_number'] = mobile_number
            return redirect(f'/OTPScreenRegistration?service_db={service_db}')
 
@csrf_exempt
def OTPScreen(request):
    
    if request.method == "GET":
        service_db = request.GET.get('service_db')
        request.session['service_db'] = service_db
        phone_number = request.session.get('phone_number')
        sms_templates = smstext.objects.all()
        
        try:
            otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            
            OTPVerification.objects.create(
                mobile=phone_number,
                otp_text=otp,
                created_at=timezone.now()
            )
            
            if sms_templates:
                template_id = sms_templates[0].template_id 
                message = sms_templates[0].template_name 
                
                action = "Login"  
                service = "Drainage connection"  

                message = format_message(message, otp, action, service)
                send_sms(phone_number, message, template_id)
            
            messages.success(request, "OTP sent successfully!")
        except Exception as e:
            messages.error(request, "Failed to send OTP. Please try again.")
            tb = traceback.extract_tb(e.__traceback__)
            fun = tb[0].name
            callproc("stp_error_log",[fun,str(e),user])  
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
        callproc("stp_error_log",[fun,str(e),user])  
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

                user = CustomUser.objects.get(phone=phone_number)
                
                request.session.cycle_key()
                request.session["user_id"]=(str(user.id))
                request.session["role_id"] = str(user.role_id)
                request.session['full_name'] = user.full_name
                request.session['phone_number'] = phone_number
                messages.success(request, "OTP verified successfully!")
                return redirect('applicationFormIndex')
            else:
                messages.error(request, "Invalid OTP. Please try again.")
                return redirect(f'/citizenLoginAccount?service_db={service_db}')

        except OTPVerification.DoesNotExist:
            messages.error(request, "No OTP record found. Please request a new OTP.")
            return redirect(f'/citizenLoginAccount?service_db={service_db}')

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

        otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])

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
                service = "Drainage connection"
                
                message = format_message(message, otp, action, service)
                
                send_sms(phone_number, message, template_id)
            
            messages.success(request, "OTP sent successfully!")
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            fun = tb[0].name
            callproc("stp_error_log", [fun, str(e), user])  
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

                if CustomUser.objects.filter(email=email).exists():
                    messages.error(request, "An account with this email already exists.")
                    context = {
                        'firstName': first_name,
                        'lastName': last_name,
                        'email': email,
                        'mobileNumber': phone_number,'service_db':service_db
                    }
                    return render(request, 'citizenAccount/citizenRegister.html', context)

                CustomUser.objects.using('default').create(
                    full_name=f"{first_name} {last_name}",
                    email=email,
                    phone=phone_number,
                    first_time_login=True,
                    role_id=role_id.id
                )

                user = CustomUser.objects.using(service_db).create(
                    full_name=f"{first_name} {last_name}",
                    email=email,
                    phone=phone_number,
                    first_time_login=True,
                    role_id=role_id.id
                )

                assigned_menus = RoleMenuMaster.objects.filter(role_id=role_id.id)
                for menu in assigned_menus:
                    UserMenuDetails.objects.create(
                        user_id=user.id,
                        menu_id=menu.menu_id,
                        role_id=user.role_id
                    )

                request.session['user_id'] = user.id
                request.session['phone_number'] = phone_number

                messages.success(request, "Registered successfully! OTP verified.")
                return redirect(f'/citizenLoginAccount?service_db={service_db}')

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
        except IntegrityError:
            messages.error(request, "An account with this email already exists.")
            context = {
                'firstName': first_name,
                'lastName': last_name,
                'email': email,
                'mobileNumber': phone_number,'service_db':service_db
            }
            return render(request, 'citizenAccount/citizenRegister.html', context)
        except Exception as e:
            messages.error(request, "An unexpected error occurred. Please try again.")
            context = {
                'firstName': first_name,
                'lastName': last_name,
                'email': email,
                'mobileNumber': phone_number,'service_db':service_db
            }
            return render(request, 'citizenAccount/citizenRegister.html', context)

    return render(request, 'OTPScreen/OTPScreenRegistration.html', {'error': 'Invalid request method.','service_db':service_db})