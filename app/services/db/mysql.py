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
#----------------------------------------------------------------------------------------
def call_proc_bbdd(procedimiento:str, param) -> InfoTransaccion:
    
    connection = get_db_connection()
    
    try:
        # Crear una nueva lista para almacenar los elementos expandidos, ya que param debe trar un tipo InfoTransaccion
        param_expanded = expande_lista(param)

        cursor = connection.cursor()
        response = cursor.callproc(procedimiento, param_expanded)

        infoTrans = InfoTransaccion(id_App=response[0], 
                                    user=response[1], 
                                    ret_code=response[2], 
                                    ret_txt=response[3])

        if infoTrans.ret_code < 0:
            return infoTrans
    
        # Asignamos la lista de parametros que son del salida
        infoTrans.set_parametros(response[4:])

        # para convertirlo a JSON el posible record set retornado
        rows = []
        for result in cursor.stored_results():
            columns = [col[0] for col in result.description]  # Obtener nombres de las columnas
            rows = [
                    {col: (val if val is not None else "") for col, val in zip(columns, row)}
                    for row in result.fetchall()
                   ]  # Convertir cada fila en un diccionario, reemplazando None con ""

        # Convertir la lista de diccionarios a JSON
        json_rows = json.dumps(rows)
        infoTrans.set_resultados(json.loads(json_rows))

        return infoTrans

    except Exception as e:
        raise HTTPException(status_code=400, detail={"ret_code": -3,
                                                     "ret_txt": str(e),
                                                     "excepcion": e
                                                    }
                           )
    finally:
        get_db_close_connection(connection, cursor)






# Función para procesar los resultados en formato JSON
def procesar_a_json(resultados):
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
        get_db_close_connection(connection, cursor)



#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def obtener_cnt_exp_centros(param: list) -> InfoTransaccion:
    return call_proc_bbdd('w_cnt_exp_centros', param)


#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def comunidades_provincias_centros(param: list) -> InfoTransaccion:

    print("03")
    query = """
            SELECT 
                exp_centros.id_contenido,
                dir_provincias.id AS id_provincia,
                dir_provincias.nombre AS nombre_provincia,
                dir_comunidades.id AS id_comunidad,
                dir_comunidades.nombre AS nombre_comunidad
            FROM 
                exp_centros
            INNER JOIN 
                dir_provincias ON exp_centros.id_provincia = dir_provincias.id
                                AND dir_provincias.id_pais = 1
            INNER JOIN 
                dir_comunidades ON dir_provincias.id_comunidad = dir_comunidades.id;
            """
    print("04")
    resultados = ejec_select(query)

    print("05")
    json_resultado = procesar_a_json(resultados)

    print("06")    
    print(type(resultados))
    print(type(json_resultado))
    return json_resultado
