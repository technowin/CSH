from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from Account.models import APIClient


def _build_client_tokens(client):
    refresh = RefreshToken()
    refresh["username"] = client.client_id
    refresh["client_id"] = client.client_id

    access = refresh.access_token
    access["username"] = client.client_id
    access["client_id"] = client.client_id

    return {
        "access": str(access),
        "refresh": str(refresh),
        "client_id": client.client_id,
    }


@api_view(["POST"])
@permission_classes([AllowAny])
def obtain_client_token(request):
    client_id = (request.data.get("client_id") or request.data.get("username") or "").strip()
    client_secret = (request.data.get("client_secret") or request.data.get("password") or "").strip()

    if not client_id or not client_secret:
        return Response(
            {"detail": "client_id and client_secret are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    client = APIClient.objects.using("default").filter(
        client_id=client_id,
        client_secret=client_secret,
        is_active=True,
    ).first()
    if not client:
        return Response({"detail": "Invalid client credentials."}, status=status.HTTP_401_UNAUTHORIZED)

    return Response(_build_client_tokens(client), status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([AllowAny])
def refresh_client_token(request):
    serializer = TokenRefreshSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    return Response(serializer.validated_data, status=status.HTTP_200_OK)
