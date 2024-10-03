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

    
