from fastapi import HTTPException
import mysql.connector
from mysql.connector import Error
import json

from app.config.settings import settings

#----------------------------------------------------------------------------------------
def get_db_connection():
#----------------------------------------------------------------------------------------
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
def get_db_close_connection(conn, cursor):
#----------------------------------------------------------------------------------------
    if conn.is_connected():
        if isinstance(cursor, mysql.connector.cursor_cext.CMySQLCursor):
            cursor.close()
        conn.close()




#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def call_proc_bbdd_param(procedimiento:str, param):
#----------------------------------------------------------------------------------------

    connection = get_db_connection()

    try:
        cursor = connection.cursor()
        response = cursor.callproc(procedimiento, param)

        return {"ret_code": response[0],
                "ret_txt": response[1],
                "datos": json.loads(response[3])
               }

    except Exception as e:
        raise HTTPException(status_code=400, detail={"ret_code": -3,
                                                     "ret_txt": str(e)
                                                    }
                           )
    finally:
        get_db_close_connection(connection, cursor)

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def call_proc_bbdd_records(procedimiento:str, ret_code:int = 0, ret_txt:str = 'OKdef'):
#----------------------------------------------------------------------------------------

    connection = get_db_connection()
    
    try:
        cursor = connection.cursor()
        response = cursor.callproc(procedimiento, [ret_code, ret_txt])
        
        if response[0] < 0:
            return {"ret_code": response[0],
                    "ret_txt": response[1],
                }

        # para convertirlo a JSON
        rows = []
        for result in cursor.stored_results():
            columns = [col[0] for col in result.description]  # Obtener nombres de las columnas
            rows = [dict(zip(columns, row)) for row in result.fetchall()]  # Convertir cada fila en un diccionario

        # Convertir la lista de diccionarios a JSON
        json_rows = json.dumps(rows)
        datos = json.loads(json_rows)

        return {"ret_code": response[0],
                "ret_txt": response[1],
                "datos": datos
               }

    except Exception as e:
        return {"ret_code": -3,
                "ret_txt": str(e),
               }

    finally:
        get_db_close_connection(connection, cursor)

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def valida_url_db(url:str, datos_str:str, ret_code:int = 0, ret_txt:str = 'OKdef'):
    return call_proc_bbdd_param('Valida_url', [ret_code, ret_txt, url, datos_str])


#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def obtener_lista_centros(ret_code:int = 0, ret_txt:str = 'OKdef'):
    return call_proc_bbdd_records('lista_centros', ret_code, ret_txt)

