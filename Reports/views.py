from django.shortcuts import render

# Create your views here.
import string
from django.http import JsonResponse
from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
import requests
from Reports.models import *
import Db 
import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from calendar import monthrange
from mysql.connector.errors import InterfaceError
import calendar
import pandas as pd
import xlwt
from django.http import HttpResponse
import os
import time
import xlsxwriter
import io
import os
# Create your views here.
from django.core.mail import send_mail
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib import messages
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from flask import Flask, render_template
from django.shortcuts import render
app = Flask(__name__)
# Create your views here.

from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import google.generativeai as genai
from rest_framework import serializers
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from django.http import FileResponse
from xhtml2pdf import pisa
from django.template.loader import get_template
import traceback
from Account.db_utils import callproc
from django.utils import timezone
# Report section
@login_required
def common_html(request):
    title,note ='',''
    try:
        if request.user.is_authenticated ==True:                
            global user
            user = request.user.id
            entity =request.GET.get('entity', '')  
            if request.method=="GET":
                filter_name = callproc("stp_get_filter_names",[entity])          
                column_name = callproc("stp_get_column_names",[entity])        
                result = callproc("stp_get_report_title", [entity])
                if result and result[0]:
                    for items in result[0]:
                        title, note = items
                saved_names = callproc("stp_get_saved_filters",[entity,user])        

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),request.user.id])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally:
        return render(request,'Reports/common_reports.html', {'filter_name':filter_name,'column_name':column_name,'saved_names':saved_names,'entity':entity,'title':title,'note':note})
    
@login_required      
def get_filter(request):
    try:
        if request.user.is_authenticated ==True:                
            global user
            user = request.user.id
            if request.method=="GET":
                entity =request.GET.get('entity', '')
                data4 = callproc("stp_get_filter_names",[entity])
                drop_down=[]
                data5 = []
                for items in data4:
                    data5=[]
                    data5=list(items)
                    unit = common_model(id1=data5[0], name=data5[1])
                    drop_down.append(common_dict(unit))
                if len(drop_down) == 0:
                    drop_down = 0
    except Exception  as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),request.user.id])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally:
        return JsonResponse(drop_down, safe=False)
    
class common_model(models.Model):
    name = models.CharField(max_length=255)
    id1 =models.CharField(max_length=255)
    def __str__(self):
        return self.id1    
    
def common_dict(unit):
    return {
        'id1': unit.id1,
        'name': unit.name,
    }  
    
@login_required    
def get_sub_filter(request):
    try:
        if request.user.is_authenticated ==True:                
            global user
            user = request.user.id 
            if request.method=="GET":
                filter_id =request.GET.get('filter_id', '')
                data4 = callproc("stp_get_sub_filter",[filter_id,user])
                drop_down=[]
                data5 = []
                for items in data4:
                    data5=[]
                    data5=list(items)
                    unit = common_model(id1=data5[0], name=data5[1])
                    drop_down.append(common_dict(unit))
                if len(drop_down) == 0:
                    drop_down = 0 
    except Exception  as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),request.user.id])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally:
        return JsonResponse(drop_down, safe=False)  

@login_required
def add_new_filter(request):
    try:
        if request.user.is_authenticated ==True:                
            global user
            user = request.user.id
            if request.method == "GET":
                filter_count =str(request.GET.get('filter_count', ''))
                entity =str(request.GET.get('entity', ''))
                filter_name = callproc("stp_get_filter_names",[entity])                
                fId = filter_count + 'filterId'           
                sfId = filter_count + 'subFilterId'           
                context = {'filter_name':filter_name,'fId':fId,'sfId':sfId,'fcount':filter_count}
                html = render_to_string('Reports/_add_new_filter.html', context)
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),request.user.id])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally:
        data = {'html': html}
        return JsonResponse(data, safe=False)
    
@login_required
def partial_report(request):
    try:
        if request.user.is_authenticated ==True:                
            global user
            user = request.user.id
            if request.method == "GET":
                columnName =str(request.GET.get('columnName', ''))
                filterid =str(request.GET.get('filterid', ''))
                subFilterId =str(request.GET.get('subFilterId', ''))
                sft =str(request.GET.get('sft', ''))
                entity =str(request.GET.get('entity', ''))
                filterid1 = filterid.split(',')
                SubFilterId1 = subFilterId.split(',')
                sft1 = sft.split(',')
                data = common_fun(columnName,filterid1,SubFilterId1,sft1,entity,user)
                headers = data['headers']
                emptycheck = data['emptycheck']
                data_list = data['data_list']
                display_name_list = data['display_name_list']
                # entityName = entity
                context = {'emptycheck':emptycheck,'columns':display_name_list,'rows':data_list,'entity':entity}
                html = render_to_string('Reports/_partial_report.html', context)
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),request.user.id])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally:
        data = {'html': html}
        return JsonResponse(data, safe=False)
    
