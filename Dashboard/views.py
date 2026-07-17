from django.shortcuts import render
from django.contrib import messages
from Account.serializers import *
import Db 
from django.contrib.auth.decorators import login_required
from CSH.encryption import *
import traceback
from django.http import JsonResponse
import traceback
from Account.db_utils import callproc
from django.utils import timezone
from CSH.access_control import no_direct_access

@login_required
def newdashboard(request):
    try:
        user_id = request.session.get('user_id', '')
        roster_count = callproc("stp_get_roster_count",[user_id])
        roster_count = roster_count[0] if roster_count else None

        user_id = request.session.get('user_id', '')
        today_result = callproc("stp_get_today_roster_graph",[user_id])
        today_result = today_result[0] if today_result else None
        tommorow_result = callproc("stp_get_tommorow_roster_graph",[user_id])
        tommorow_result = tommorow_result[0] if tommorow_result else None

        user_id = request.session.get('user_id', '')
        company_names = callproc("stp_get_graph_dropdown", [user_id,'company'])
        
        site_names = callproc("stp_get_graph_dropdown", [user_id,'site'])
        fetched_results = []
        fetched_results = callproc("stp_get_worksite_percent_count_pie", ['1'])

        results = []
        results = callproc("stp_get_worksite_percent_count_pie2", ['1'])
        
        # # Structure data into a more manageable format
        formatted_results = [
            {
                "worksite_name": row[0],  # Assuming the first column is worksite_name
                "percent": row[1],        # Assuming the second column is percent
                "yes_count": row[2],      # Assuming the third column is yes_count
                "no_count": row[3],       # Assuming the fourth column is no_count
                "pending_count": row[4]   # Assuming the fifth column is pending_count
            }
            for row in results
        ]
       

        # Context data to pass to the template
        context = {
            'today_result':today_result,
            'tommorow_result':tommorow_result,
            'roster_count':roster_count,
            'company_names': company_names,
            'site_names': site_names,
            'fetched_results':fetched_results,
            'results': formatted_results,
        }
    
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), request.user.id])
        print(f"error: {e}")
        messages.error(request, 'Oops...! Something went wrong!')
        response = {'result': 'fail', 'messages': 'something went wrong !'}

    finally:
        if request.method == "GET":
            return render(request, 'Dashboard/index.html', context)

@login_required
def get_sites(request):
    try:
        user_id = request.session.get('user_id', '')
        selectedCompany = request.POST.get('selectedCompany','')
        companywise_site_names = callproc("stp_get_company_wise_site_names", [user_id,selectedCompany])
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), request.user.id])
        print(f"error: {e}")
        return JsonResponse({'result': 'fail', 'message': 'something went wrong!'}, status=500)
    finally:
        return JsonResponse({'companywise_site_names': companywise_site_names}, status=200)

@login_required
def updateGraph(request):
    try:
        company_id = request.POST.get('company_id', '')
        site_name = request.POST.get('site_name', '')
        shift_date = request.POST.get('shift_date', '')

        fetched_result = callproc("stp_get_today_roster_graph_filter", [company_id, site_name, shift_date])
        fetched_result = fetched_result[0] if fetched_result else None
        if fetched_result:
            result_data = {
                'total_count': fetched_result[0],
                'yes_count': fetched_result[1],
                'no_count': fetched_result[2],
                'pending_count': fetched_result[3],
                'more_than_8_hours_count': fetched_result[4],
                'less_than_8_hours_count': fetched_result[5]
            }

        fetched_result= callproc("stp_get_tommorow_roster_graph_filter", [company_id, site_name, shift_date])
        fetched_result = fetched_result[0] if fetched_result else None
        if fetched_result:
            result_data_tommorow = {
                'nxttotal_count': fetched_result[0],
                'nxtyes_count': fetched_result[1],
                'nxtno_count': fetched_result[2],
                'nxtpending_count': fetched_result[3],
                'nxtmore_than_8_hours_count': fetched_result[4],
                'nxtless_than_8_hours_count': fetched_result[5]
            }
        fetched_results = []
        fetched_results = callproc("stp_get_worksite_percent_count_pie_filter", [company_id,shift_date])
        
        results = []
        results = callproc("stp_get_worksite_percent_count_filter2",[company_id,shift_date])

        formatted_results = [
            {
                "worksite_name": row[0] if row else "",  
                "percent": row[1] if row else 0,        
                "yes_count": row[2] if row else 0,     
                "no_count": row[3] if row else 0,       
                "pending_count": row[4] if row else 0  
            }
            for row in results
        ] if results else [
            {
                "worksite_name": "",  
                "percent": 0,        
                "yes_count": 0,     
                "no_count": 0,       
                "pending_count": 0  
            }
        ]

        return JsonResponse({'shift_date':shift_date,'data': result_data,'data1':result_data_tommorow,'data3':fetched_results,'data2':formatted_results})

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), request.user.id])
        print(f"error: {e}")
        return JsonResponse({'result': 'fail', 'message': 'something went wrong!'}, status=500)
    
