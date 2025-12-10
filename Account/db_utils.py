from django.db import connections, DEFAULT_DB_ALIAS
from .thread_local import get_current_service
import logging

logger = logging.getLogger(__name__)

class Db:
    @staticmethod
    def get_connection(database_alias=None):
        service_alias = database_alias or get_current_service() or DEFAULT_DB_ALIAS
        # ensure alias exists in settings.DATABASES
        if service_alias not in connections:
            logger.warning("Requested DB alias '%s' not in connections, falling back to default", service_alias)
            service_alias = DEFAULT_DB_ALIAS
        return connections[service_alias]

    @staticmethod
    def close_connection(database_alias=None):
        service_alias = database_alias or get_current_service() or DEFAULT_DB_ALIAS
        try:
            conn = connections[service_alias]
            if conn and not conn.closed_in_transaction:
                conn.close()
        except Exception as e:
            logger.exception("Error closing connection '%s': %s", service_alias, e)


def callproc(procedure_name, params=None):
    connection = Db.get_connection()
    try:
        fetched_data = []
        with connection.cursor() as cursor:
            cursor.callproc(procedure_name, params or [])
            # For mysql-connector: iterate stored_results if supported
            try:
                for result in cursor.stored_results():
                    fetched_data = result.fetchall()
            except Exception:
                # fallback for other DB backends where stored_results() isn't available
                try:
                    fetched_data = cursor.fetchall()
                except Exception:
                    fetched_data = []
            connection.commit()
            return fetched_data
    except Exception as e:
        connection.rollback()
        raise
    finally:
        Db.close_connection()

def get_service_db():
    """
    Returns the current selected database alias from thread-local storage.
    """
    return get_current_service()