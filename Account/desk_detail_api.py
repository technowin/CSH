import traceback
import requests
import json
from django.conf import settings
from django.utils import timezone
from requests.exceptions import RequestException, Timeout

from Account.db_utils import callproc

# ------------------------------------------------------------------
# API BASE URLs (keep configurable)
# ------------------------------------------------------------------
LIVE_URL = "https://www.cidcoindia.com/AapleMiddlewareAPITest/api"
TEST_URL = "https://www.cidcoindia.com/AapleMiddlewareAPITest/api"

API_BASE_URL = TEST_URL   # switch based on environment


# ------------------------------------------------------------------
# Generate Token
# ------------------------------------------------------------------
def generate_token():
    """
    Generate bearer token from Appellate API
    """
    url = f"{API_BASE_URL}/AppellateToken/AppellateGenerateToken"

    payload = {
        "Username": "cidcoLTD",
        "password": "cidco@12"
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=15
        )
        response.raise_for_status()

        response_json = response.json()
        token = response_json.get("token")

        if not token:
            raise ValueError("Token not found in response")

        return token

    except (RequestException, Timeout, ValueError) as e:
        # Log this properly in production
        print("Token generation failed:", str(e))
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), 'DESK DETAILS API'])
        return None


# ------------------------------------------------------------------
# Update Desk Details API
# ------------------------------------------------------------------
def upd_desk_detail(request):
    """
    Send desk details to Aaple Sarkar API
    """
    # ------------------------------------------------------------------
    # Session data
    # ------------------------------------------------------------------
    application_id = request.session.get("ApplicationId")
    desk_number = request.session.get("DeskNumber")
    review_action_by = request.session.get("ReviewActionBy")
    review_action_datetime = request.session.get(
        "ReviewActionDateTime",
        timezone.now().isoformat()
    )
    review_action_details = request.session.get("ReviewActionDetails")
    desk_remark = request.session.get("DeskRemark")

    # ------------------------------------------------------------------
    # Validate required fields
    # ------------------------------------------------------------------
    if not application_id or not desk_number:
        return {
            "success": False,
            "message": "ApplicationId or DeskNumber missing"
        }

    # ------------------------------------------------------------------
    # Generate token
    # ------------------------------------------------------------------
    token = generate_token()
    if not token:
        return {
            "success": False,
            "message": "Unable to generate authentication token"
        }

    # ------------------------------------------------------------------
    # API Call
    # ------------------------------------------------------------------
    url = f"{API_BASE_URL}/RequestFromAapleSarkar/InsertDeskDetails"

    payload = {
        "ApplicationId": application_id,
        "DeskNumber": desk_number,
        "ReviewActionBy": review_action_by,
        "ReviewActionDateTime": review_action_datetime,
        "ReviewActionDetails": review_action_details,
        "DeskRemark": desk_remark
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=20
        )
        response.raise_for_status()

        response_json = response.json()

        return {
            "success": True,
            "data": response_json.get("data"),
            "message": response_json.get("message", "Desk details updated successfully")
        }

    except (RequestException, Timeout) as e:
        # Log error properly
        print("Desk update failed:", str(e))
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), 'DESK DETAILS API'])
        return {
            "success": False,
            "message": "API request failed",
            "error": str(e)
        }
        