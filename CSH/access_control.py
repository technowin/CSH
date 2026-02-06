from functools import wraps
from django.contrib import messages
from django.conf import settings

from functools import wraps
from django.contrib import messages
from urllib.parse import urlparse

ALLOWED_EXTERNAL_REFERRERS = [
    'aaplesarkar.mahaonline.gov.in',
    'aaplesarkar.gov.in', 
    'mahaonline.gov.in',
    'gov.in',  # Allow all .gov.in sites if needed
]

def no_direct_access(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        referer = request.META.get('HTTP_REFERER')
        
        # 🔴 CRITICAL FIX: Always allow if user has valid session
        # This handles bookmarks, typed URLs, etc.
        if request.session.get('user_id') and request.session.get('phone_number'):
            return view_func(request, *args, **kwargs)
        
        # If no referer AND no valid session → block
        if not referer:
            messages.warning(
                request,
                "Please login to access this page."
            )
            from Account.views import logoutView
            return logoutView(request)
        
        try:
            referer_host = urlparse(referer).netloc
            
            # Internal navigation
            if referer_host == request.get_host():
                return view_func(request, *args, **kwargs)
            
            # External trusted sites
            for allowed in ALLOWED_EXTERNAL_REFERRERS:
                if allowed in referer_host:
                    return view_func(request, *args, **kwargs)
                    
        except Exception:
            # If URL parsing fails, be conservative and block
            pass
        
        # Block everything else
        messages.warning(
            request,
            "Access denied. Please navigate through proper channels."
        )
        from Account.views import logoutView
        return logoutView(request)

    return _wrapped_view


# from django.shortcuts import redirect
# from functools import wraps
# from django.contrib import messages

# def no_direct_access(view_func):
#     @wraps(view_func)
#     def _wrapped_view(request, *args, **kwargs):
#         referer = request.META.get('HTTP_REFERER')
#         current_host = request.get_host()

#         if not referer or current_host not in referer:
#             from Account.views import logoutView

#             messages.warning(
#                 request,
#                 "Your session could not be verified."
#             )

#             return logoutView(request)

#         return view_func(request, *args, **kwargs)

#     return _wrapped_view
