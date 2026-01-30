from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse

class SessionExpiryRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip middleware for login/logout pages
        if request.path in ['/logout/', '/login/', '/citizenLoginAccount/', '/OTPScreenPost/']:
            return self.get_response(request)
        
        response = self.get_response(request)
        
        # Check if user is not authenticated but session expired flag exists
        # AND user didn't manually logout
        if (hasattr(request, 'user') and 
            not request.user.is_authenticated and 
            request.session.get('_session_expired') and
            not request.session.get('_user_logged_out')):
            
            # Clear the expired flag
            request.session.pop('_session_expired', None)
            
            # Clear any remaining user session data
            user_session_keys = ['phone_number', 'user_id', 'role_id', 'full_name', 'service_db']
            for key in user_session_keys:
                if key in request.session:
                    del request.session[key]
            
            # Set cache headers
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect(reverse('citizenLoginAccount'))
            
        return response