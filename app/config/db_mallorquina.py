# Para MySql
import mysql.connector
from mysql.connector import Error
from app.config.settings import settings

from app.utils.functions import graba_log, imprime
from app.utils.InfoTransaccion import InfoTransaccion

# Para SQL Server
import pyodbc


#----------------------------------------------------------------------------------------
def get_db_connection_mysql():
    param = InfoTransaccion(debug=f"Conectando con: {settings.MYSQL_DB_URL_MLL}/{settings.MYSQL_DB_USER_MLL}/{settings.MYSQL_DB_DATABASE_MLL}")
    try:
        connection = mysql.connector.connect(
            host=settings.MYSQL_DB_URL_MLL,
            user=settings.MYSQL_DB_USER_MLL,
            password= settings.MYSQL_DB_PWD_MLL,
            database=settings.MYSQL_DB_DATABASE_MLL
        )
        return connection
    
    except Exception as e:
        param.error_sistema()
        graba_log(param, "db_mallorquina.get_db_connection_mysql", e)
        raise

#----------------------------------------------------------------------------------------
def close_connection_mysql(conn, cursor):
    try:
        if conn is not None and conn.is_connected():
            if isinstance(cursor, mysql.connector.cursor.MySQLCursor):
                cursor.close()
            conn.close()
    
    except Error as e:
        raise 

#----------------------------------------------------------------------------------------
def get_db_connection_sqlserver(conexion_json):
    try:
        conexion = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={conexion_json['host']},{conexion_json['port']};DATABASE={conexion_json['database']};UID={conexion_json['user']};PWD={conexion_json['password']}"
        donde = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={conexion_json['host']};DATABASE={conexion_json['database']};UID={conexion_json['user']};PWD='XXXXXXX'"
        connection =  pyodbc.connect(conexion)

        return connection
    
    except Exception as e:
        graba_log({"ret_code": -1, "ret_txt": "get_db_connection_sqlserver - "+ donde}, "Excepción", e)
        return False
    
#----------------------------------------------------------------------------------------
def close_connection_sqlserver(conn, cursor):
    try:
        if conn is not None:
            if cursor is not None:
                cursor.close()
            conn.close()
    
    except Error as e:
        return