def common_fun(columnName,filterid,SubFilterId,sft,entity,user):
    try:
        report_filters= []
        report_columns= []
        column_join_list= []
        mandatory_arr= []
        result_data = callproc("stp_get_report_filters", [entity])
        if result_data and result_data[0]:
            for row in result_data[0]:
                report_filters.append(list(row))
        result_data =callproc("stp_get_report_columns", [entity])
        if result_data and result_data[0]:
            for row in result_data[0]:
                report_columns.append(list(row))
        result_data = callproc("stp_get_column_join", [entity])
        if result_data and result_data[0]:
            for row in result_data[0]:
                column_join_list.append(list(row))
        result_data = callproc("stp_get_mandatory", [entity])
        mandf = ''
        if result_data and result_data[0]: 
            mandf = result_data[0][0]
        if mandf != '':
            mandatory_arr = mandf.split(',')
      
        from_clause = ""
        language = ""
        where_clause = ""
        where_extra = ""
        join_query = ""
        join_clause = ""
        from_clause1 = ""
        where_clause1 = [""] * len(filterid)
        join_query1 = [""] * len(filterid)
        order_by = ""
        group_by = ""
        columns = ""
        b = 0
        for fid in filterid:
            from_clause = next((f[4] for f in report_filters if f[0] == int(fid)), '')
            if from_clause != '':
                from_clause1 = from_clause

            where_clause1[b] = next((f[5] for f in report_filters if f[0] == int(fid)), '')
            join_query1[b] = next((f[6] for f in report_filters if f[0] == int(fid)), '')
            group_by = next((f[7] for f in report_filters if f[0] == int(fid)), '')
            order_by = next((f[8] for f in report_filters if f[0] == int(fid)), '')
            
            where_clause1[b] = where_clause1[b] if where_clause1[b] is not None else ''
            join_query1[b] = join_query1[b] if join_query1[b] is not None else ''
            group_by = group_by if group_by is not None else ''
            order_by = order_by if order_by is not None else ''
            b += 1
        from_clause = from_clause1
        header_filter = []
        header_sub_filter = []
        filter_name = ""
        cnt1 = 0
        for i in range(len(filterid)):
                if sft[i] and sft[i].strip() not in ("", "0"):
                    filter_name = next((f[2] for f in report_filters if f[0] == int(filterid[i])), '')
                    if filter_name in header_filter:
                       idx = header_filter.index(filter_name)
                       header_sub_filter[idx] += '|' + sft[i]
                    else:
                       header_filter.append(filter_name)
                       header_sub_filter.append(sft[i])  
        b =0
        for sub in range(len(SubFilterId)):
            SubFilterId[sub] = SubFilterId[sub].replace("|", "','")
            if not SubFilterId[sub] or SubFilterId[sub] in ("0", "", " "):
                where_clause1[b] = ""
            else:
                where_clause1[b] = where_clause1[b].replace("BindPara1", SubFilterId[sub])
            b += 1
        
        column_name = callproc("stp_get_dispay_names",[entity])        
        
        result_data = callproc("get_user_role_map",[user])   
        company = '' 
        worksite = ''
        if result_data and result_data[0]:  
            for items in result_data[0]:  
                company = items[0]  
                worksite = items[1]
                
        if columnName == '': 
            column_name_arr = [col[0] for col in column_name] 
            display_name_arr = [col[1] for col in column_name]
            columns = " , ".join(column_name_arr)
        else :
            column_name_arr = columnName.split(',')
            for i, col in enumerate(column_name_arr):
                column_name_arr[i] = col.replace('|', ',')
            display_name_arr = []

            for item in column_name:
                if item[0] in column_name_arr:
                    display_name_arr.append(item[1])

            columns = " , ".join(column_name_arr)

        display_names = " , ".join(display_name_arr)

        for dr in column_join_list:
            check = dr[0]
            if check in columns:
                replace = dr[1]
                columns = columns.replace(check, replace)
            join_clause += dr[2] + " "
        for z in range(len(filterid)):
            if where_clause1[z] not in where_clause:
                if not where_clause:
                    where_clause = " where " + where_clause1[z]
                else:
                    where_clause += " and " + where_clause1[z]
                    
        if not where_clause:
            where_extra = " where "
        else: where_extra = " and "
        
        if entity in ['em']:
            where_extra += "worksite in (" + str(worksite) + ")"
        elif entity in ['cm']:
            where_extra += "company_id in (" + str(company) + ")"
        elif entity in ['sm']:
            where_extra += "t1.company_id in (" + str(company) + ") and site_name in (" + str(worksite) + ")"
        elif entity in ['r']:
            where_extra += "t1.company_id in (" + str(company) + ") and worksite in (" + str(worksite) + ")"
        elif entity in ['nr']:
            where_extra += "t2.company_id in (" + str(company) + ") and t3.worksite in (" + str(worksite) + ")"
                            
            if join_query1[z] not in join_clause:
                join_clause += join_query1[z]

        sql_query = "Select " + columns + " " + from_clause + " " + join_clause + " " + where_clause + " " + where_extra + " " + group_by + " " + order_by
        
        ch = 0
        for value in mandatory_arr:
            if value not in filterid:
                ch = 1
                break
        if ch == 0:
            if not all(value.strip() for value in SubFilterId[:len(mandatory_arr)]):
                ch = 1
            elif len(filterid) != len(SubFilterId):
                ch = 1
                
        data_list= []
        if ch == 0:
            result_data = callproc("stp_get_execute_report_query", [sql_query])
            if result_data and result_data[0]:
                for row in result_data[0]:
                    data_list.append(list(row))
      
        display_name_list = list(display_name_arr)

        if len(data_list) > 0:
            emptycheck = 0
        else : emptycheck = 1
        
        hl = []
        for filter_key, filter_value in zip(header_filter, header_sub_filter):
            if "|" in filter_value:
                values = filter_value.split("|")
                hl.append(f"{filter_key} :- ({','.join(values)})")
            else:
                hl.append(f"{filter_key} :- {filter_value}")
        hl_r = " , ".join(hl)

        data = {
               'headers': hl_r,
               'emptycheck': emptycheck,
               'data_list': data_list,
               'display_name_list': display_name_list,
               'sql_query': sql_query,
               'display_names': display_names
            }
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),user])  
    finally:
          return data
      
