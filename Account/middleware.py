# myapp/middleware.py

from django.utils.deprecation import MiddlewareMixin
import threading
from .thread_local import set_current_service

# Thread-local storage
_thread_locals = threading.local()

def set_current_request(request):
    _thread_locals.request = request

class ServiceDatabaseMiddleware(MiddlewareMixin):
    """
    Middleware to automatically set the selected database based on the user's session.
    """
    def process_request(self, request):
          # Store the current request in thread-local storage
        set_current_request(request)
        
        # Retrieve the selected service from the session
        service_db = request.session.get('service_db', 'default')
        
        # Store the selected service in thread-local storage
        set_current_service(service_db)
        # Store the selected service for later use in database routing
        request.service_db = service_db
