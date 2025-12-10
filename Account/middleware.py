# Account/middleware.py
from django.utils.deprecation import MiddlewareMixin
from .thread_local import set_current_request, set_current_service, get_current_service
import logging

logger = logging.getLogger(__name__)

class ServiceDatabaseMiddleware(MiddlewareMixin):
    """
    Saves current request + service alias into shared thread-local storage.
    """

    def process_request(self, request):
        try:
            # store request so routers can access it
            set_current_request(request)

            # default fallback if not set in session
            service_db = request.session.get('service_db')
            if not service_db:
                service_db = 'default'

            # store service alias in thread-local
            set_current_service(service_db)

            # also attach to request object for convenience
            request.service_db = service_db

        except Exception as e:
            # Defensive: don't raise here — middleware errors break session processing.
            logger.exception("ServiceDatabaseMiddleware.process_request error: %s", e)
            # ensure request has a fallback to avoid AttributeError later
            try:
                request.service_db = getattr(request, 'service_db', 'default')
                set_current_service(getattr(request, 'service_db', 'default'))
            except Exception:
                pass

    def process_response(self, request, response):
        # optional: clear thread-local values to prevent leakage between requests
        try:
            set_current_request(None)
            set_current_service('default')
        except Exception:
            pass
        return response