@login_required
def get_roster_data(request):
    try:
        company_id = request.GET.get('company_id', '')
        site_name = request.GET.get('site_name', '')
        shift_date = request.GET.get('shift_date', '')
        clickedCategory = request.GET.get('clickedCategory', '')
        data = []
        data = callproc("stp_get_roster_count_data",[shift_date,company_id,site_name,clickedCategory])
        return JsonResponse({'data': data})

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), request.user.id])
        print(f"error: {e}")
        return JsonResponse({'result': 'fail', 'message': 'something went wrong!'}, status=500)
    
@login_required
def get_roster_data_tommorow(request):
    try:
        company_id = request.GET.get('company_id', '')
        worksite = request.GET.get('site_name', '')
        shift_date = request.GET.get('shift_date', '')
        clickedCategory = request.GET.get('clickedCategory', '')
        data1 = []
        data1 = callproc("stp_get_roster_count_tommorow_data", [shift_date, company_id, worksite, clickedCategory])
        return JsonResponse({'data': data1})

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), request.user.id])
        print(f"Error: {e}")
        return JsonResponse({'result': 'fail', 'message': 'Something went wrong!'}, status=500)


# Dashboard common

import json
import traceback
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.db import connections
from django.utils import timezone
from datetime import datetime, timedelta
from django.apps import apps
from django.contrib.auth.decorators import login_required
from django.contrib import messages

# ========== HELPER FUNCTIONS ==========

def get_service_master():
    """Get all services from service_master table"""
    try:
        from Account.models import service_master
        services = service_master.objects.using('default').all().values('ser_id', 'ser_name', 'short_name')
        return list(services)
    except Exception as e:
        print(f"Error fetching service master: {e}")
        return []

def get_service_db_name(service_id):
    """Get database name for the service - ONLY for services that have databases"""
    db_mapping = {
        '1': '1',
        '2': '2',
        '3': '3',
        '4': '4',
        '5': '5'
    }
    return db_mapping.get(str(service_id), None)  # Return None instead of 'default'

def get_model_for_service(service_id, model_name):
    """Dynamically get the model class for the given service and model name"""
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
            return apps.get_model('Masters', 'status_master')
        except LookupError:
            try:
                return apps.get_model('Masters', 'StatusMaster')
            except LookupError:
                return None
    
    # For other models, get from service app
    app_label = service_to_app.get(str(service_id))
    if not app_label:
        return None
    
    try:
        return apps.get_model(app_label, model_name)
    except LookupError:
        try:
            model_class_name = ''.join(word.capitalize() for word in model_name.split('_'))
            return apps.get_model(app_label, model_class_name)
        except LookupError:
            return None

def get_user_names(user_ids):
    """Fetch user names from Account app"""
    try:
        CustomUser = apps.get_model('Account', 'CustomUser')
        user_names = {}
        if CustomUser and user_ids:
            users = CustomUser.objects.using('default').filter(id__in=user_ids)
            for user in users:
                user_names[user.id] = user.full_name if user.full_name else user.phone
        return user_names
    except Exception as e:
        print(f"Error fetching users: {e}")
        return {}

def get_active_services():
    """Get ONLY services that have databases (1-5)"""
    all_services = get_service_master()
    
    # Only these service IDs have actual databases
    active_service_ids = ['1', '2', '3', '4', '5']
    
    active_services = []
    for service in all_services:
        ser_id = str(service['ser_id'])
        if ser_id in active_service_ids:
            active_services.append(service)
        else:
            print(f"⏭️ Skipping service {service['ser_name']} (ID: {ser_id}) - No database connection")
    
    print(f"Active services with databases: {[s['ser_name'] for s in active_services]}")
    return active_services

def get_service_name(service_id):
    """Get friendly service name from service_id"""
    service_names = {
        '1': 'Drainage Connection',
        '2': 'Tree Cutting',
        '3': 'Tree Trimming',
        '4': 'Contract Registration',
        '5': 'Product Approval'
    }
    return service_names.get(str(service_id), 'Unknown Service')

# ========== MAIN DASHBOARD VIEW ==========

