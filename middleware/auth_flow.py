from django.shortcuts import redirect
from django.urls import reverse

class OTPBackForwardGuardMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        otp_verified = request.session.get('otp_verified', False)
        admin_flow_done = request.session.get('admin_flow_completed', False)

        citizen_login_url = reverse('citizenLogin')
        admin_login_url = reverse('Login')
        otp_url = '/OTPScreen'
        service_url = reverse('services')

        # 🔴 CITIZEN: Back to login / OTP after verification
        if otp_verified and (
            path.startswith(citizen_login_url) or path.startswith(otp_url)
        ):
            request.session.flush()
            return redirect(citizen_login_url + '?expired=1')

        # 🔴 ADMIN: Back to login / service after flow completed
        if admin_flow_done and (
            path.startswith(admin_login_url) or path.startswith(service_url)
        ):
            request.session.flush()
            return redirect(admin_login_url + '?expired=1')

        return self.get_response(request)


# class OTPBackForwardGuardMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         path = request.path
#         otp_verified = request.session.get('otp_verified', False)

#         login_url = reverse('citizenLogin')
#         otp_url = '/OTPScreen'

#         # 🚨 User tries to go back to login/OTP AFTER verification
#         if otp_verified and (path.startswith(login_url) or path.startswith(otp_url)):
#             # 🔥 HARD INVALIDATE SESSION
#             request.session.flush()

#             # Mark reason (optional)
#             request.session['_forced_logout'] = True

#             return redirect(reverse('citizenLogin') + '?expired=1')

#         return self.get_response(request)


    
class DisableBrowserCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'

        return response

