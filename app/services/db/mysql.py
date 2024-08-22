import mysql.connector
from mysql.connector import Error
from app.config.settings import settings
import json

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=settings.MYSQL_DB_URL,
            user=settings.MYSQL_DB_USER,
            password=settings.MYSQL_DB_PWD,
            database=settings.MYSQL_DB_DATABASE
        )
        return connection
    
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def valida_url_db(ret_code, ret_txt:str, url:str, datos_str:str):
    connection = get_db_connection()
    if not connection:
        return None, "Error connecting to database"
    
    try:
        cursor = connection.cursor()
        response = cursor.callproc('Valida_url', [ret_code, ret_txt, url, datos_str])

        print("Ver datos: ", response[2])

        # si esperamos varios resultados
        # for result in cursor.stored_results():
            # response = result.fetchall()  es un array de dos dimensiones
            # si esperamos un resultado
            # response = result.fetchone()
        return {"codigo_error": response[0],
                "mensaje": response[1],
                "datos": dict(response[2])
               }

    except Exception as e:
        print(f"Error executing stored procedure: {e}")
        return None, str(e)
    
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
