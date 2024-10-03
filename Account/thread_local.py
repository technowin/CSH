# myapp/thread_local.py
import threading

# Thread-local storage object
_thread_locals = threading.local()

def get_current_service():
    """
    Get the current service (database) from thread-local storage.
    """
    return getattr(_thread_locals, 'service', 'default')

def set_current_service(service):
    """
    Set the current service (database) in thread-local storage.
    """
    _thread_locals.service = service
