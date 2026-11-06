"""Basic authentication for API clients."""
import base64
import binascii
import hmac

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from Account.models import APIClient


class ClientUser:
    """Minimal stand-in user so IsAuthenticated passes for API clients."""
    is_authenticated = True
    is_anonymous = False
    id = None

    def __init__(self, client):
        self.client = client
        self.username = client.client_id


class ClientBasicAuthentication(BaseAuthentication):
    """Authorization: Basic base64(client_id:client_secret)"""

    def authenticate(self, request):
        parts = request.META.get("HTTP_AUTHORIZATION", "").split()
        if not parts or parts[0].lower() != "basic":
            return None
        if len(parts) != 2:
            raise AuthenticationFailed("Invalid Basic authorization header.")

        try:
            decoded = base64.b64decode(parts[1], validate=True).decode("utf-8")
            client_id, separator, client_secret = decoded.partition(":")
        except (binascii.Error, UnicodeDecodeError, ValueError):
            raise AuthenticationFailed("Invalid Basic authorization header.")
        if not separator or not client_id or not client_secret:
            raise AuthenticationFailed("Invalid Basic authorization header.")

        client = APIClient.objects.using("default").filter(
            client_id=client_id, is_active=True
        ).first()
        if not client or not hmac.compare_digest(
            str(client.client_secret).encode("utf-8"), client_secret.encode("utf-8")
        ):
            raise AuthenticationFailed("Invalid client credentials.")

        return (ClientUser(client), None)

    def authenticate_header(self, request):
        return 'Basic realm="CIDCO Statistics API"'