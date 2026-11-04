"""
api_service/authentication.py

Use this ONLY if the project does not already have api_service.authentication
(copy the file from the other project instead, if you can).
It validates the access token issued by obtain_client_token, which carries a
'username' claim (the APIClient.client_id) and no user id.
"""
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

from Account.models import APIClient


class ClientUser:
    """Minimal stand-in user so IsAuthenticated passes for API clients."""
    is_authenticated = True
    is_anonymous = False
    id = None

    def __init__(self, client):
        self.client = client
        self.username = client.client_id


class ClientJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        parts = request.META.get("HTTP_AUTHORIZATION", "").split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None                      # no token: DRF answers 401

        try:
            token = AccessToken(parts[1])
        except TokenError:
            raise AuthenticationFailed("Token is invalid or expired.")

        client = APIClient.objects.using("default").filter(
            client_id=token.get("username"), is_active=True
        ).first()
        if not client:
            raise AuthenticationFailed("API client not found or inactive.")

        return (ClientUser(client), token)

    def authenticate_header(self, request):
        return "Bearer"