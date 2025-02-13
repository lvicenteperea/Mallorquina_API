from datetime import datetime

import json
import pyodbc

from app.utils.functions import graba_log, row_to_dict, imprime
from app.models.mll_cfg_bbdd import obtener_conexion_bbdd_origen
from app.config.db_mallorquina import get_db_connection_mysql, close_connection_mysql, get_db_connection_sqlserver
from app.models.mll_cfg import obtener_cfg_general, actualizar_en_ejecucion
from app.services.auxiliares.sendgrid_service import enviar_email
from app.utils.InfoTransaccion import InfoTransaccion
from app.utils.mis_excepciones import MiException

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def recorre_consultas_tiendas(param: InfoTransaccion) -> list:
    funcion = "consulta.caja.recorre_consultas_tiendas"
    param.debug="Inicio"
    resultado = []
    conn_mysql = None # para que no de error en el finally
    cursor_mysql = None # para que no de error en el finally
    fecha = param.parametros[0]
    tienda = param.parametros[1]

    try:
        config = obtener_cfg_general(param)

        if not config.get("ID", False):
            param.registrar_error(ret_txt= f"No se han encontrado datos de configuración: {config['En_Ejecucion']}", debug=f"{funcion}.config-ID")
            raise MiException(param = param)
        
        if config["En_Ejecucion"]:
            param.registrar_error(ret_txt="El proceso ya está en ejecución.", debug=f"{funcion}.config.en_ejecucion")
            raise MiException(param = param)


        param.debug="actualizar_en_ejecucion"
        actualizar_en_ejecucion(param, 1)

        param.debug = "get_db_connection_mysql"
        conn_mysql = get_db_connection_mysql()
        cursor_mysql = conn_mysql.cursor(dictionary=True)

        param.debug = "Select"
        cursor_mysql.execute("""SELECT a.*, b.stIdEnt, b.Nombre as nombre_entidad FROM mll_cfg_bbdd a
                                 inner join mll_cfg_entidades b on a.id = b.id_bbdd and b.activo = 'S'
                                 where a.activo= 'S'
                                   and a.id = if( %s = 0 , a.id , %s)""", 
                             (tienda,tienda)
                            )
        lista_bbdd = cursor_mysql.fetchall()

        for bbdd in lista_bbdd:
            # Nombre_BBDD = f"{json.loads(bbdd['Conexion'])['database']} ({bbdd['ID']})"
            Nombre_BBDD = json.loads(bbdd['Conexion'])['database']
            id_bbdd = bbdd["ID"]
            imprime(["Procesando TIENDA:", Nombre_BBDD, id_bbdd, bbdd['stIdEnt'], bbdd['nombre_entidad']], "-")

            # Aquí va la lógica específica para cada bbdd
            resultado.extend( procesar_consulta(param, Nombre_BBDD, id_bbdd, fecha, bbdd['stIdEnt'], conn_mysql) )

            param.debug = "update"
            cursor_mysql.execute(
                "UPDATE mll_cfg_bbdd SET Ultima_fecha_Carga = %s WHERE ID = %s",
                (datetime.now(), bbdd["ID"])
            )
            conn_mysql.commit()

        return resultado 
       
    except Exception as e:
        param.error_sistema()
        graba_log(param, f"Excepción consulta_caja.recorre_consultas_tiendas-{param.debug}", e)
        raise

    finally:
        close_connection_mysql(conn_mysql, cursor_mysql)

        actualizar_en_ejecucion(param, 0)
        enviar_email(config["Lista_emails"],
                     "Proceso finalizado",
                     "El proceso de sincronización ha terminado."
        )

#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
def procesar_consulta(param: InfoTransaccion, Nombre_BBDD, id_BBDD, fecha, stIdEnt, conn_mysql) -> list:
    resultado = []
    param.debug = "Inicio"

    try:
        param.debug = "Con. BBDD Origen"
        # Buscamos la conexión que necesitamos para esta bbdd origen
        bbdd_config = obtener_conexion_bbdd_origen(conn_mysql, id_BBDD)

        param.debug = "Con. BBDD SqlServe"
        # conextamos con esta bbdd origen
        conn_sqlserver = get_db_connection_sqlserver(bbdd_config)

        if conn_sqlserver:
            # Leer datos desde SQL Server
            cursor_sqlserver = conn_sqlserver.cursor()

            # Averiguamos los IDs de dia de cierre de caja:
            placeholders = "?"
            # en realidad parametros solo tiene un elemento que es la fecha y debe ser en formato aaaa-mm-dd
            select_query = f"""SELECT [Id Cierre]
                                FROM [Cierres de Caja] WHERE CAST(Fecha AS DATE) = ?
                    """
            param.debug = "Execute cierres"
            cursor_sqlserver.execute(select_query, fecha)

            apertura_ids_lista = cursor_sqlserver.fetchall()
            ids_cierre = [item[0] for item in apertura_ids_lista]

            if ids_cierre:
                # buscamos los cierres de estos IDs
                placeholders = ", ".join(["?"] * len(ids_cierre))
                select_query = f"""SELECT AC.[Id Apertura] as ID_Apertura,
                                        AC.[Fecha Hora] as Fecha_Hora,
                                        AC.[Id Cobro] as ID_Cobro,
                                        AC.[Descripcion] as Medio_Cobro,
                                        AC.[Importe] as Importe,
                                        AC.[Realizado] as Realizado,
                                        AC.[Id Rel] as ID_Relacion,
                                        CdC.[Id Puesto] as ID_Puesto,
                                        PF.Descripcion as Puesto_Facturacion, 
                                        '{Nombre_BBDD}' as Nombre_BBDD,
                                        {id_BBDD} as ID_BBDD,
                                        '{stIdEnt}' as stIdEnt
                                    FROM [Arqueo Ciego] AC
                                    inner join [Cierres de Caja] CdC on CdC.[Id Cierre] = AC.[Id Apertura]
                                    inner join [Puestos Facturacion] PF on PF.[Id Puesto] = CdC.[Id Puesto]
                                    WHERE AC.[Id Apertura] IN ({placeholders})
                                    ORDER BY CdC.[Id Puesto], AC.[Fecha Hora]
                        """
                param.debug = "Execute arqueo"
                cursor_sqlserver.execute(select_query, ids_cierre)

                Lista_registros = cursor_sqlserver.fetchall()

                # if isinstance(Lista_registros, pyodbc.Row):
                #     if isinstance(row, pyodbc.Row):
                #         # Convertir pyodbc.Row a diccionario
                #         resultado[idx] = row_to_dict(row, cursor_sqlserver)  # Usa el cursor que generó la fila
                # elif isinstance(Lista_registros, list):
                for idx, row in enumerate(Lista_registros):
                    if isinstance(row, pyodbc.Row):
                        # Convertir pyodbc.Row a diccionario
                        resultado.append(row_to_dict(row, cursor_sqlserver))  # Usa el cursor que generó la fila
                
        param.debug = "Fin"
        return resultado

    except Exception as e:
        param.error_sistema()
        graba_log(param, f"Excepción tarifas_a_TPV.proceso-{param.debug}", e)
        raise

    finally:
        if conn_sqlserver:
            conn_sqlserver.close()
