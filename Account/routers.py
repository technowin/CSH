
# myapp/routers.py

import threading

# Create a thread-local object to store the current request
_thread_locals = threading.local()

def get_current_request():
    return getattr(_thread_locals, 'request', None)

class ServiceRouter:
    """
    A router to control database operations for service-specific databases.
    """

    def db_for_read(self, model, **hints):
        """
        Attempts to route read operations to the appropriate database based on the 'service' hint.
        """
        request = get_current_request()
        if request and hasattr(request, 'service_db'):
            service = request.service_db
            return service
          

    def db_for_write(self, model, **hints):
        """
        Attempts to route write operations to the appropriate database based on the 'service' hint.
        """
        request = get_current_request()
        if request and hasattr(request, 'service_db'):
            service = request.service_db
            return service
