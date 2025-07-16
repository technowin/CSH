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
from MenuManager.views import *
from DrainageConnection.views import *
from TreeCutting.views import *
from TreeTrimming.views import *
from ContractRegistration.views import *
from ProductApproval.views import *
from Masters.views import site_master as sm
from Masters.views import company_master as cm
from django.urls import path


urlpatterns = [
    path('admin/', admin.site.urls),
    # APP URLS

    # Account
    path("", citizenLoginAccount,name='citizenLogin'),
    path('citizenLogin', citizenLoginAccount, name='citizenLogin'), 
    path('api/citizen', citizen_api, name='citizen_api'), 

    # path("", onetimepage,name='onetimepage'),
    # path("", Login,name='Account'),
    path("Login", Login,name='Account'),
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

    path("onetimepage",onetimepage, name="onetimepage"),
    
    # Dashboard
    path("newdashboard",newdashboard,name='newdashboard'),
    path("get_sites",get_sites,name='get_sites'),
    path("updateGraph",updateGraph, name="updateGraph"),
    path("get_roster_data",get_roster_data, name="get_roster_data"),
    path("get_roster_data_tommorow",get_roster_data_tommorow, name="get_roster_data_tommorow"),

    # Masters
    path('masters/', masters, name='masters'),
    path('sample_xlsx/', sample_xlsx, name='sample_xlsx'),
    path("roster_upload",roster_upload, name="roster_upload"),
    path("company_master",cm,name="company_master"),
    path("employee_master",employee_master, name="employee_master"),
    path("upload_excel",upload_excel, name="upload_excel"),
    path("site_master",sm, name="site_master"),
    path("get_access_control",get_access_control, name="get_access_control"),
    path("documentMaster",documentMaster, name="documentMaster"),
    path("Edit_Document_master",Edit_Document_master, name="Edit_Document_master"),
    path("Create_Document_Master",Create_Document_Master, name="Create_Document_Master"),

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
    
    # Drainage Connection Workflow
    path('index/', index, name='index'),
    path('matrix_flow', matrix_flow, name='matrix_flow'),

    # Drainage Connection application 
    
    path('applicationFormIndex', applicationFormIndex, name='applicationFormIndex'),
    # path('aple_sarkar/', aple_sarkar, name='aple_sarkar'),
    path('aple_sarkar_Register', aple_sarkar_Register, name='aple_sarkar_Register'),
    path('aple_sarkar_Login', aple_sarkar_Login, name='aple_sarkar_Login'),
    path('applicationMasterCrate', applicationMasterCrate, name='applicationMasterCrate'), 
    path('application_Master_Post', application_Master_Post, name='application_Master_Post'), 
    path('application_Form_Final_Submit', application_Form_Final_Submit, name='application_Form_Final_Submit'), 
    path('EditApplicationForm/<str:row_id>/<str:row_id_status>/', EditApplicationForm, name='EditApplicationForm'),
    path('EditApplicationFormFinalSubmit/<str:row_id>/<str:row_id_status>/', EditApplicationFormFinalSubmit, name='EditApplicationFormFinalSubmit'),
    path('viewapplicationform/<str:row_id>/<str:new_id>/', viewapplicationform, name='viewapplicationform'),
    path('edit_Post_Application_Master/<int:application_id>/<int:row_id_status>/', edit_Post_Application_Master, name='edit_Post_Application_Master'),
    path('edit_Post_Application_Master_final_submit/<int:application_id>/<int:row_id_status>/', edit_Post_Application_Master_final_submit, name='edit_Post_Application_Master_final_submit'),
    
    # path('EditApplicationFormFinalSubmit/<int:row_id>/<int:row_id_status>/', EditApplicationFormFinalSubmit, name='EditApplicationFormFinalSubmit'),
    # path('viewapplicationform/<int:row_id>/<int:new_id>/', viewapplicationform, name='viewapplicationform'),
    # path('EditApplicationForm/<int:row_id>/<int:row_id_status>/', EditApplicationForm, name='EditApplicationForm'),
    
    # Tree Cutting Workflow

    path('index_tc/', index_tc, name='index_tc'),
    path('matrix_flow_tc', matrix_flow_tc, name='matrix_flow_tc'),

    # Tree Cutting application
    
    path('applicationFormIndexTC', applicationFormIndexTC, name='applicationFormIndexTC'),
    path('application_Master_Crate_TC', application_Master_Crate_TC, name='application_Master_Crate_TC'),
    path('application_Master_Edit_TC/<str:row_id>/<str:new_id>/', application_Master_Edit_TC, name='application_Master_Edit_TC'),
    path('application_Master_View_TC/<str:row_id>/<str:new_id>/', application_Master_View_TC, name='application_Master_View_TC'),

    # Tree Trimming Workflow
    
    path('index_tt/', index_tt, name='index_tt'),
    path('matrix_flow_tt', matrix_flow_tt, name='matrix_flow_tt'),
    
    # Tree Trimming application
    
    path('applicationFormIndexTT', applicationFormIndexTT, name='applicationFormIndexTT'),
    path('application_Master_Crate_TT', application_Master_Crate_TT, name='application_Master_Crate_TT'),
    path('application_Master_Edit_TT/<str:row_id>/<str:new_id>/', application_Master_Edit_TT, name='application_Master_Edit_TT'),
    path('application_Master_View_TT/<str:row_id>/<str:new_id>/', application_Master_View_TT, name='application_Master_View_TT'),
    
    # Contract Registration
    
    path('index_cr/', index_cr, name='index_cr'),
    path('matrix_flow_cr', matrix_flow_cr, name='matrix_flow_cr'),
    path('citizen_index_cr', citizen_index_cr, name='citizen_index_cr'),
    path('citizen_crate_cr', citizen_crate_cr, name='citizen_crate_cr'),
    path('citizen_edit_cr/<str:row_id>/<str:new_id>/', citizen_edit_cr, name='citizen_edit_cr'),
    path('citizen_delete_cr/<str:row_id>/<str:new_id>/', citizen_delete_cr, name='citizen_delete_cr'),
    path('citizen_view_cr/<str:row_id>/<str:new_id>/', citizen_view_cr, name='citizen_view_cr'),
    path('create_partial_view', create_partial_view, name='create_partial_view'),
    
    # Product Approval
    
    path('index_pa/', index_pa, name='index_pa'),
    path('matrix_flow_pa', matrix_flow_pa, name='matrix_flow_pa'),
    path('citizen_index_pa', citizen_index_pa, name='citizen_index_pa'),
    path('citizen_crate_pa', citizen_crate_pa, name='citizen_crate_pa'),
    path('citizen_edit_pa/<str:row_id>/<str:new_id>/', citizen_edit_pa, name='citizen_edit_pa'),
    path('citizen_view_pa/<str:row_id>/<str:new_id>/', citizen_view_pa, name='citizen_view_pa'),
    path('create_partial_view_product', create_partial_view_product, name='create_partial_view_product'),
    
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
    path('downloadIssuedCertificate/<str:row_id>/', downloadIssuedCertificate, name='downloadIssuedCertificate'), 
    path('downloadIssuedCertificatetc/<str:row_id>/', downloadIssuedCertificatetc, name='downloadIssuedCertificatetc'), 
    path('downloadIssuedCertificatett/<str:row_id>/', downloadIssuedCertificatett, name='downloadIssuedCertificatett'), 
    
    path('downloadRefusalDocument/<str:row_id>/', downloadRefusalDocument, name='downloadRefusalDocument'), 
    path('downloadRefusalDocumenttt/<str:row_id>/', downloadRefusalDocumenttt, name='downloadRefusalDocumenttt'), 
    path('downloadRefusalDocumenttc/<str:row_id>/', downloadRefusalDocumenttc, name='downloadRefusalDocumenttc'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)