# Para MySql
import mysql.connector
from mysql.connector import Error

# Para SQL Server
import pyodbc
import pymysql

from sshtunnel import SSHTunnelForwarder
import random

from app.config.settings import settings
from app.utils.utilidades import graba_log
from app.utils.InfoTransaccion import InfoTransaccion


#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def crea_tunel_ssh(param: InfoTransaccion):
    try:
        # Elegimos un puerto aleatorio disponible entre 10000 y 60000
        local_port = random.randint(20000, 60000)
        tunnel = SSHTunnelForwarder(
            (settings.SSH_HOST, settings.SSH_PORT),
            ssh_username=settings.SSH_USER,
            ssh_password=settings.SSH_KEY_PATH,
            remote_bind_address=(settings.MYSQL_DB_HOST, settings.MYSQL_DB_PORT),
            local_bind_address=('127.0.0.1', local_port)
        )
        tunnel.start()
        return tunnel, local_port
    
    except Exception as e:
        print(f"Error al abrir Túnel SSH 127.0.0.1:{e}")
        param.error_sistema(e=e, debug="db_clubo.crea_tunel_ssh")
        raise

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def get_db_connection_mysql():
    param = InfoTransaccion(debug=f"Conectando con: {settings.MYSQL_DB_HOST}/{settings.MYSQL_DB_PORT}/{settings.MYSQL_DB_USER}/{settings.MYSQL_DB_DATABASE}")
    connection = None
    tunnel = None
    
    try:
        if settings.SSH_CONEX:
            # Crear el túnel SSH
            tunnel, local_port = crea_tunel_ssh(param)
            
            # Pequeña pausa para asegurar que el túnel esté completamente establecido
            import time
            time.sleep(1)
            
            # Configuración de la conexión con mysql.connector
            connection = pymysql.connect(
                host='127.0.0.1',
                port=local_port,
                user=settings.MYSQL_DB_USER,
                password=settings.MYSQL_DB_PWD,
                database=settings.MYSQL_DB_DATABASE,
                charset='utf8mb4',
                connect_timeout=30,
                read_timeout=30,
                write_timeout=30
            )
        else:
            connection = pymysql.connect(
                host=settings.MYSQL_DB_HOST,
                port=settings.MYSQL_DB_PORT,
                user=settings.MYSQL_DB_USER,
                password=settings.MYSQL_DB_PWD,
                database=settings.MYSQL_DB_DATABASE,
                charset=settings.MYSQL_DB_CHARSET
            )

        return connection
    
    except mysql.connector.Error as mysql_err:
        if tunnel:
            tunnel.stop()
        param.error_sistema(e=mysql_err, debug="db_clubo.get_db_connection_mysql - MySQL Error")
        raise
    
    except Exception as e:
        if tunnel:
            tunnel.stop()
        param.error_sistema(e=e, debug="db_clubo.get_db_connection_mysql")
        raise

#----------------------------------------------------------------------------------------
def close_connection_mysql(conn, cursor, tunnel=None):
    mi_error = "close_connection_mysql"

    try:
        # Cerrar cursor
        if cursor:
            mi_error = "Cursor MySQL"
            cursor.close()

        # Cerrar conexión
        if conn:
            mi_error = "Conexión MySQL"
            conn.close()
    
        # Cerrar túnel SSH si se proporciona
        if tunnel:
            mi_error = "Tunel MySQL"
            tunnel.stop()

    except Exception as e:
        print(f"⚠️ Cerrando conexion ({mi_error}): {e}")
        pass


#----------------------------------------------------------------------------------------
def get_db_connection_sqlserver(param: InfoTransaccion, conexion_json):
    try:
        param.debug = "Inicio get_db_connection_sqlserver"
        conexion = f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={conexion_json['host']},{conexion_json['port']};DATABASE={conexion_json['database']};UID={conexion_json['user']};PWD={conexion_json['password']};TrustServerCertificate=yes;"
        param.debug =  f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={conexion_json['host']},{conexion_json['port']};DATABASE={conexion_json['database']};UID={conexion_json['user']};PWD=xxxxxxxx;TrustServerCertificate=yes;"
        connection =  pyodbc.connect(conexion)

        return connection
    
    except Exception as e:
        graba_log(param, "get_db_connection_sqlserver.Exception", e)
        return False
    
#----------------------------------------------------------------------------------------
def close_connection_sqlserver(param: InfoTransaccion, conn, cursor):
    try:
        if conn:
            if cursor:
                cursor.close()
            conn.close()
    
    except Error as e:
        return