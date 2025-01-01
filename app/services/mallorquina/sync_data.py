from fastapi import HTTPException
from datetime import datetime, timedelta
import json

from app.utils.functions import graba_log, imprime

from app.models.mll_cfg_tablas import obtener_campos_tabla, crear_tabla_destino
from app.models.mll_cfg_bbdd import obtener_conexion_bbdd_origen
from app.config.db_mallorquina import get_db_connection_mysql, close_connection_mysql, get_db_connection_sqlserver, close_connection_sqlserver
from app.models.mll_cfg import obtener_configuracion_general, actualizar_en_ejecucion
from app.services.auxiliares.sendgrid_service import enviar_email

from app.utils.InfoTransaccion import InfoTransaccion
from app.utils.mis_excepciones import MadreException

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def recorre_tiendas(param: InfoTransaccion) -> list:
    funcion = "arqueo_caja.proceso"
    param.debug = "Obtener Conf. Gen"
    config = obtener_configuracion_general()
    resultado = []
    conn_mysql = None # para que no de error en el finally
    cursor_mysql = None # para que no de error en el finally

    try:

        if not config.get("ID", False):
            param.registrar_error(-1, f'No se han encontrado datos de configuración: config["En_Ejecucion"]', f"{funcion}.config-ID")
            raise MadreException(param = param)
                
        if config["En_Ejecucion"]:
                param.registrar_error(-1, "El proceso ya está en ejecución.", f"{funcion}.config.en_ejecucion")
                raise MadreException(param = param)

        param.debug = "actualiza ejec 1"
        actualizar_en_ejecucion(1)

        param.debug = "conn. MySql"
        conn_mysql = get_db_connection_mysql()
        cursor_mysql = conn_mysql.cursor(dictionary=True)

        param.debug = "execute cfg_bbdd"
        cursor_mysql.execute("SELECT * FROM mll_cfg_bbdd where activo= 'S'")
        lista_bbdd = cursor_mysql.fetchall()

        for bbdd in lista_bbdd:
            imprime(["Procesando TIENDA:", json.loads(bbdd['Conexion'])['database']], "-")

            param.debug = "por tablas"
            # Aquí va la lógica específica para cada bbdd
            recorre_tablas(param, bbdd, conn_mysql)
            resultado.append(json.loads(bbdd['Conexion'])['database'])

            param.debug = "execute act. fec_Carga"
            cursor_mysql.execute(
                "UPDATE mll_cfg_bbdd SET Ultima_fecha_Carga = %s WHERE ID = %s",
                (datetime.now(), bbdd["ID"])
            )
        
        conn_mysql.commit()

        param.debug = "Fin"
        return resultado

    except MadreException as e:
        raise
                    
    except HTTPException as e:
        param.error_sistema()
        graba_log(param, "recorre_tiendas.HTTPException", e)
        raise

    except Exception as e:
        param.error_sistema()
        graba_log(param, "recorre_tiendas.Exception", e)
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    finally:
        param.debug = "cierra conn"
        close_connection_mysql(conn_mysql, cursor_mysql)

        param.debug = "Actualiza Ejec 0"
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
def recorre_tablas(param: InfoTransaccion, reg_cfg_bbdd, conn_mysql) -> list:

    try:
        param.debug = "Inicio"
        cursor_mysql = conn_mysql.cursor(dictionary=True)

        param.debug = "execute cfg_tablas"
        cursor_mysql.execute("SELECT * FROM mll_cfg_tablas_bbdd where id_bbdd = %s", (reg_cfg_bbdd["ID"],))
        tablas_bbdd = cursor_mysql.fetchall()

        for tabla in tablas_bbdd:
            ultima_actualizacion = tabla["Fecha_Ultima_Actualizacion"]
            intervalo = tabla["Cada_Cuanto_Ejecutar"]

            if (intervalo == 0 or (datetime.now() > ultima_actualizacion + timedelta(days=intervalo))):
                param.debug = f"Procesando tabla: {tabla}"
                # Aquí va la lógica específica para cada tabla
                procesar_tabla(param, tabla, conn_mysql)

                param.debug = "Execute fec_ult_act"
                cursor_mysql.execute(
                    "UPDATE mll_cfg_tablas_bbdd SET Fecha_Ultima_Actualizacion = %s WHERE ID = %s",
                    (datetime.now(), tabla["ID"])
                )
                conn_mysql.commit()
        
        return []

    except MadreException as e:
        raise
                    
    except HTTPException as e:
        param.error_sistema()
        graba_log(param, "recorre_tablas.HTTPException", e)
        raise

    except Exception as e:
        param.error_sistema()
        graba_log(param, "recorre_tablas.Exception", e)
        raise HTTPException(status_code=e.status_code, detail=e.detail)  
            
    finally:
        param.debug = "Cierra Cursor"
        cursor_mysql.close()



