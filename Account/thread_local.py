# Account/thread_local.py
import threading

_thread_locals = threading.local()

# Request
def set_current_request(request):
    """Store the current request in thread-local storage."""
    _thread_locals.request = request

def get_current_request():
    """Return the current request or None."""
    return getattr(_thread_locals, 'request', None)

# Service (database alias)
def set_current_service(service):
    """Store the current service/database alias in thread-local storage."""
    _thread_locals.service = service

def get_current_service():
    """Return the current service alias or 'default'."""
    return getattr(_thread_locals, 'service', 'default')