def render_to_pdf(html):
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if pdf.err:
        return HttpResponse("Invalid PDF", status_code=400, content_type='text/plain')
    return HttpResponse(result.getvalue(), content_type='application/pdf')

@login_required
def report_pdf(request):
    response = ''
    html_string = ''
    try:
        if request.user.is_authenticated ==True:                
            global user
            user = request.user.id
            if request.method == "POST":
                columnName = str(request.POST.get('columnName', ''))
                filterid = str(request.POST.get('filterid', ''))
                subFilterId = str(request.POST.get('subFilterId', ''))
                sft = str(request.POST.get('sft', ''))
                entity = str(request.POST.get('entity', ''))
                filterid1 = filterid.split(',')
                SubFilterId1 = subFilterId.split(',')
                sft1 = sft.split(',')
                data = common_fun(columnName, filterid1, SubFilterId1, sft1, entity, user)

                headers = data['headers']
                emptycheck = data['emptycheck']
                data_list = data['data_list']
                column_list = data['display_name_list']

                result_data = callproc("stp_get_report_title", [entity])
                title = ''
                if result_data and result_data[0]:
                    for items in result_data[0]:  
                        title = items[0]
                        
                html_string = render_to_string('Reports/report_template.html', {
                    'title': title,
                    'headers': headers,
                    'column_list': column_list,
                    'data_list': data_list,
                })
                pdf = render_to_pdf(html_string)
                filename = title+'.pdf'
                if pdf:
                    response = FileResponse(pdf, content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),request.user.id])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally:
        return response
    
@login_required
def report_xlsx(request):
    response = ''
    try:
        if request.user.is_authenticated ==True:                
            global user
            user = request.user.id
            if request.method == "POST":
                columnName =str(request.POST.get('columnName', ''))
                filterid =str(request.POST.get('filterid', ''))
                subFilterId =str(request.POST.get('subFilterId', ''))
                sft =str(request.POST.get('sft', ''))
                entity =str(request.POST.get('entity', ''))
                filterid1 = filterid.split(',')
                SubFilterId1 = subFilterId.split(',')
                sft1 = sft.split(',')
                data = common_fun(columnName,filterid1,SubFilterId1,sft1,entity,user)

                headers = data['headers']
                emptycheck = data['emptycheck']
                data_list = data['data_list']
                column_list = data['display_name_list']

                result_data = callproc("stp_get_report_title", [entity])
                title = ''
                if result_data and result_data[0]:
                    for items in result_data[0]:  
                        title = items[0]

                output = io.BytesIO()
                workbook = xlsxwriter.Workbook(output)
                worksheet = workbook.add_worksheet(str(entity))

                worksheet.insert_image('A1', 'static/images/CSH-logo0.png', {'x_offset': 10, 'y_offset': 10, 'x_scale': 0.5, 'y_scale': 0.5})

                header_format = workbook.add_format({'align': 'center', 'bold': True, 'font_size': 14})
                data_format = workbook.add_format({'border': 1})
                worksheet.merge_range('A4:{}'.format(chr(65+len(column_list)-1)+'2'), title, header_format)

                filter_format = workbook.add_format({'bold': True})
                worksheet.write(5, 0, headers, filter_format)

                header_format = workbook.add_format({'bold': True, 'bg_color': '#DD8C8D', 'font_color': 'black'})
                for i, column_name in enumerate(column_list):
                    worksheet.write(6, i, column_name, header_format)

                for row_num, row_data in enumerate(data_list, start=7):
                    for col_num, col_data in enumerate(row_data):
                        worksheet.write(row_num, col_num, col_data,data_format)
                workbook.close()
                response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = 'attachment; filename="' + str(title) + '.xlsx"'
                output.seek(0)
                response.write(output.read())
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),request.user.id])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally:
        return response
    
