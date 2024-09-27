import mysql.connector as sql
from mysql.connector import pooling
from CSH.settings import DATABASES
_connection = None

def get_connection():
    global _connection
    if _connection is  None:
        # Create a connection pool
        _connection = sql.connect(
            # pool_name="mypool",
            #                       pool_size=32,                                
                                  host= DATABASES["default"]["HOST"],
                                  # host="52.172.154.80",
                                  user=DATABASES["default"]["USER"],
                                  password=DATABASES["default"]["PASSWORD"],                                
                                  # password="Mysqlcsr@2023",
                                  database=DATABASES["default"]["NAME"],
                                  auth_plugin='mysql_native_password',
                                  connect_timeout= 100)
        _connection.autocommit = True
    # else:
        # if _connection is not None and _connection.is_connected():
        # Create a connection pool
            # _connection = sql.connect(pool_name="mypool",
            #                         pool_size=32,                                
            #                         host= DATABASES["default"]["HOST"],
            #                         # host="52.172.154.80",
            #                         user=DATABASES["default"]["USER"],
            #                         password=DATABASES["default"]["PASSWORD"],                                
            #                         # password="Mysqlcsr@2023",
            #                         database=DATABASES["default"]["NAME"],
            #                         auth_plugin='mysql_native_password',
            #                         connect_timeout= 100)
    return _connection

def closeConnection():
    global _connection
    _connection=None