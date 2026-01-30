class NoCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Check for ADMIN authentication (Django auth)
        is_admin_authenticated = hasattr(request, 'user') and request.user.is_authenticated
        
        # Check for CITIZEN authentication (session-based)
        is_citizen_authenticated = (
            request.session.get('user_id') and 
            request.session.get('phone_number')
        )
        
        # ✅ Check if user_id exists in either form
        # Some views might use 'user' instead of 'user_id' in session
        has_user_id = request.session.get('user_id') or request.session.get('user')
        
        # ✅ Additional check: If user is authenticated via Django OR has session user data
        is_any_authenticated = (
            is_admin_authenticated or 
            is_citizen_authenticated or
            has_user_id
        )
        
        # Apply no-cache headers if ANY authentication method is active
        if is_any_authenticated:
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0, post-check=0, pre-check=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = 'Mon, 01 Jan 1990 00:00:00 GMT'
            response['Vary'] = '*'
        
        # Also prevent caching for ALL auth-related pages AND static assets used in auth
        auth_paths = [
            '/citizenLoginAccount', 
            '/logout/', 
            '/login/', 
            '/Login/',
            '/OTPScreenPost',
            '/accounts/login/',
            '/accounts/logout/',
            '/admin/',  # Admin pages
            '/services/',  # Services page after login
            '/applicationFormIndex/',  # Protected citizen pages
            '/index/',  # Protected admin pages
        ]
        
        # Check if path starts with any auth path
        path_matches = any(request.path.startswith(path) for path in auth_paths)
        
        # Also check for GET parameters in citizen login
        is_citizen_login = '/citizenLoginAccount' in request.path
        
        if path_matches or is_citizen_login:
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            
        # ✅ EXTRA: Also add cache headers for POST requests (logout is usually POST)
        if request.method == 'POST':
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        
        return response
    
# class NoCacheMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         response = self.get_response(request)
        
#         # Always add cache control for authenticated/sensitive pages
#         if request.session.get('user_id') and request.session.get('phone_number'):
#             # User is logged in (by your session criteria)
#             response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0, post-check=0, pre-check=0'
#             response['Pragma'] = 'no-cache'
#             response['Expires'] = 'Mon, 01 Jan 1990 00:00:00 GMT'
#             response['Vary'] = '*'
            
#         # Also prevent caching for auth-related pages
#         auth_paths = ['/citizenLoginAccount', '/logout/', '/OTPScreenPost']
#         if any(request.path.startswith(path) for path in auth_paths):
#             response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
#             response['Pragma'] = 'no-cache'
#             response['Expires'] = '0'
            
#         return response
    
