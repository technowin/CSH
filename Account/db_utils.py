# myapp/db_utils.py

from django.db import connections
from .thread_local import get_current_service

class Db:
    @staticmethod
    def get_connection(database_alias='default'):
        """
        Get the database connection based on the alias provided (e.g., 'default', 'service1_db').
        """
        service_alias = get_current_service()  # Fetch dynamically from thread-local storage
        return connections[service_alias]

    @staticmethod
    def close_connection(database_alias='default'):
        """
        Close the database connection if it's open.
        """
        service_alias = get_current_service()
        connection = connections[service_alias]
        if connection and not connection.closed_in_transaction:
            connection.close()

def callproc(procedure_name, params=None):
    """
    Calls the specified stored procedure on the selected service database.
    """
    connection = Db.get_connection()
    try:
        fetched_data=[]
        with connection.cursor() as cursor:
            cursor.callproc(procedure_name, params)
            for result in cursor.stored_results():
                fetched_data = result.fetchall()
            connection.commit()
            return fetched_data
    except Exception as e:
        connection.rollback()
        print(f"Error: {e}")
        raise
    finally:
        Db.close_connection()


def get_service_db():
    """
    Returns the current selected database alias from thread-local storage.
    """
    return get_current_service()