import hashlib
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import logout

class SessionBindingMiddleware:
    """
    Middleware to bind a session to a device/browser.
    Works for both admin (Django auth) and citizen (OTP/session-based) users.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        # Admin user (Django auth)
        if hasattr(request, 'user') and request.user.is_authenticated:
            ua = request.META.get('HTTP_USER_AGENT', '')
            ip = request.META.get('REMOTE_ADDR', '')

            current_ua = hashlib.sha256(ua.encode()).hexdigest()
            stored_ua = request.session.get('_ua_hash')
            stored_ip = request.session.get('_ip')

            if stored_ua and (stored_ua != current_ua or stored_ip != ip):
                logout(request)
                request.session.flush()
                messages.warning(
                    request,
                    "We detected a change in your login environment. For your security, you’ve been logged out."
                )
                return redirect('citizenLoginAccount')

        # Citizen user (OTP/session-based)
        elif request.session.get('user_id') and request.session.get('otp_verified'):
            ua = request.META.get('HTTP_USER_AGENT', '')
            ip = request.META.get('REMOTE_ADDR', '')

            current_ua = hashlib.sha256(ua.encode()).hexdigest()
            stored_ua = request.session.get('_ua_hash')
            stored_ip = request.session.get('_ip')

            if stored_ua and (stored_ua != current_ua or stored_ip != ip):
                request.session.flush()
                messages.warning(
                    request,
                    "Your session was terminated due to security reasons. Please log in again."
                )
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
