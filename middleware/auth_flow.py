from django.shortcuts import redirect
from django.urls import reverse

class OTPBackForwardGuardMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        otp_verified = request.session.get('otp_verified', False)

        login_url = reverse('citizenLogin')
        otp_url = '/OTPScreen'

        # 🚨 User tries to go back to login/OTP AFTER verification
        if otp_verified and (path.startswith(login_url) or path.startswith(otp_url)):
            # 🔥 HARD INVALIDATE SESSION
            request.session.flush()

            # Mark reason (optional)
            request.session['_forced_logout'] = True

            return redirect(reverse('citizenLogin') + '?expired=1')

        return self.get_response(request)


    
class DisableBrowserCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'

        return response

