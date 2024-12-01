from fastapi import HTTPException

# Para MySql
import mysql.connector
from mysql.connector import Error
from app.config.settings import settings

# Para SQL Server
import pyodbc


#----------------------------------------------------------------------------------------
def get_db_connection_mysql():
    try:
        connection = mysql.connector.connect(
            host=settings.MYSQL_DB_URL,
            user=settings.MYSQL_DB_USER,
            password=settings.MYSQL_DB_PWD,
            database=settings.MYSQL_DB_DATABASE
        )
        return connection
    
    except Error as e:
        raise HTTPException(status_code=400, detail= {"ret_code": -1,
                                                      "ret_txt": str(e),
                                                     }
                           )

#----------------------------------------------------------------------------------------
def close_connection_mysql(conn, cursor):
    try:
        if conn.is_connected():
            if isinstance(cursor, mysql.connector.cursor_cext.CMySQLCursor):
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
        connection =  pyodbc.connect(f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={conexion_json['host']};"
                                     f"DATABASE={conexion_json['database']};UID={conexion_json['user']};PWD={conexion_json['password']}"
                                    )
        return connection
    
    except Error as e:
        raise HTTPException(status_code=400, detail= {"ret_code": -1,
                                                      "ret_txt": str(e),
                                                     }
                           )