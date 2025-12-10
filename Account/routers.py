# Account/routers.py
from .thread_local import get_current_service
import logging

logger = logging.getLogger(__name__)

class ServiceRouter:
    """
    Route DB operations based on service alias from thread-local storage.
    """

    def _service_alias(self):
        try:
            return get_current_service() or 'default'
        except Exception as e:
            logger.exception("ServiceRouter._service_alias error: %s", e)
            return 'default'

    def db_for_read(self, model, **hints):
        service = self._service_alias()

        # route common apps to selected service
        if model._meta.app_label in ('Account', 'Masters'):
            return service

        # route service-specific apps to configured aliases
        app = model._meta.app_label
        mapping = {
            'DrainageConnection': '1',
            'TreeCutting': '2',
            'TreeTrimming': '3',
            'ContractRegistration': '4',
            'ProductApproval': '5',
        }
        return mapping.get(app, service)

    def db_for_write(self, model, **hints):
        # same logic as read
        return self.db_for_read(model, **hints)
