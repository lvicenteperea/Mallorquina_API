from fastapi import HTTPException
import mysql.connector 
from mysql.connector import Error
import json
from collections import defaultdict

from app.utils.InfoTransaccion import InfoTransaccion
from app.utils.functions import expande_lista
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
# Función para procesar los resultados en formato JSON
def procesar_a_json(resultados):
#----------------------------------------------------------------------------------------
    comunidades_dict = defaultdict(lambda: {"id": None, "nombre": "", "provincias": []})

    for row in resultados:
        id_comunidad = row["id_comunidad"]
        if comunidades_dict[id_comunidad]["id"] is None:
            comunidades_dict[id_comunidad]["id"] = id_comunidad
            comunidades_dict[id_comunidad]["nombre"] = row["nombre_comunidad"]
        
        provincia = {
            "id": row["id_provincia"],
            "nombre": row["nombre_provincia"]
        }
        comunidades_dict[id_comunidad]["provincias"].append(provincia)

    # Convertir el diccionario a la estructura JSON final
    comunidades_list = list(comunidades_dict.values())
    output_json = {"comunidades": comunidades_list}
    
    # Convertir a formato JSON y devolverlo
    return json.dumps(output_json, indent=4, ensure_ascii=False)





#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def ejec_select(query:str):
 
    connection = get_db_connection()
    

    try:
        cursor = connection.cursor(dictionary=True)  # Para obtener los resultados como diccionarios
        cursor.execute(query)
        resultado = cursor.fetchall()  # Obtener los resultados como lista de diccionarios

        return resultado
  
    except Exception as e:
        raise HTTPException(status_code=400, detail={"ret_code": -3,
                                                     "ret_txt": str(e),
                                                     "excepcion": e
                                                    }
                           )
    finally:
        cursor.close()
        get_db_close_connection(connection, cursor)