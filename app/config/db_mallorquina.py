from fastapi import HTTPException

# Para MySql
import mysql.connector
from mysql.connector import Error
from app.config.settings import settings

from app.utils.functions import graba_log

# Para SQL Server
import pyodbc


#----------------------------------------------------------------------------------------
def get_db_connection_mysql():
    try:
        connection = mysql.connector.connect(
            host=settings.MYSQL_DB_URL_MLL,
            user=settings.MYSQL_DB_USER_MLL,
            password= settings.MYSQL_DB_PWD_MLL,
            database=settings.MYSQL_DB_DATABASE_MLL
        )
        return connection
    
    except Exception as e:
        graba_log({"ret_code": -1, "ret_txt": f"Error al conectar: {settings.MYSQL_DB_URL_MLL}/{settings.MYSQL_DB_USER_MLL}/{settings.MYSQL_DB_DATABASE_MLL}/"},
                   "Excepción get_db_connection_mysql", e)
        raise HTTPException(status_code=400, detail= {"ret_code": -1,
                                                      "ret_txt": str(e),
                                                     }
                           )

#----------------------------------------------------------------------------------------
def close_connection_mysql(conn, cursor):
    try:
        if conn is not None and conn.is_connected():
            if isinstance(cursor, mysql.connector.cursor.MySQLCursor):
                cursor.close()
            conn.close()
    
    except Error as e:
        raise HTTPException(status_code=400, detail= {"ret_code": -1,
                                                      "ret_txt": str(e),
                                                     }
                           )

#----------------------------------------------------------------------------------------
def get_db_connection_sqlserver(conexion_json):
    try:
        conexion = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={conexion_json['host']};DATABASE={conexion_json['database']};UID={conexion_json['user']};PWD={conexion_json['password']}"
        donde = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={conexion_json['host']};DATABASE={conexion_json['database']};UID={conexion_json['user']};PWD='XXXXXXX'"
        connection =  pyodbc.connect(conexion)

        #connection =  pyodbc.connect(f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={conexion_json['host']};"
        #                             f"DATABASE={conexion_json['database']};UID={conexion_json['user']};PWD={conexion_json['password']}"
        #                            )
        return connection
    
    except Exception as e:
        graba_log({"ret_code": -1, "ret_txt": "get_db_connection_sqlserver - "+ donde}, "Excepción", e)
        return False