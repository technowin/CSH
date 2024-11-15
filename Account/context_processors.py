from django.conf import settings
from CSH.encryption import decrypt_parameter
import Db
from .db_utils import callproc
from django.utils import timezone
from Masters.models import service_master
def logged_in_user(request):
    user =''
    session_cookie_age_seconds = settings.AUTO_LOGOUT['IDLE_TIME']
    session_timeout_minutes = session_cookie_age_seconds 
    username = request.session.get('username', '')
    full_name = request.session.get('full_name', '')
    user_id = request.session.get('user_id', '')
    role_id = request.session.get('role_id', '')
    if request.user.is_authenticated ==True:
        user = str(request.user.id or '')
    reports = ''    
    menu_items = []
    # result_data  = callproc("stp_get_all_reports", [user])
    # if result_data and result_data[0]: 
    #     for items in result_data[0]:
    #         reports = items[0]     
    service_db = request.session.get('service_db') 
    if service_db and service_db!='default' and user_id!='' and role_id!='':
        menu_data = callproc("stp_get_side_navbar_details", [user_id, role_id])

        # Organize the menu data
        items = []
        for row in menu_data:
            item = { 'id': row[1], 'name': row[2], 'action': row[3],  'is_parent': row[4],'parent_id': row[5],
                    'is_sub_menu': row[6], 'sub_menu': row[7],'is_sub_menu2': row[8],'sub_menu2': row[9],'menu_icon': row[10]
            }
            items.append(item)

        # Build the hierarchy
        menu_dict = {}
        for item in items:
            item['children'] = [i for i in items if i['parent_id'] == item['id']]
            if item['parent_id'] not in menu_dict:
                menu_dict[item['parent_id']] = []
            menu_dict[item['parent_id']].append(item)

        menu_items = menu_dict.get(-1, []) 
    service = ''  
    
    if service_db: 
        service1 = service_master.objects.using('default').filter(ser_id=service_db).first()
        service = service1.ser_name

    return {'username':username,'full_name':full_name,'session_timeout_minutes':session_timeout_minutes,'reports':reports, 'menu_items': menu_items, 'service': service}