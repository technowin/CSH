"""
URL configuration for CSH project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.Account, name='Account')
Class-based views
    1. Add an import:  from other_app.views import Account
    2. Add a URL to urlpatterns:  path('', Account.as_view(), name='Account')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls.static import static
from Account.views import *
from Dashboard.views import *
# from Masters.models import site_master
from Masters.views import *
from Reports.views import *
from TrackFlow.views import *
from Masters.views import site_master as sm
from Masters.views import company_master as cm
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
    # APP URLS

    # Account
    path("", Login,name='Account'),
    path("Login", Login,name='Login'),
    path("services/", services,name='services'),
    path("home", home,name='home'),
    path("logout",logoutView,name='logout'),
    path("forgot_password",forgot_password,name='forgot_password'),
    path('search/', search, name='search'),
    path("register_new_user",register_new_user, name="register_new_user"),
    path("reset_password",reset_password, name="reset_password"),
    path("change_password",change_password, name="change_password"),
    path("forget_password_change",forget_password_change, name="forget_password_change"),

    # Dashboard
    path("newdashboard",newdashboard,name='newdashboard'),
    path("get_sites",get_sites,name='get_sites'),
    path("updateGraph",updateGraph, name="updateGraph"),
    path("get_roster_data",get_roster_data, name="get_roster_data"),
    path("get_roster_data_tommorow",get_roster_data_tommorow, name="get_roster_data_tommorow"),

    # TrackFlow
    path('index/', index, name='index'),
    path('matrix_flow', matrix_flow, name='matrix_flow'),

    # Masters
    path('masters/', masters, name='masters'),
    path('sample_xlsx/', sample_xlsx, name='sample_xlsx'),
    path("roster_upload",roster_upload, name="roster_upload"),
    path("company_master",cm,name="company_master"),
    path("employee_master",employee_master, name="employee_master"),
    path("upload_excel",upload_excel, name="upload_excel"),
    path("site_master",sm, name="site_master"),
    path("get_access_control",get_access_control, name="get_access_control"),

    #Reports 
    path('common_html', common_html, name='common_html'),
    path('get_filter', get_filter, name='get_filter'),
    path('get_sub_filter', get_sub_filter, name='get_sub_filter'),
    path('add_new_filter', add_new_filter, name='add_new_filter'),
    path('partial_report', partial_report, name='partial_report'),
    path('report_pdf', report_pdf, name='report_pdf'),
    path('report_xlsx', report_xlsx, name='report_xlsx'),
    path('save_filters', save_filters, name='save_filters'),
    path('delete_filters', delete_filters, name='delete_filters'),
    path('saved_filters', saved_filters, name='saved_filters'),
    
    # Menu Management
    path("menu_admin",menu_admin, name="menu_admin"),
    path("menu_master",menu_master, name="menu_master"),
    path("assign_menu",assign_menu, name="assign_menu"),
    path("get_assigned_values",get_assigned_values, name="get_assigned_values"),
    path("menu_order",menu_order, name="menu_order"),
    path("delete_menu",delete_menu, name="delete_menu"),
    
    # Bootstarp Pages
    path("dashboard",dashboard,name='dashboard'),
    path("buttons",buttons,name='buttons'),
    path("cards",cards,name='cards'),
    path("utilities_color",utilities_color,name='utilities_color'),
    path("utilities_border",utilities_border,name='utilities_border'),
    path("utilities_animation",utilities_animation,name='utilities_animation'),
    path("utilities_other",utilities_other,name='utilities_other'),
    path("error_page",error_page,name='error_page'),
    path("blank",blank,name='blank'),
    path("charts",charts,name='charts'),  
    path("tables",tables,name='tables'),
    
    # application master
    
    path('applicationFormIndex', applicationFormIndex, name='applicationFormIndex'),
    path('aple_sarkar/', aple_sarkar, name='aple_sarkar'),
    path('applicationMasterCrate', applicationMasterCrate, name='applicationMasterCrate'), 
    path('application_Master_Post', application_Master_Post, name='application_Master_Post'), 
    path('application_Form_Final_Submit', application_Form_Final_Submit, name='application_Form_Final_Submit'), 
    # path('EditApplicationForm/<int:row_id>/', EditApplicationForm, name='EditApplicationForm'),
    path('EditApplicationForm/<int:row_id>/<int:row_id_status>/', EditApplicationForm, name='EditApplicationForm'),
    path('EditApplicationFormFinalSubmit/<int:row_id>/<int:row_id_status>/', EditApplicationFormFinalSubmit, name='EditApplicationFormFinalSubmit'),
    path('viewapplicationform/<int:row_id>/<int:new_id>/', viewapplicationform, name='viewapplicationform'),
    path('edit_Post_Application_Master/<int:application_id>/<int:row_id_status>/', edit_Post_Application_Master, name='edit_Post_Application_Master'),
    path('edit_Post_Application_Master_final_submit/<int:application_id>/<int:row_id_status>/', edit_Post_Application_Master_final_submit, name='edit_Post_Application_Master_final_submit'),

    # Verification Screen 
    
    path('VerificationForm', VerificationForm, name='VerificationForm'), 
    
    # Internal User Index 
    
    path('InternalUserIndex', InternalUserIndex, name='InternalUserIndex'), 

    # Login With OTP
    
    path('citizenLoginAccount', citizenLoginAccount, name='citizenLoginAccount'), 
    path('citizenRegisterAccount', citizenRegisterAccount, name='citizenRegisterAccount'), 
    path('OTPScreen', OTPScreen, name='OTPScreen'), 
    path('checkmobilenumber', checkmobilenumber, name='checkmobilenumber'), 
    path('verify_otp', verify_otp, name='verify_otp'), 
    path('OTPScreenPost', OTPScreenPost, name='OTPScreenPost'), 
    path('OTPScreenRegistration', OTPScreenRegistration, name='OTPScreenRegistration'), 
    path('download_doc/<str:filepath>/', download_doc, name='download_doc'), 

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)