@no_direct_access
@login_required
def dashboard(request):
    try:
        user_id = request.session.get('user_id', '')
        role_id = request.session.get('role_id', '')
        
        # Get filter parameters
        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')
        service_filter = request.GET.get('service', 'all')
        
        print(f"\n{'='*60}")
        print(f"=== SUPER ADMIN DASHBOARD ===")
        print(f"User ID: {user_id}")
        print(f"From Date: {from_date}")
        print(f"To Date: {to_date}")
        print(f"Service Filter: {service_filter}")
        print(f"{'='*60}\n")
        
        # ========== GET ACTIVE SERVICES (ONLY 1-5) ==========
        services = get_active_services()
        print(f"Active services: {[s['ser_name'] for s in services]}")
        
        # If specific service selected, filter
        if service_filter and service_filter != 'all':
            services = [s for s in services if str(s['ser_id']) == str(service_filter)]
            print(f"Filtered to: {[s['ser_name'] for s in services]}")
        
        # ========== INITIALIZE COUNTS ==========
        total_applications = 0
        approved_count = 0
        pending_count = 0
        rejected_count = 0
        status_distribution = {}
        status_colors = {}
        service_stats = {}
        
        # ========== COLLECT ALL APPLICATIONS DATA ==========
        applications_data = []  # <-- This is where we store all applications
        
        # Status categories for matching
        status_categories = {
            'approved': ['approved', 'approve', 'approval', 'issued', 'issue', 'certificate', 'certified', 'final', 'completed'],
            'pending': ['pending', 'pend', 'process', 'progress', 'forward', 'submitted', 'initiated', 'new', 'acknowledged', 'scrutiny', 'inspection', 'chalan', 'payment', 'permission'],
            'rejected': ['rejected', 'reject', 'refused', 'refuse', 'failed', 'cancelled', 'cancel']
        }
        
        # ========== PROCESS EACH SERVICE ==========
        for service in services:
            ser_id = str(service['ser_id'])
            ser_name = service['ser_name']
            short_name = service['short_name']
            
            print(f"\n--- Processing: {ser_name} (ID: {ser_id}) ---")
            
            # Skip services without databases
            if ser_id not in ['1', '2', '3', '4', '5']:
                print(f"  ⏭️ Skipping {ser_name} - No database connection")
                service_stats[ser_name] = {
                    'total': 0, 'approved': 0, 'pending': 0, 'rejected': 0, 'short_name': short_name
                }
                continue
            
            db_alias = get_service_db_name(ser_id)
            
            if db_alias is None or db_alias not in connections:
                print(f"  ❌ Database '{db_alias}' not found!")
                service_stats[ser_name] = {
                    'total': 0, 'approved': 0, 'pending': 0, 'rejected': 0, 'short_name': short_name
                }
                continue
            
            print(f"  ✅ DB Alias: {db_alias}")
            
            try:
                ApplicationForm = get_model_for_service(ser_id, 'application_form')
                StatusMaster = get_model_for_service(ser_id, 'status_master')
                
                if not ApplicationForm:
                    print(f"  ❌ ApplicationForm model not found")
                    service_stats[ser_name] = {
                        'total': 0, 'approved': 0, 'pending': 0, 'rejected': 0, 'short_name': short_name
                    }
                    continue
                
                print(f"  ✅ ApplicationForm model found")
                
                # ========== LOAD STATUSES FROM SERVICE DATABASE ==========
                status_map = {}
                if StatusMaster:
                    try:
                        all_statuses = StatusMaster.objects.using(db_alias).all()
                        status_map = {status.status_id: status for status in all_statuses}
                        print(f"  ✅ Loaded {len(status_map)} statuses from service database ({db_alias})")
                    except Exception as e:
                        print(f"  ❌ Error loading statuses: {e}")
                        status_map = {}
                else:
                    print(f"  ❌ StatusMaster model not found for service {ser_name}")
                    status_map = {}
                
                # Get applications
                applications = ApplicationForm.objects.using(db_alias).all()
                
                # Apply date filters
                if from_date:
                    try:
                        from_date_obj = datetime.strptime(from_date, '%Y-%m-%d')
                        applications = applications.filter(created_at__gte=from_date_obj)
                        print(f"  Applied from_date: {from_date}")
                    except ValueError:
                        pass
                
                if to_date:
                    try:
                        to_date_obj = datetime.strptime(to_date, '%Y-%m-%d')
                        to_date_obj = to_date_obj + timedelta(days=1)
                        applications = applications.filter(created_at__lt=to_date_obj)
                        print(f"  Applied to_date: {to_date}")
                    except ValueError:
                        pass
                
                count = applications.count()
                print(f"  Total applications: {count}")
                total_applications += count
                
                # ========== COUNT STATUSES AND BUILD APPLICATIONS_DATA ==========
                approved = 0
                pending = 0
                rejected = 0
                
                for app in applications:
                    # Get user names
                    created_by_name = '-'
                    if app.created_by:
                        try:
                            # Try to get user name if stored as ID
                            from Account.models import CustomUser
                            user = CustomUser.objects.using('default').filter(id=app.created_by).first()
                            if user:
                                created_by_name = user.full_name if user.full_name else user.phone
                            else:
                                created_by_name = str(app.created_by)
                        except:
                            created_by_name = str(app.created_by)
                    
                    # Get status
                    status_name = 'No Status'
                    status_color = '#95a5a6'
                    status_id = None
                    
                    try:
                        if app.status_id and app.status_id in status_map:
                            status_obj = status_map[app.status_id]
                            status_name = status_obj.status_name
                            status_color = status_obj.status_color or '#6c757d'
                            status_id = app.status_id
                    except Exception as e:
                        print(f"  ⚠️ Error getting status for app {app.id}: {e}")
                    
                    # Add to applications_data
                    applications_data.append({
                        'id': app.id,
                        'request_no': app.request_no or '-',
                        'service_id': ser_id,
                        'service_name': ser_name,
                        'short_name': short_name,
                        'status': status_name,
                        'status_color': status_color,
                        'created_at': app.created_at,
                        'created_by': created_by_name,
                        'db_alias': db_alias,
                    })
                    
                    # Count for pie chart
                    status_distribution[status_name] = status_distribution.get(status_name, 0) + 1
                    
                    # Store color
                    if status_color and status_color != '#95a5a6':
                        status_colors[status_name] = status_color
                    elif 'approved' in status_name.lower():
                        status_colors[status_name] = '#2ECC71'
                    elif 'pending' in status_name.lower():
                        status_colors[status_name] = '#F39C12'
                    elif 'rejected' in status_name.lower():
                        status_colors[status_name] = '#E74C3C'
                    else:
                        status_colors[status_name] = '#6c757d'
                    
                    # Count for stats cards
                    status_lower = status_name.lower()
                    if any(word in status_lower for word in status_categories['approved']):
                        approved += 1
                        approved_count += 1
                    elif any(word in status_lower for word in status_categories['rejected']):
                        rejected += 1
                        rejected_count += 1
                    elif any(word in status_lower for word in status_categories['pending']):
                        pending += 1
                        pending_count += 1
                
                service_stats[ser_name] = {
                    'total': count,
                    'approved': approved,
                    'pending': pending,
                    'rejected': rejected,
                    'short_name': short_name
                }
                
                print(f"  ✅ Done: Total={count}, Approved={approved}, Pending={pending}, Rejected={rejected}")
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
                import traceback
                traceback.print_exc()
                service_stats[ser_name] = {
                    'total': 0, 'approved': 0, 'pending': 0, 'rejected': 0, 'short_name': short_name
                }
                continue
        
        # Sort applications by created_at descending
        applications_data.sort(key=lambda x: x['created_at'] if x['created_at'] else datetime.min, reverse=True)
        
        print(f"\n{'='*60}")
        print(f"=== FINAL COUNTS ===")
        print(f"Total: {total_applications}")
        print(f"Approved: {approved_count}")
        print(f"Pending: {pending_count}")
        print(f"Rejected: {rejected_count}")
        print(f"Total applications_data: {len(applications_data)}")
        print(f"{'='*60}\n")
        
        # ========== TABLE DATA ==========
        table_data = []
        for app in applications_data:  # Limit to 100 for performance
            table_data.append({
                'id': app['id'],
                'request_no': app['request_no'],
                'service_id': app['service_id'],
                'short_name': app['short_name'],
                'status': app['status'],
                'status_color': app['status_color'],
                'created_at': app['created_at'].strftime('%Y-%m-%d %H:%M') if app['created_at'] else '-',
                'created_by': app['created_by'],
                'db_alias': app['db_alias'],
            })
        
        # ========== GET SERVICES FOR FILTER ==========
        services_for_filter = get_active_services()
        username = request.session.get('username', 'Admin')
        
        # ========== SERVICE-WISE DISTRIBUTION DATA ==========
        service_labels = []
        service_values = []
        service_colors = []
        service_ids = []

        service_color_map = {
            'Drainage Connection': '#3498db',
            'Tree Cutting': '#2ecc71',
            'Tree Trimming': '#f39c12',
            'Contract Registration': '#9b59b6',
            'Product Approval': '#e74c3c'
        }

        service_id_map = {
            'Drainage Connection': '1',
            'Tree Cutting': '2',
            'Tree Trimming': '3',
            'Contract Registration': '4',
            'Product Approval': '5'
        }

        for name, stats in service_stats.items():
            service_labels.append(name)
            service_values.append(stats['total'])
            service_colors.append(service_color_map.get(name, '#6c757d'))
            service_ids.append(service_id_map.get(name, ''))
            
        # ========== MONTHLY TREND DATA ==========
        monthly_data = []
        today = timezone.now()

        # Get last 12 months
        for i in range(11, -1, -1):
            month_start = today.replace(day=1) - timedelta(days=30*i)
            month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            
            month_count = 0
            for app in applications_data:
                if app['created_at']:
                    # Check if app created_at is in this month
                    if app['created_at'] >= month_start and app['created_at'] <= month_end + timedelta(days=1):
                        month_count += 1
            
            monthly_data.append({
                'month': month_start.strftime('%b %Y'),
                'count': month_count
            })

        print(f"Monthly trend data: {monthly_data}")
        
        context = {
            'user_id': user_id,
            'role_id': role_id,
            'username': username,
            'total_applications': total_applications,
            'approved_count': approved_count,
            'pending_count': pending_count,
            'rejected_count': rejected_count,
            'services': services_for_filter,
            'service_stats': service_stats,
            'selected_service': service_filter,
            'from_date': from_date if from_date else '',
            'to_date': to_date if to_date else '',
            'status_distribution': json.dumps({
                'labels': list(status_distribution.keys()),
                'values': list(status_distribution.values()),
                'colors': [status_colors.get(label, '#6c757d') for label in status_distribution.keys()]
            }),
            'service_distribution': json.dumps({
                'labels': service_labels,
                'values': service_values,
                'colors': service_colors,
                'service_ids': service_ids
            }),
            'table_data': table_data,
            'monthly_data': json.dumps(monthly_data),
        }
        
        return render(request, 'Dashboard/index.html', context)
        
    except Exception as e:
        print(f"Error in dashboard: {str(e)}")
        print(traceback.format_exc())
        messages.error(request, 'Oops...! Something went wrong!')
        return render(request, 'Dashboard/index.html', {'error': str(e)})
    
