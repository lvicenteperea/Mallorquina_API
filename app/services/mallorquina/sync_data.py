from fastapi import HTTPException
import json
from collections import defaultdict
from datetime import datetime

from app.config.db_mallorquina import get_db_connection_mysql, close_connection_mysql
from app.models.mll_cfg import obtener_configuracion_general, actualizar_en_ejecucion
from app.services.mallorquina.sendgrid_service import enviar_email
from app.services.mallorquina.procesar_tabla import procesar_tabla

from app.utils.InfoTransaccion import InfoTransaccion
from app.utils.functions import expande_lista


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

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def recorre_tiendas(param: list) -> InfoTransaccion:
    # return call_proc_bbdd('w_exp_valida_url', param)
    config = obtener_configuracion_general()


    if not config.get("ID", False):
        print("No se han encontrado datos de configuración", config["En_Ejecucion"])
        return
    
    if config["En_Ejecucion"]:
        print("El proceso ya está en ejecución.")
        return

    actualizar_en_ejecucion(1)

    try:
        conn_mysql = get_db_connection_mysql()
        cursor_mysql = conn_mysql.cursor(dictionary=True)

        cursor_mysql.execute("SELECT * FROM mll_cfg_bbdd")
        lista_bbdd = cursor_mysql.fetchall()

        for bbdd in lista_bbdd:
                print("")
                print("---------------------------------------------------------------------------------------")
                print(f"Procesando TIENDA: {bbdd}")
                print("---------------------------------------------------------------------------------------")
                print("")

                # Aquí va la lógica específica para cada bbdd
                recorre_tablas(bbdd, conn_mysql)

                cursor_mysql.execute(
                    "UPDATE mll_cfg_bbdd SET Ultima_fecha_Carga = %s WHERE ID = %s",
                    (datetime.now(), bbdd["ID"])
                )
                conn_mysql.commit()


        """ 
            resultados = ejec_select(query)
            print("05")
            json_resultado = procesar_a_json(resultados)

            print("06")    
            print(type(resultados))
            print(type(json_resultado))
            return json_resultado
        """

    except Exception as e:
        raise HTTPException(status_code=400, detail={"ret_code": -3,
                                                     "ret_txt": str(e),
                                                     "excepcion": e
                                                    }
                           )        

    finally:
        close_connection_mysql(conn_mysql, cursor_mysql)

        actualizar_en_ejecucion(0)
        enviar_email(config["Lista_emails"],
                     "Proceso finalizado",
                     "El proceso de sincronización ha terminado."
        )


#----------------------------------------------------------------------------------------
# ejecutar_proceso: Sincroniza todas las tablas de una tienda. Recibe un json con los datos del registro de mll_cfg_bbdd:
#   - ID int: Es el ID de la tabla que vamos a tratar
#   - Nombre str: Es el nombre de la tienda
#   - Conexion str: es la conexión de la tienda en formato -->{"host": "ip", "port": "1433", "user": "usuario", "database": "nombre_database", "p a s  s w o  r d": "la_contraseña"}
#   - Ultima_Fecha_Carga str: fecha en la que se sincronizó la última vez

#----------------------------------------------------------------------------------------
def recorre_tablas(reg_cfg_bbdd, conn_mysql, param: list) -> InfoTransaccion:
#def procesar_BBDD():
    try:
        # conn_mysql = conexion_mysql("General")
        cursor_mysql = conn_mysql.cursor(dictionary=True)

        cursor_mysql.execute("SELECT * FROM mll_tablas_bbdd where id_bbdd = %s", (reg_cfg_bbdd["ID"],))
        tablas_bbdd = cursor_mysql.fetchall()

        for tabla in tablas_bbdd:
            ultima_actualizacion = tabla["Fecha_Ultima_Actualizacion"]
            intervalo = tabla["Cada_Cuanto_Ejecutar"]

            if (intervalo == 0 or (datetime.now() > ultima_actualizacion + timedelta(days=intervalo))):
                # print(f"Procesando tabla: {tabla['ID_Tabla']}")
                print("---------------------------------------------------------------------------------------")
                print(f"Procesando tabla: {tabla}")
                print("---------------------------------------------------------------------------------------")

                # Aquí va la lógica específica para cada tabla
                procesar_tabla(tabla, conn_mysql)

                cursor_mysql.execute(
                    "UPDATE mll_tablas_bbdd SET Fecha_Ultima_Actualizacion = %s WHERE ID = %s",
                    (datetime.now(), tabla["ID"])
                )
                conn_mysql.commit()
        
    except Exception as e:
        raise HTTPException(status_code=400, detail={"ret_code": -3,
                                                     "ret_txt": str(e),
                                                     "excepcion": e
                                                    }
                           )            
    finally:
        cursor_mysql.close()
