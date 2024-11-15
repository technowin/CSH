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
from Account.db_utils import callproc
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
