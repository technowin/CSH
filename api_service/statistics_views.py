"""
CIDCO Service Statistics API  (api_service/statistics_views.py)

GET/POST  /api/v1/cidco/service-statistics/?as_of_date=YYYY-MM-DD   (as_of_date optional)

Follows the conventions of the existing COPAS/BPMS endpoints:
  * ClientBasicAuthentication + IsAuthenticated
  * JSON array response containing the statistics records
  * errors logged through stp_error_log
"""
import logging
import traceback
from datetime import date, datetime

from rest_framework import status
from rest_framework.decorators import (
    api_view, authentication_classes, permission_classes, renderer_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from Account.db_utils import callproc
from api_service.authentication import ClientBasicAuthentication

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------------
# Fixed values from the requirement specification
# ----------------------------------------------------------------------------
DEPARTMENT = "CIDCO"
DIVISION = 6                                    # Konkan
PERIOD_START = date(2026, 4, 1)                 # counts are cumulative from here
DISTRICTS = [520, 528, 517, 529, 519, 518, 990]  # Raigarh, Ratnagiri, Thane, Sindhudurg,
                                                 # Mumbai City, Mumbai Suburban, Palghar
SOURCE = "D"                                    # CIDCO data

# The 15 response fields, in the order required by the specification
FIELDS = [
    "Department", "Service", "Division", "District", "Taluka",
    "Approved", "Rejected", "OnTimeDelivery", "PendingatUser",
    "PendingatDepartmentWithinSLA", "PendingatDepartmentAfterSLA",
    "PendingatDepartment", "NotOnTimeDelivery", "PaymentMode", "ApplicationSource",
]
COUNT_FIELDS = FIELDS[5:13]

# ----------------------------------------------------------------------------
# Service registry. One entry per service that has a finished, validated procedure.
#   proc:   stored procedure that takes the as-of date and returns one row per
#           district with the 15 API fields in FIELDS order.
#   database_alias: Django database alias containing this service's tables and
#                   its statistics procedure.
#   source: the ApplicationSource the procedure's counts belong to.
# ----------------------------------------------------------------------------
SERVICES = [
    {
        "id": 8354,
        "proc": "stp_service_statistics_8354",
        "database_alias": "5",  # Product Approval
        "source": "D",
    },
    {
        "id": 8353,
        "proc": "stp_service_statistics_8353",
        "database_alias": "4",  # Contractor Registration
        "source": "D",
    },
    {
        "id": 8291,
        "proc": "stp_service_statistics_8291",
        "database_alias": "2",  # Tree Cutting
        "source": "D",
    },
    {
        "id": 8290,
        "proc": "stp_service_statistics_8290",
        "database_alias": "3",  # Tree Trimming
        "source": "D",
    },
    {
        "id": 8289,
        "proc": "stp_service_statistics_8289",
        "database_alias": "1",  # Drainage Connection
        "source": "D",
    },
   
    
]


# def _fetch_by_district(svc, as_of):
#     """Call the service's stored procedure and return {district_code: row_dict}.

#     callproc returns plain tuples, so columns are mapped by position using FIELDS.
#     Returns an empty dict (all-zero counts) if the procedure does not yet exist,
#     so the endpoint stays live while procedures are being rolled out incrementally.
#     """
#     try:
#         rows = callproc(
#             svc["proc"],
#             [as_of.isoformat()],
#             database_alias=svc["database_alias"],
#         ) or []
#     except Exception as e:
#         error_msg = str(e)
#         if "does not exist" in error_msg or "1305" in error_msg:
#             logger.warning(
#                 "Stored procedure '%s' not found in database alias '%s' — "
#                 "returning zero counts. Create the procedure to populate real data.",
#                 svc["proc"], svc["database_alias"],
#             )
#             return {}
#         raise  # re-raise unexpected DB errors so the view's except block can log them
#     result = {}
#     for r in rows:
#         row = dict(zip(FIELDS, r))
#         result[int(row["District"])] = row
#     return result

def _fetch_by_district(svc, as_of):
    rows = callproc(
        svc["proc"],
        [as_of.isoformat()],
        database_alias=svc["database_alias"],
    ) or []
    result = {}
    for r in rows:
        row = dict(zip(FIELDS, r))
        result[int(row["District"])] = row
    return result


def _build_records(as_of):
    """One record per Service x District x Taluka(0) for the configured source."""
    records = []
    for svc in SERVICES:
        found = _fetch_by_district(svc, as_of)
        for district in DISTRICTS:
            row = found.get(district)
            rec = {
                "Department": DEPARTMENT,
                "Service": svc["id"],
                "Division": DIVISION,
                "District": district,
                "Taluka": 0,
                "PaymentMode": "NA",
                "ApplicationSource": svc.get("source", SOURCE),
            }
            for k in COUNT_FIELDS:
                rec[k] = int(row[k] or 0) if row else 0
            records.append({k: rec[k] for k in FIELDS})   # enforce field order
    return records


@api_view(["GET", "POST"])
@authentication_classes([ClientBasicAuthentication])
@permission_classes([IsAuthenticated])
@renderer_classes([JSONRenderer])
def service_statistics(request):
    try:
        raw = request.query_params.get("as_of_date") or request.data.get("as_of_date")

        if raw:
            try:
                as_of = datetime.strptime(str(raw).strip(), "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"status": False, "message": "as_of_date must be in YYYY-MM-DD format."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            as_of = date.today()

        if as_of < PERIOD_START:
            return Response(
                {"status": False,
                 "message": f"as_of_date cannot be earlier than {PERIOD_START.isoformat()}."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if as_of > date.today():
            return Response(
                {"status": False, "message": "as_of_date cannot be in the future."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        records = _build_records(as_of)

        return Response(records, status=status.HTTP_200_OK)

    except Exception as e:
        try:
            tb = traceback.extract_tb(e.__traceback__)
            fun = tb[0].name if tb else "service_statistics"
            user_id = getattr(request.user, "id", None)
            callproc("stp_error_log", [fun, str(e), user_id])
        except Exception as log_error:
            logger.error("Error logging failed: %s | original error: %s", log_error, e)

        # Details are in stp_error_log; they are not returned to the caller.
        return Response(
            {"status": False, "message": "Internal server error."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )