import hashlib
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from Account.views import get_client_ip
from Account.models import SessionActivityLog

class SessionBindingMiddleware:
    """
    Binds a session to a specific browser + IP.
    Protects against session hijacking.
    Works for:
    - Admin users (Django auth)
    - Citizen users (OTP/session-based)
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip session binding for unauthenticated users
        if not request.session.get('_ua_hash') and not request.user.is_authenticated:
            return self.get_response(request)
        
        ua = request.META.get('HTTP_USER_AGENT', '')
        ip = get_client_ip(request)

        current_ua_hash = hashlib.sha256(ua.encode()).hexdigest()
        stored_ua_hash = request.session.get('_ua_hash')
        stored_ua = request.session.get('_ua_raw')
        stored_ip = request.session.get('_ip')

        # Check if session binding exists
        if stored_ua_hash:
                
            # 🔐 Admin user
            if hasattr(request, 'user') and request.user.is_authenticated:
                
                log_session_activity(
                    request,
                    action='mismatch_detected',
                    remarks='UA or IP mismatch – forced logout',
                    current_ua=ua,
                    current_ua_hash=current_ua_hash,
                    current_ip=ip
                )
                    
                if stored_ua_hash != current_ua_hash or stored_ip != ip:
                    logout(request)
                    request.session.flush()
                    return redirect('citizenLoginAccount')  # Redirect to admin login
            
            # 🔐 Citizen user (OTP-based)
            elif request.session.get('user_id') and request.session.get('otp_verified'):
                
                log_session_activity(
                    request,
                    action='mismatch_detected',
                    remarks='UA or IP mismatch – forced logout',
                    current_ua=ua,
                    current_ua_hash=current_ua_hash,
                    current_ip=ip
                )
                
                if stored_ua_hash != current_ua_hash or stored_ip != ip:
                    logout(request)
                    request.session.flush()
                    return redirect('citizenLoginAccount') 
        
        return self.get_response(request)
    
def log_session_activity(request, action, remarks='', current_ua=None, current_ua_hash=None, current_ip=None):
    try:
        user_id = None
        user_type = None

        if hasattr(request, 'user') and request.user.is_authenticated:
            user_id = str(request.user.id)
            user_type = 'admin'
        elif request.session.get('user_id'):
            user_id = str(request.session.get('user_id'))
            user_type = 'citizen'

        SessionActivityLog.objects.create(
            user_id=user_id,
            user_type=user_type,
            ip_address=current_ip,
            stored_ip_address=request.session.get('_ip'),

            user_agent=current_ua,
            stored_user_agent=request.session.get('_ua_raw'),

            user_agent_hash=current_ua_hash,
            stored_user_agent_hash=request.session.get('_ua_hash'),

            action=action,
            remarks=remarks
        )
    except Exception:
        # logging must NEVER break auth flow
        pass

# from django.contrib.auth import logout
# from django.shortcuts import redirect
# from django.contrib import messages
# import hashlib

# class SessionBindingMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         if request.user.is_authenticated:
#             ua = request.META.get('HTTP_USER_AGENT', '')
#             ip = request.META.get('REMOTE_ADDR', '')

#             current_ua = hashlib.sha256(ua.encode()).hexdigest()
#             stored_ua = request.session.get('_ua_hash')
#             stored_ip = request.session.get('_ip')  

#             # If session is hijacked / used from different device
#             if stored_ua != current_ua or stored_ip != ip:
#                 # Log out user and flush session
#                 logout(request)
#                 request.session.flush()

#                 # Add a message so user knows what happened
#                 messages.warning(
#                     request,
#                     "We detected a change in your login environment. For your security, you’ve been logged out."
#                 )
#                 return redirect('citizenLoginAccount')

#         return self.get_response(request)
