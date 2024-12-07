from fastapi import HTTPException
import json
from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from app.models.mll_cfg_bbdd import obtener_conexion_bbdd_origen
from app.config.db_mallorquina import get_db_connection_mysql, close_connection_mysql, get_db_connection_sqlserver
from app.models.mll_cfg import obtener_configuracion_general, actualizar_en_ejecucion
from app.services.mallorquina.sendgrid_service import enviar_email
from app.services.mallorquina.procesar_tabla import procesar_tabla
from app.services.mallorquina.procesar_consulta import procesar_consulta

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

#----------------------------------------------------------------------------------------
# Función para procesar los resultados en formato JSON
#     data = [
#         (8285, datetime(2024, 10, 5, 14, 7, 20), 13, 'CREDITO CLIENTE', Decimal('0.000'), True, 39151),
#         (8286, datetime(2024, 10, 5, 13, 48, 40), 13, 'CREDITO CLIENTE', Decimal('0.000'), True, 39142),
#         (8287, datetime(2024, 10, 5, 21, 21, 6), 13, 'CREDITO CLIENTE', Decimal('0.000'), True, 39169),
#         (8288, datetime(2024, 10, 5, 21, 9, 13), 13, 'CREDITO CLIENTE', Decimal('0.000'), True, 39160),
#     ]
#----------------------------------------------------------------------------------------
def lista_arqueo_caja_a_json(data):
    # Claves descriptivas para los campos de las tuplas
    keys = ["Id", "Fecha", "Tipo", "Descripcion", "Monto", "Activo", "Codigo"]

    # Función personalizada para serializar Decimal y datetime
    def custom_serializer(obj):
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, bool):
            return obj
        raise TypeError(f"Tipo no serializable: {type(obj)}")

    # Convertir la lista de tuplas a una lista de diccionarios
    dict_data = [dict(zip(keys, row)) for row in data]

    # Convertir a JSON
    return json.dumps(dict_data, default=custom_serializer, indent=4)

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def ejec_select(query:str):
 
    connection = get_db_connection_mysql()
    

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
        close_connection_mysql(connection, cursor)

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def ejec_select_sql_server(query:str):
 
    # Buscamos la conexión que necesitamos para esta bbdd origen
    bbdd_config = obtener_conexion_bbdd_origen(conn_mysql, tabla["ID_BBDD"])

    # conextamos con esta bbdd origen
    conn_sqlserver = get_db_connection_sqlserver(bbdd_config)

    try:
        cursor_sqlserver = conn_sqlserver.cursor()
        cursor_sqlserver.execute(query)
        resultado = cursor_sqlserver.fetchall()  # Obtener los resultados como lista de diccionarios

        return resultado
  
    except Exception as e:
        raise HTTPException(status_code=400, detail={"ret_code": -3,
                                                     "ret_txt": str(e),
                                                     "excepcion": e
                                                    }
                           )
    finally:
        conn_sqlserver.close()



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
                recorre_tablas(bbdd, conn_mysql,[])

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
                print(f"Procesando tabla: {tabla}")

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



#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def recorre_consultas_tiendas(param: list) -> InfoTransaccion:
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
                recorrer_consultas(bbdd, conn_mysql,[])

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
#----------------------------------------------------------------------------------------
def recorrer_consultas(reg_cfg_bbdd, conn_mysql, param: list) -> InfoTransaccion:

    try:
        cursor_mysql = conn_mysql.cursor(dictionary=True)

        # cursor_mysql.execute("SELECT * FROM mll_tablas_bbdd where id_bbdd = %s", (reg_cfg_bbdd["ID"],))
        # tablas_bbdd = cursor_mysql.fetchall()

        # for tabla in tablas_bbdd:
        tabla={'ID': 11, 'ID_BBDD': reg_cfg_bbdd["ID"], 'ID_Tabla': 1, 'TABLA': "arqueo_caja"}
        # ultima_actualizacion = tabla["Fecha_Ultima_Actualizacion"]
        # intervalo = tabla["Cada_Cuanto_Ejecutar"]

        # if (intervalo == 0 or (datetime.now() > ultima_actualizacion + timedelta(days=intervalo))):
        print(f"Tratando tabla: {tabla}")

        # Aquí va la lógica específica para cada tabla
        resultados = procesar_consulta(tabla, conn_mysql)

        # cursor_mysql.execute(
        #     "UPDATE mll_tablas_bbdd SET Fecha_Ultima_Actualizacion = %s WHERE ID = %s",
        #     (datetime.now(), tabla["ID"])
        # )
        # conn_mysql.commit()
        # FIN IF comentado
        # FIN FOR comentado


        print("tipo resultados: ", type(resultados))
        print (resultados) # return json_resultado
        
        json_resultado = lista_arqueo_caja_a_json(resultados)

        print("tipo json_resultado: ", type(json_resultado))
        print (json_resultado) # return json_resultado
        
    
    except Exception as e:
        raise HTTPException(status_code=400, detail={"ret_code": -3,
                                                     "ret_txt": str(e),
                                                     "excepcion": e
                                                    }
                           )            
    finally:
        cursor_mysql.close()