def add_page_number(canvas, doc):
    canvas.saveState()
    page_num = canvas.getPageNumber()
    text = "Page %s" % page_num
    canvas.drawRightString(200*2.54, 1*2.54*2.54, text)
    canvas.restoreState()    

@login_required
def save_filters(request):
    try:
        if request.user.is_authenticated ==True:                
            global user
            user = request.user.id
            if request.method == "GET":
                columnName =str(request.GET.get('columnName', ''))
                filterid =str(request.GET.get('filterid', ''))
                subFilterId =str(request.GET.get('subFilterId', ''))
                sft =str(request.GET.get('sft', ''))
                entity =str(request.GET.get('entity', ''))
                saved_name =str(request.GET.get('save_filter_name', ''))
                f_count =str(request.GET.get('f_count', ''))
                filterid1 = filterid.split(',')
                SubFilterId1 = subFilterId.split(',')
                sft1 = sft.split(',')
                data = common_fun(columnName,filterid1,SubFilterId1,sft1,entity,user)
                sql_query = data['sql_query'] 
                display_names = data['display_names']       
                datalist = callproc("stp_save_report_filters",[saved_name,entity,filterid,subFilterId,columnName,f_count,display_names,sql_query,user])
                response_data = {'result': datalist[0][0]}                       
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),request.user.id])  
        messages.error(request, 'Oops...! Something went wrong!')
        response_data = {'result': 'fail'}       
    finally:
        return JsonResponse(response_data,safe=False)

@login_required
def delete_filters(request):
    try:
        if request.user.is_authenticated ==True:                
            global user
            user = request.user.id
            if request.method == "GET":
                entity =str(request.GET.get('entity', ''))
                saved_id =str(request.GET.get('save_filter_name', ''))
                datalist = callproc("stp_delete_report_filters",[saved_id,entity,user])
                response_data = {'result': datalist[0][0]}                       
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),request.user.id])  
        messages.error(request, 'Oops...! Something went wrong!')
        response_data = {'result': 'fail','messages ':'something went wrong !'}       
    finally:
        return JsonResponse(response_data,safe=False)
    
@login_required
def saved_filters(request):
    try:
        if request.user.is_authenticated ==True:                
            global user
            user = request.user.id
            if request.method == "GET":
                entity =str(request.GET.get('entity', ''))
                saved_id =str(request.GET.get('saved_id', ''))
                result_data  = callproc("stp_get_saved_report_filters",[saved_id,entity,user])
                filters, sub_filters, selected_columns, f_count, display_name, sql_query = ('',) * 6  # Initialize variables
                if result_data and result_data[0]: 
                    for items in result_data[0]: 
                        filters, sub_filters, selected_columns, f_count, display_name, sql_query = items 

                display_name_arr = display_name.split(',')
                display_name_list = list(display_name_arr)
                fil_arr = filters.split(',')
                sub_fil_arr = sub_filters.split(',')
                sel_col_arr = selected_columns.split(',')
                f_id = ''
                s_fid = ''
                if len(fil_arr) > 0:
                    f_id = fil_arr[0]
                    fil_arr = fil_arr[1:]
                if len(sub_fil_arr) > 0:
                    s_fid = sub_fil_arr[0]
                    sub_fil_arr = sub_fil_arr[1:]

                data_list= []
                result_data  = callproc("stp_get_execute_report_query", [sql_query])
                if result_data and result_data[0]:
                    for row in result_data[0]:
                        data_list.append(list(row))

                if len(data_list) > 0:
                    emptycheck = 0
                else : emptycheck = 1

                table = render_to_string('Reports/_partial_report.html', {'emptycheck':emptycheck,'columns':display_name_list,'rows':data_list})

                context = {'result': 'success','filters':fil_arr,'sub_filters':sub_fil_arr,'sel_col_arr':sel_col_arr,
                           'sel_col':selected_columns,'f_count':f_count,'table':table,'f_id':f_id,'s_fid':s_fid}                       
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),request.user.id])  
        messages.error(request, 'Oops...! Something went wrong!')
        context = {'result': 'fail'}       
    finally:
        return JsonResponse(context,safe=False)
 
 