from django.conf import settings
from CSH.encryption import decrypt_parameter
import Db

def logged_in_user(request):
    
    Db.closeConnection()
    m = Db.get_connection()
    cursor=m.cursor()
    user =''
    session_cookie_age_seconds = settings.AUTO_LOGOUT['IDLE_TIME']
    session_timeout_minutes = session_cookie_age_seconds 
    username = request.session.get('username', '')
    full_name = request.session.get('full_name', '')
    user_id = request.session.get('user_id', '')
    role_id = request.session.get('role_id', '')
    if request.user.is_authenticated ==True:
        user = str(request.user.id or '')
        
    cursor.callproc("stp_get_all_reports", [user])
    for result in cursor.stored_results():
        for items in result.fetchall():
            reports = items[0]     
    
    cursor.callproc("stp_get_side_navbar_details", [user_id, role_id])
    for result in cursor.stored_results():
            menu_data = list(result.fetchall())
        
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
    
    cursor.close()
    m.commit()
    cursor.close()
    m.close()
    Db.closeConnection()        
    return {'username':username,'full_name':full_name,'session_timeout_minutes':session_timeout_minutes,'reports':reports, 'menu_items': menu_items}