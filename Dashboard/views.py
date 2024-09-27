from django.shortcuts import render
from django.contrib import messages
from Account.serializers import *
import Db 
from django.contrib.auth.decorators import login_required
from CSH.encryption import *
import traceback
from django.http import JsonResponse
import traceback

@login_required
def newdashboard(request):
    Db.closeConnection()
    m = Db.get_connection()
    cursor = m.cursor()
    
    try:
        user_id = request.session.get('user_id', '')
        cursor.callproc("stp_get_roster_count",[user_id])
        for result in cursor.stored_results():
            roster_count = result.fetchone() 

        user_id = request.session.get('user_id', '')
        cursor.callproc("stp_get_today_roster_graph",[user_id])

        for result in cursor.stored_results():
            today_result = result.fetchone() 

        cursor.callproc("stp_get_tommorow_roster_graph",[user_id])

        for result in cursor.stored_results():
            tommorow_result = result.fetchone() 

        
        user_id = request.session.get('user_id', '')
        cursor.callproc("stp_get_graph_dropdown", [user_id,'company'])
        for result in cursor.stored_results():
            company_names = list(result.fetchall())

        cursor.callproc("stp_get_graph_dropdown", [user_id,'site'])
        for result in cursor.stored_results():
            site_names = list(result.fetchall())

        cursor.callproc("stp_get_worksite_percent_count_pie", ['1'])
        fetched_results = []
    
        for result in cursor.stored_results():
            fetched_results = result.fetchall()

        cursor.callproc("stp_get_worksite_percent_count_pie2", ['1'])
        
        results = []
        for result in cursor.stored_results():
            results = result.fetchall()

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
        cursor.callproc("stp_error_log", [fun, str(e), request.user.id])
        print(f"error: {e}")
        messages.error(request, 'Oops...! Something went wrong!')
        response = {'result': 'fail', 'messages': 'something went wrong !'}

    finally:
        cursor.close()
        m.commit()
        m.close()
        Db.closeConnection()
    
    # Render the dashboard template with the context data
    if request.method == "GET":
        return render(request, 'Dashboard/index.html', context)


@login_required
def get_sites(request):
    Db.closeConnection()
    m = Db.get_connection()
    cursor = m.cursor()
    
    try:
        user_id = request.session.get('user_id', '')
        selectedCompany = request.POST.get('selectedCompany','')
        cursor.callproc("stp_get_company_wise_site_names", [user_id,selectedCompany])
        for result in cursor.stored_results():
            companywise_site_names = list(result.fetchall())

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        cursor.callproc("stp_error_log", [fun, str(e), request.user.id])
        print(f"error: {e}")
        return JsonResponse({'result': 'fail', 'message': 'something went wrong!'}, status=500)
    
    finally:
        cursor.close()
        m.commit()
        m.close()
        Db.closeConnection()
    
    return JsonResponse({'companywise_site_names': companywise_site_names}, status=200)


@login_required
def updateGraph(request):
    Db.closeConnection()
    m = Db.get_connection()
    cursor = m.cursor()
    
    try:
        company_id = request.POST.get('company_id', '')
        site_name = request.POST.get('site_name', '')
        shift_date = request.POST.get('shift_date', '')


        cursor.callproc("stp_get_today_roster_graph_filter", [company_id, site_name, shift_date])
        
        for result in cursor.stored_results():
            fetched_result = result.fetchone() 
            if fetched_result:
                result_data = {
                    'total_count': fetched_result[0],
                    'yes_count': fetched_result[1],
                    'no_count': fetched_result[2],
                    'pending_count': fetched_result[3],
                    'more_than_8_hours_count': fetched_result[4],
                    'less_than_8_hours_count': fetched_result[5]
                }

        cursor.callproc("stp_get_tommorow_roster_graph_filter", [company_id, site_name, shift_date])
        
        for result in cursor.stored_results():
            fetched_result = result.fetchone() 
            if fetched_result:
                result_data_tommorow = {
                    'nxttotal_count': fetched_result[0],
                    'nxtyes_count': fetched_result[1],
                    'nxtno_count': fetched_result[2],
                    'nxtpending_count': fetched_result[3],
                    'nxtmore_than_8_hours_count': fetched_result[4],
                    'nxtless_than_8_hours_count': fetched_result[5]
                }

        cursor.callproc("stp_get_worksite_percent_count_pie_filter", [company_id,shift_date])
        fetched_results = []
    
        for result in cursor.stored_results():
            fetched_results = result.fetchall()

        cursor.callproc("stp_get_worksite_percent_count_filter2",[company_id,shift_date])
        
        results = []
        for result in cursor.stored_results():
            results = result.fetchall() or []

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
        cursor.callproc("stp_error_log", [fun, str(e), request.user.id])
        print(f"error: {e}")
        return JsonResponse({'result': 'fail', 'message': 'something went wrong!'}, status=500)
    
@login_required
def get_roster_data(request):
    Db.closeConnection()
    m = Db.get_connection()
    cursor = m.cursor()

    try:

        company_id = request.GET.get('company_id', '')
        site_name = request.GET.get('site_name', '')
        shift_date = request.GET.get('shift_date', '')
        clickedCategory = request.GET.get('clickedCategory', '')

        cursor.callproc("stp_get_roster_count_data",[shift_date,company_id,site_name,clickedCategory])
        
        data = []
        for result in cursor.stored_results():
            data = result.fetchall()

        return JsonResponse({'data': data})

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        cursor.callproc("stp_error_log", [fun, str(e), request.user.id])
        print(f"error: {e}")
        return JsonResponse({'result': 'fail', 'message': 'something went wrong!'}, status=500)
    
    finally:
        cursor.close()
        m.commit()
        m.close()
        Db.closeConnection()
    
@login_required
def get_roster_data_tommorow(request):
    Db.closeConnection()
    m = Db.get_connection()
    cursor = m.cursor()

    try:
        company_id = request.GET.get('company_id', '')
        worksite = request.GET.get('site_name', '')
        shift_date = request.GET.get('shift_date', '')
        clickedCategory = request.GET.get('clickedCategory', '')

        cursor.callproc("stp_get_roster_count_tommorow_data", [shift_date, company_id, worksite, clickedCategory])

        data1 = []
        for result in cursor.stored_results():
            data1 = result.fetchall()

        return JsonResponse({'data': data1})

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        cursor.callproc("stp_error_log", [fun, str(e), request.user.id])
        print(f"Error: {e}")
        return JsonResponse({'result': 'fail', 'message': 'Something went wrong!'}, status=500)

    finally:
        cursor.close()
        m.commit()
        m.close()
        Db.closeConnection()
    
    