# ========== GET APPLICATION DETAIL FOR MODAL ==========
def common_get_application_detail(request):
    """
    API to get detailed application data for modal popup
    """
    try:
        service_id = request.GET.get('service_id')
        db_alias = request.GET.get('db_alias')
        app_id = request.GET.get('app_id')
        
        print(f"=== common_get_application_detail ===")
        print(f"Service ID: {service_id}")
        print(f"DB Alias: {db_alias}")
        print(f"App ID: {app_id}")
        
        if not service_id or not db_alias or not app_id:
            return JsonResponse({'error': 'Missing required parameters'}, status=400)
        
        ApplicationForm = get_model_for_service(service_id, 'application_form')
        WorkflowHistory = get_model_for_service(service_id, 'workflow_history')
        StatusMaster = get_model_for_service(service_id, 'status_master')
        
        if not ApplicationForm:
            return JsonResponse({'error': 'ApplicationForm model not found'}, status=404)
        
        try:
            application = ApplicationForm.objects.using(db_alias).get(id=app_id)
        except ApplicationForm.DoesNotExist:
            return JsonResponse({'error': 'Application not found'}, status=404)
        
        # Get user IDs from application
        user_ids = set()
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
        
        # Get user names from Account app
        user_names = {}
        try:
            from Account.models import CustomUser
            if user_ids:
                users = CustomUser.objects.using('default').filter(id__in=user_ids)
                for user in users:
                    user_names[user.id] = user.full_name if user.full_name else user.phone
        except Exception as e:
            print(f"Error fetching users: {e}")
        
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
        
        # ========== GET STATUS USING STATUS_ID ==========
        status_name = 'No Status'
        status_color = '#95a5a6'
        
        try:
            if application.status_id:
                if StatusMaster:
                    try:
                        status_obj = StatusMaster.objects.using(db_alias).get(status_id=application.status_id)
                        status_name = status_obj.status_name if status_obj.status_name else 'N/A'
                        status_color = status_obj.status_color if status_obj.status_color else '#6c757d'
                        print(f"  ✅ Found status: {status_name} (ID: {application.status_id})")
                    except StatusMaster.DoesNotExist:
                        print(f"  ⚠️ Status with ID {application.status_id} not found in service DB")
                        status_name = f'Status ID: {application.status_id}'
                        status_color = '#6c757d'
                else:
                    print(f"  ⚠️ StatusMaster model not available")
                    status_name = f'Status ID: {application.status_id}'
                    status_color = '#6c757d'
        except Exception as e:
            print(f"  ⚠️ Error getting status: {e}")
            status_name = 'Error loading status'
            status_color = '#e74c3c'
        
        app_data['status'] = status_name
        app_data['status_color'] = status_color
        app_data['request_no'] = application.request_no if application.request_no else 'N/A'
        
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
        
        # ========== GET WORKFLOW HISTORY - FIXED ==========
        workflow_data = []
        if WorkflowHistory:
            try:
                # Get the queryset first
                history_qs = WorkflowHistory.objects.using(db_alias).filter(
                    form_id=application,
                    request_no__isnull=False
                ).exclude(
                    request_no=''
                ).order_by('-created_at')[:20]
                
                # Debug: Check the raw SQL
                print(f"  📊 SQL: {str(history_qs.query)}")
                
                # Convert to list to see actual records
                history_list = list(history_qs)
                print(f"  📊 Found {len(history_list)} workflow records from database")
                
                # If multiple records, check if they are identical
                if len(history_list) > 1:
                    print(f"  📊 First record ID: {history_list[0].id}")
                    print(f"  📊 Second record ID: {history_list[1].id if len(history_list) > 1 else 'None'}")
                
                # Use a set to track unique record IDs
                seen_ids = set()
                unique_history = []
                
                for record in history_list:
                    if record.id not in seen_ids:
                        seen_ids.add(record.id)
                        unique_history.append(record)
                
                print(f"  📊 Unique records: {len(unique_history)}")
                
                # Limit to 20 unique records
                unique_history = unique_history[:20]
                
                # Get user IDs from workflow
                workflow_user_ids = set()
                for record in unique_history:
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
                
                # Get workflow user names
                workflow_user_names = {}
                try:
                    from Account.models import CustomUser
                    if workflow_user_ids:
                        users = CustomUser.objects.using('default').filter(id__in=workflow_user_ids)
                        for user in users:
                            workflow_user_names[user.id] = user.full_name if user.full_name else user.phone
                except Exception as e:
                    print(f"Error fetching workflow users: {e}")
                
                # Build a status map
                status_map = {}
                if StatusMaster:
                    try:
                        all_statuses = StatusMaster.objects.using(db_alias).all()
                        status_map = {status.status_id: status for status in all_statuses}
                        print(f"  ✅ Loaded {len(status_map)} statuses for workflow")
                    except Exception as e:
                        print(f"  ⚠️ Error loading statuses for workflow: {e}")
                
                # Process unique records
                for record in unique_history:
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
                    
                    # GET WORKFLOW STATUS USING STATUS_ID
                    wf_status_name = 'N/A'
                    try:
                        if record.status_id and record.status_id in status_map:
                            status_obj = status_map[record.status_id]
                            wf_status_name = status_obj.status_name if status_obj.status_name else 'N/A'
                        elif record.status_id:
                            wf_status_name = f'Status ID: {record.status_id}'
                    except Exception as e:
                        print(f"  ⚠️ Error getting workflow status: {e}")
                        wf_status_name = 'Error loading status'
                    
                    workflow_data.append({
                        'level': record.level or '-',
                        'status': wf_status_name,
                        'send_forward': send_forward_name,
                        'pre_user': pre_user_name,
                        'created_at': record.created_at.strftime('%Y-%m-%d %H:%M:%S') if record.created_at else '-',
                        'updated_at': record.updated_at.strftime('%Y-%m-%d %H:%M:%S') if record.updated_at else '-',
                    })
                    
            except Exception as e:
                print(f"Error fetching workflow history: {e}")
                import traceback
                traceback.print_exc()
        
        service_name = get_service_name(service_id)
        
        print(f"  📊 Final workflow_data count: {len(workflow_data)}")
        
        return JsonResponse({
            'application': app_data,
            'workflow_history': workflow_data,
            'service': service_name
        })
        
    except Exception as e:
        import traceback
        print(f"Error in common_get_application_detail: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)
    
# ========== EXPORT TO EXCEL ==========
def common_export_excel(request):
    """
    Export all applications to Excel with proper formatting
    """
    try:
        # Get filter parameters
        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')
        service_filter = request.GET.get('service', 'all')
        
        # Get current user info from session
        generated_by = request.session.get('full_name', request.session.get('username', 'Unknown User'))
        user_id = request.session.get('user_id', 'N/A')
        
        # Get applications data using the same logic as dashboard
        from datetime import datetime
        from django.db import connections
        from django.apps import apps
        import openpyxl
        from openpyxl.utils import get_column_letter
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.styles import numbers
        
        # Get services
        services = get_active_services()
        
        if service_filter and service_filter != 'all':
            services = [s for s in services if str(s['ser_id']) == str(service_filter)]
        
        # Collect all applications data
        all_applications = []
        status_categories = {
            'approved': ['approved', 'approve', 'approval', 'issued', 'issue', 'certificate', 'certified', 'final', 'completed'],
            'pending': ['pending', 'pend', 'process', 'progress', 'forward', 'submitted', 'initiated', 'new', 'acknowledged', 'scrutiny', 'inspection', 'chalan', 'payment', 'permission'],
            'rejected': ['rejected', 'reject', 'refused', 'refuse', 'failed', 'cancelled', 'cancel']
        }
        
        for service in services:
            ser_id = str(service['ser_id'])
            ser_name = service['ser_name']
            short_name = service['short_name']
            
            if ser_id not in ['1', '2', '3', '4', '5']:
                continue
            
            db_alias = get_service_db_name(ser_id)
            if db_alias is None or db_alias not in connections:
                continue
            
            try:
                ApplicationForm = get_model_for_service(ser_id, 'application_form')
                StatusMaster = get_model_for_service(ser_id, 'status_master')
                
                if not ApplicationForm:
                    continue
                
                # Load statuses
                status_map = {}
                if StatusMaster:
                    try:
                        all_statuses = StatusMaster.objects.using(db_alias).all()
                        status_map = {status.status_id: status for status in all_statuses}
                    except:
                        pass
                
                applications = ApplicationForm.objects.using(db_alias).all()
                
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
                
                for app in applications:
                    # Get status
                    status_name = 'No Status'
                    status_color = '#95a5a6'
                    try:
                        if app.status_id and app.status_id in status_map:
                            status_obj = status_map[app.status_id]
                            status_name = status_obj.status_name if status_obj.status_name else 'N/A'
                            status_color = status_obj.status_color if status_obj.status_color else '#6c757d'
                    except:
                        pass
                    
                    # Get created_by name
                    created_by_name = '-'
                    if app.created_by:
                        try:
                            from Account.models import CustomUser
                            user = CustomUser.objects.using('default').filter(id=app.created_by).first()
                            if user:
                                created_by_name = user.full_name if user.full_name else user.phone
                            else:
                                created_by_name = str(app.created_by)
                        except:
                            created_by_name = str(app.created_by)
                    
                    # Get all field data
                    app_data = {
                        'request_no': app.request_no or '-',
                        'service': ser_name,
                        'short_name': short_name,
                        'status': status_name,
                        'created_at': app.created_at.strftime('%Y-%m-%d %H:%M:%S') if app.created_at else '-',
                        'created_by': created_by_name,
                    }
                    
                    # Add service-specific fields
                    for field in ApplicationForm._meta.get_fields():
                        if field.name in ['id', 'status', 'form_user', 'request_no', 'created_at', 'created_by', 'updated_at', 'updated_by']:
                            continue
                        if field.is_relation:
                            continue
                        value = getattr(app, field.name, None)
                        if value is not None:
                            if isinstance(value, datetime):
                                app_data[field.name.replace('_', ' ').title()] = value.strftime('%Y-%m-%d %H:%M:%S')
                            else:
                                app_data[field.name.replace('_', ' ').title()] = str(value)
                    
                    all_applications.append(app_data)
                    
            except Exception as e:
                print(f"Error exporting service {ser_name}: {e}")
                continue
        
        if not all_applications:
            return HttpResponse('No data to export', status=404)
        
        # ========== CREATE EXCEL WORKBOOK ==========
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Applications"
        
        # ========== STYLES ==========
        # Header style
        header_font = Font(bold=True, color="FFFFFF", size=11, name='Segoe UI')
        header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        
        # Border style
        thin_border = Border(
            left=Side(style='thin', color='D0D0D0'),
            right=Side(style='thin', color='D0D0D0'),
            top=Side(style='thin', color='D0D0D0'),
            bottom=Side(style='thin', color='D0D0D0')
        )
        
        # Cell alignment
        cell_alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        header_cell_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        
        # ========== ADD HEADER INFORMATION ==========
        current_row = 1
        
        # Row 1: Title
        ws.merge_cells(f'A{current_row}:Z{current_row}')
        title_cell = ws.cell(row=current_row, column=1)
        
        # Determine title based on filter
        if service_filter and service_filter != 'all':
            service_name = get_service_name(service_filter)
            title = f"{service_name} - Applications Export Report"
        else:
            title = "All Services - Applications Export Report"
        
        title_cell.value = title
        title_cell.font = Font(bold=True, size=16, name='Segoe UI', color="1F4E79")
        title_cell.alignment = Alignment(horizontal="center", vertical="center")
        current_row += 1
        
        # Row 2: Generated By and Date
        ws.merge_cells(f'A{current_row}:Z{current_row}')
        info_cell = ws.cell(row=current_row, column=1)
        current_time = datetime.now().strftime("%d-%b-%Y %I:%M %p")
        info_cell.value = f"Generated By: {generated_by} (ID: {user_id})  |  Generated On: {current_time}"
        info_cell.font = Font(size=10, name='Segoe UI', color="555555")
        info_cell.alignment = Alignment(horizontal="center", vertical="center")
        current_row += 1
        
        # Row 3: Total Records
        ws.merge_cells(f'A{current_row}:Z{current_row}')
        total_cell = ws.cell(row=current_row, column=1)
        total_cell.value = f"Total Records: {len(all_applications)}"
        total_cell.font = Font(bold=True, size=11, name='Segoe UI', color="1F4E79")
        total_cell.alignment = Alignment(horizontal="center", vertical="center")
        current_row += 1
        
        # Row 4: Blank row for separation
        current_row += 1
        
        # ========== GET ALL COLUMNS ==========
        all_columns = set()
        for app in all_applications:
            all_columns.update(app.keys())
        
        # Define column order (priority columns first)
        priority_columns = ['request_no', 'service', 'short_name', 'status', 'created_at', 'created_by']
        other_columns = sorted([col for col in all_columns if col not in priority_columns])
        final_columns = priority_columns + other_columns
        
        # ========== ADD HEADERS ==========
        for col_idx, col_name in enumerate(final_columns, 1):
            cell = ws.cell(row=current_row, column=col_idx)
            cell.value = col_name.replace('_', ' ').title()
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = thin_border
        
        header_row = current_row
        current_row += 1
        
        # ========== ADD DATA ==========
        for row_idx, app_data in enumerate(all_applications, current_row):
            for col_idx, col_name in enumerate(final_columns, 1):
                cell = ws.cell(row=row_idx, column=col_idx)
                
                # Get value
                value = app_data.get(col_name, '-')
                
                # Handle None or empty values
                if value is None or value == '':
                    value = '-'
                
                # Convert to string if not already
                if not isinstance(value, (int, float)):
                    value = str(value)
                
                cell.value = value
                cell.alignment = cell_alignment
                cell.border = thin_border
        
        # ========== AUTO-FIT COLUMN WIDTHS ==========
        for col_idx, col_name in enumerate(final_columns, 1):
            column_letter = get_column_letter(col_idx)
            
            # Calculate max length based on header and data
            max_length = len(col_name)
            for row_idx in range(header_row, min(len(all_applications) + header_row + 1, header_row + 100)):
                cell_value = ws.cell(row=row_idx, column=col_idx).value
                if cell_value:
                    max_length = max(max_length, len(str(cell_value)))
            
            # Set width with some padding (max 50 chars)
            adjusted_width = min(max_length + 5, 50)
            ws.column_dimensions[column_letter].width = max(adjusted_width, 15)
        
        # ========== ADD FILTER ==========
        # ws.auto_filter.ref = ws.dimensions
        
        # ========== FREEZE HEADER ROW ==========
        ws.freeze_panes = f'A{header_row + 1}'
        
        # ========== ADD SERVICE SUMMARY SHEET ==========
        wb.create_sheet("Summary")
        summary_ws = wb["Summary"]
        
        # Summary header
        summary_ws.merge_cells('A1:E1')
        summary_ws.cell(row=1, column=1, value="Service-wise Summary").font = Font(bold=True, size=14, color="1F4E79")
        
        summary_ws.merge_cells('A2:E2')
        summary_ws.cell(row=2, column=1, value=f"Generated By: {generated_by} on {datetime.now().strftime('%d-%b-%Y %I:%M %p')}").font = Font(size=10, color="666666", italic=True)
        
        # Summary headers
        summary_headers = ['Service', 'Total', 'Approved', 'Pending', 'Rejected']
        for col_idx, header in enumerate(summary_headers, 1):
            cell = summary_ws.cell(row=4, column=col_idx)
            cell.value = header
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = thin_border
        
        # Calculate summary data
        service_summary = {}
        for app in all_applications:
            service = app.get('service', 'Unknown')
            status = app.get('status', 'Unknown')
            
            if service not in service_summary:
                service_summary[service] = {'total': 0, 'approved': 0, 'pending': 0, 'rejected': 0}
            
            service_summary[service]['total'] += 1
            
            status_lower = status.lower()
            if 'approved' in status_lower or 'issued' in status_lower or 'certificate' in status_lower:
                service_summary[service]['approved'] += 1
            elif 'pending' in status_lower or 'process' in status_lower or 'forward' in status_lower:
                service_summary[service]['pending'] += 1
            elif 'rejected' in status_lower or 'refused' in status_lower:
                service_summary[service]['rejected'] += 1
        
        # Add summary data
        row_idx = 5
        for service, stats in service_summary.items():
            summary_ws.cell(row=row_idx, column=1, value=service).border = thin_border
            summary_ws.cell(row=row_idx, column=2, value=stats['total']).border = thin_border
            summary_ws.cell(row=row_idx, column=3, value=stats['approved']).border = thin_border
            summary_ws.cell(row=row_idx, column=4, value=stats['pending']).border = thin_border
            summary_ws.cell(row=row_idx, column=5, value=stats['rejected']).border = thin_border
            row_idx += 1
        
        # Auto-fit summary columns
        for col_idx in range(1, 6):
            column_letter = get_column_letter(col_idx)
            summary_ws.column_dimensions[column_letter].width = 20
        
        # ========== CREATE RESPONSE ==========
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if from_date and to_date:
            filename = f'Applications_{from_date}_to_{to_date}_{timestamp}.xlsx'
        elif from_date:
            filename = f'Applications_From_{from_date}_{timestamp}.xlsx'
        elif to_date:
            filename = f'Applications_To_{to_date}_{timestamp}.xlsx'
        else:
            filename = f'All_Applications_{timestamp}.xlsx'
        
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        wb.save(response)
        return response
        
    except Exception as e:
        import traceback
        print(f"Error in common_export_excel: {str(e)}")
        print(traceback.format_exc())
        return HttpResponse(f'Error exporting data: {str(e)}', status=500)

