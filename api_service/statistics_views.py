"""
CIDCO Service Statistics API  (api_service/statistics_views.py)

GET/POST  /api/v1/cidco/service-statistics/?as_of_date=YYYY-MM-DD   (as_of_date optional)

Follows the conventions of the existing COPAS/BPMS endpoints:
  * ClientJWTAuthentication + IsAuthenticated (token from obtain_client_token)
  * {"status": True/False, "message": ...} response envelope
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
from api_service.authentication import ClientJWTAuthentication

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------------
# Fixed values from the requirement specification
# ----------------------------------------------------------------------------
DEPARTMENT = "CIDCO"
DIVISION = 6                                    # Konkan
PERIOD_START = date(2026, 4, 1)                 # counts are cumulative from here
DISTRICTS = [520, 528, 517, 529, 519, 518, 990]  # Raigarh, Ratnagiri, Thane, Sindhudurg,
                                                 # Mumbai City, Mumbai Suburban, Palghar
SOURCES = ["D", "U"]                             # D = CIDCO data, U = Aaple Sarkar data

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
#   source: the ApplicationSource the procedure's counts belong to. The other
#           source is returned as zero rows until a procedure exists for it.
# Add 8353, 8291, 8290, 8354 here as their procedures are completed.
# ----------------------------------------------------------------------------
SERVICES = [
    {"id": 8289, "proc": "stp_service_statistics_8289", "source": "D"},
]


def _fetch_by_district(svc, as_of):
    """Call the service's stored procedure and return {district_code: row_dict}.

    callproc returns plain tuples, so columns are mapped by position using FIELDS.
    """
    rows = callproc(
        svc["proc"],
        [as_of.isoformat()],
        database_alias="default",
    ) or []
    result = {}
    for r in rows:
        row = dict(zip(FIELDS, r))
        result[int(row["District"])] = row
    return result


def _build_records(as_of):
    """One record per Service x District x Taluka(0) x ApplicationSource."""
    records = []
    for svc in SERVICES:
        found = _fetch_by_district(svc, as_of)
        for district in DISTRICTS:
            for source in SOURCES:
                row = found.get(district) if source == svc["source"] else None
                rec = {
                    "Department": DEPARTMENT,
                    "Service": svc["id"],
                    "Division": DIVISION,
                    "District": district,
                    "Taluka": 0,
                    "PaymentMode": "NA",
                    "ApplicationSource": source,
                }
                for k in COUNT_FIELDS:
                    rec[k] = int(row[k] or 0) if row else 0
                records.append({k: rec[k] for k in FIELDS})   # enforce field order
    return records


@api_view(["GET", "POST"])
@authentication_classes([ClientJWTAuthentication])
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

        return Response(
            {
                "status": True,
                "message": "Service statistics fetched successfully.",
                "department": DEPARTMENT,
                "period_from": PERIOD_START.isoformat(),
                "as_of_date": as_of.isoformat(),
                "record_count": len(records),
                "data": records,
            },
            status=status.HTTP_200_OK,
        )

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