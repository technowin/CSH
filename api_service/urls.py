# api_service/urls.py  (match the prefixes and names to your existing urls)
from django.urls import path

from api_service.statistics_views import service_statistics
from api_service.token_view import obtain_client_token, refresh_client_token

urlpatterns = [
    path("api/token/", obtain_client_token),
    path("api/token/refresh/", refresh_client_token),
    path("api/v1/cidco/service-statistics/", service_statistics),
]