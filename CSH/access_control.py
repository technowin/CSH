from functools import wraps
from django.contrib import messages
from urllib.parse import urlparse

ALLOWED_EXTERNAL_HOSTS = {
    'aaplesarkar.mahaonline.gov.in',
}

def no_direct_access(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        referer = request.META.get('HTTP_REFERER')
        current_host = request.get_host()

        # If referer exists, validate it
        if referer:
            parsed = urlparse(referer)
            referer_host = parsed.netloc

            # Internal navigation
            if referer_host == current_host:
                return view_func(request, *args, **kwargs)

            # Trusted external portal
            if referer_host in ALLOWED_EXTERNAL_HOSTS:
                return view_func(request, *args, **kwargs)

            # Unknown referer → block
            messages.warning(
                request,
                "Your session could not be verified."
            )
            from Account.views import logoutView
            return logoutView(request)

        # ❗ No referer at all
        # Do NOT logout blindly — fallback to session check
        if request.session.get('user_id'):
            return view_func(request, *args, **kwargs)

        messages.warning(
            request,
            "Your session could not be verified."
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
