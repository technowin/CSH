import hashlib
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import logout


def get_client_ip(request):
    """
    Returns the real client IP.
    Works correctly behind proxies / load balancers.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


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

        ua = request.META.get('HTTP_USER_AGENT', '')
        ip = get_client_ip(request)

        current_ua = hashlib.sha256(ua.encode()).hexdigest()
        stored_ua = request.session.get('_ua_hash')
        stored_ip = request.session.get('_ip')

        # 🔐 Admin user
        if hasattr(request, 'user') and request.user.is_authenticated:
            if stored_ua and (stored_ua != current_ua or stored_ip != ip):
                logout(request)
                request.session.flush()
                
                return redirect('citizenLoginAccount')

        # 🔐 Citizen user (OTP-based)
        elif request.session.get('user_id') and request.session.get('otp_verified'):
            if stored_ua and (stored_ua != current_ua or stored_ip != ip):
                request.session.flush()
               
                return redirect('citizenLoginAccount')

        return self.get_response(request)



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