#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def procesar_tabla(param: InfoTransaccion, tabla, conn_mysql):
    funcion = "sync_data.procesar_tabla"
    param.debug="Inicio"
    cursor_mysql = None # para que no de error en el finally
    conn_sqlserver = None # para que no de error en el finally
    cursor_sqlserver = None # para que no de error en el finally

    try:
        param.debug = "Obtener cursor"
        # Obtener configuración y campos necesarios
        cursor_mysql = conn_mysql.cursor(dictionary=True)
        
        param.debug = "Select cfg_tablas"
        # Obtener nombre de la tabla y si se debe borrar
        cursor_mysql.execute("SELECT * FROM mll_cfg_tablas WHERE ID = %s", (tabla["ID_Tabla"],))

        tabla_config = cursor_mysql.fetchone()
        nombre_tabla = tabla_config["Tabla_Origen"]
        nombre_tabla_destino = tabla_config["Tabla_Destino"]
        # borrar_tabla = tabla_config["Borrar_Tabla"]
        cursor_mysql.close()

        param.debug = "obtener campos"
        # Obtener campos de la tabla
        campos = obtener_campos_tabla(conn_mysql, tabla["ID_Tabla"])

        param.debug = "crea_tabla_dest"
        # Crear tabla si no existe
        crear_tabla_destino(conn_mysql, nombre_tabla_destino, campos)

        param.debug = "obt. Origen"
        # Buscamos la conexión que necesitamos para esta bbdd origen
        bbdd_config = obtener_conexion_bbdd_origen(conn_mysql,tabla["ID_BBDD"])

        param.debug = "conn origen"
        # conextamos con esta bbdd origen
        conn_sqlserver = get_db_connection_sqlserver(bbdd_config)

        # Leer datos desde SQL Server
        cursor_sqlserver = conn_sqlserver.cursor()
        select_query = f"SELECT {', '.join([campo['Nombre'] for campo in campos])} FROM {nombre_tabla}"
        cursor_sqlserver.execute(select_query)
        registros = cursor_sqlserver.fetchall()
        cursor_sqlserver.close()
        cursor_sqlserver = None

        # Preparar los cursores para MySQL
        cursor_mysql = conn_mysql.cursor()
        columnas_mysql = [campo["Nombre_Destino"] for campo in campos] + ["Origen_BBDD"]

        # Identificar el campo PK basado en mll_cfg_campos
        pk_campos = [campo for campo in campos if campo.get("PK", 0) >= 1]
        if not pk_campos:
            raise ValueError(f"No se encontró ningún campo PK en {nombre_tabla}.")

        # Usamos el primer campo PK encontrado
        pk_campo = pk_campos[0]["Nombre_Destino"]

        # Generar consultas dinámicas
        insert_query = f"""
            INSERT INTO {nombre_tabla_destino} ({', '.join(columnas_mysql)})
            VALUES ({', '.join(['%s'] * len(columnas_mysql))})
        """
        campos_update = [campo for campo in campos if campo["Nombre_Destino"] != pk_campo]
        update_query = f"""
            UPDATE {nombre_tabla_destino}
            SET {', '.join([f'{campo["Nombre_Destino"]} = %s' for campo in campos_update])}
            WHERE {pk_campo} = %s AND Origen_BBDD = %s
        """

        for registro in registros:
            # Obtener el valor del campo PK desde el registro
            pk_index = [campo["Nombre"] for campo in campos].index(pk_campos[0]["Nombre"])
            pk_value = registro[pk_index]

            select = f"""SELECT COUNT(*) 
                                       FROM {nombre_tabla_destino} 
                                      WHERE {pk_campo} = %s
                                        AND Origen_BBDD = {tabla["ID_BBDD"]}"""

            # Comprobar si el registro ya existe en la tabla destino
            cursor_mysql.execute(select, (pk_value,))
            existe = cursor_mysql.fetchone()[0] > 0  # Si existe, devuelve True

            if existe:
                # Realizar un UPDATE
                valores_update = list(registro) + [tabla["ID_BBDD"], pk_value]  # Campos + Origen + PK
                valores_update = [registro[[campo["Nombre"] for campo in campos].index(campo["Nombre"])]
                                            for campo in campos_update] + [pk_value, tabla["ID_BBDD"]]
                cursor_mysql.execute(update_query, valores_update)
            else:
                # Realizar un INSERT
                registro_destino = list(registro) + [tabla["ID_BBDD"]]  # Campos + Origen
                cursor_mysql.execute(insert_query, registro_destino)

        conn_mysql.commit()

        return []

    except MadreException as e:
        raise
                    
    except HTTPException as e:
        param.error_sistema()
        graba_log(param, "procesar_tabla.HTTPException", e)
        raise

    except Exception as e:
        param.error_sistema()
        graba_log(param, "procesar_tabla.Exception", e)
        raise HTTPException(status_code=e.status_code, detail=e.detail)   

    finally:
        param.debug = "cierra conexión sqlserver"
        close_connection_sqlserver(conn_sqlserver, cursor_sqlserver)

