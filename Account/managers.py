# myapp/managers.py
from django.db import models
from .db_utils import get_service_db

class ServiceManager(models.Manager):
    def get_queryset(self):
        service_db = get_service_db()
        return super().get_queryset().using(service_db)
