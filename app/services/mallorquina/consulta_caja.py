from fastapi import HTTPException
from datetime import datetime

import json
import pyodbc

from app.utils.functions import graba_log, row_to_dict, imprime
from app.models.mll_cfg_bbdd import obtener_conexion_bbdd_origen
from app.config.db_mallorquina import get_db_connection_mysql, close_connection_mysql, get_db_connection_sqlserver
from app.models.mll_cfg import obtener_configuracion_general, actualizar_en_ejecucion
from app.services.auxiliares.sendgrid_service import enviar_email
from app.utils.InfoTransaccion import InfoTransaccion
from app.utils.mis_excepciones import MadreException

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def recorre_consultas_tiendas(param: InfoTransaccion) -> list:
    funcion = "consulta.caja.recorre_consultas_tiendas"
    param.debug="Inicio"

    config = obtener_configuracion_general()
    resultado = []
    conn_mysql = None # para que no de error en el finally
    cursor_mysql = None # para que no de error en el finally

    try:
        if not config.get("ID", False):
            param.registrar_error(-1, f"No se han encontrado datos de configuración: {config['En_Ejecucion']}", f"{funcion}.config-ID")
            raise MadreException(param = param)
        
        if config["En_Ejecucion"]:
            param.registrar_error(-1, "El proceso ya está en ejecución.", f"{funcion}.config.en_ejecucion")
            raise MadreException(param = param)


        donde="actualizar_en_ejecucion"
        actualizar_en_ejecucion(1)

        donde = "get_db_connection_mysql"
        conn_mysql = get_db_connection_mysql()
        cursor_mysql = conn_mysql.cursor(dictionary=True)

        donde = "Select"
        cursor_mysql.execute("SELECT * FROM mll_cfg_bbdd where activo= 'S'")
        lista_bbdd = cursor_mysql.fetchall()

        for bbdd in lista_bbdd:
            imprime(["Procesando TIENDA:", json.loads(bbdd['Conexion'])['database']], "-")

            # Aquí va la lógica específica para cada bbdd
            resultado.extend(procesar_consulta(param, bbdd["ID"], conn_mysql))

            donde = "update"
            cursor_mysql.execute(
                "UPDATE mll_cfg_bbdd SET Ultima_fecha_Carga = %s WHERE ID = %s",
                (datetime.now(), bbdd["ID"])
            )
            conn_mysql.commit()

        return resultado 
       
    except Exception as e:
        param.error_sistema()
        graba_log({"ret_code": param.ret_code, "ret_txt": param.ret_txt}, f"Excepción consulta_caja.recorre_consultas_tiendas-{donde}", e)
        raise

    finally:
        close_connection_mysql(conn_mysql, cursor_mysql)

        actualizar_en_ejecucion(0)
        enviar_email(config["Lista_emails"],
                     "Proceso finalizado",
                     "El proceso de sincronización ha terminado."
        )

#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
def procesar_consulta(param: InfoTransaccion, tabla, conn_mysql) -> list:
    resultado = []
    donde = "Inicio"

    try:
        donde = "Con. BBDD Origen"
        # Buscamos la conexión que necesitamos para esta bbdd origen
        bbdd_config = obtener_conexion_bbdd_origen(conn_mysql,tabla)

        donde = "Con. BBDD SqlServe"
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
            donde = "Execute cierres"
            cursor_sqlserver.execute(select_query, param.parametros)

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
                                        {tabla}
                                    FROM [Arqueo Ciego] AC
                                    inner join [Cierres de Caja] CdC on CdC.[Id Cierre] = AC.[Id Apertura]
                                    inner join [Puestos Facturacion] PF on PF.[Id Puesto] = CdC.[Id Puesto]
                                    WHERE AC.[Id Apertura] IN ({placeholders})
                                    ORDER BY CdC.[Id Puesto], AC.[Fecha Hora]
                        """
                donde = "Execute arqueo"
                cursor_sqlserver.execute(select_query, ids_cierre)

                resultado = cursor_sqlserver.fetchall()
                if isinstance(resultado, pyodbc.Row):
                    if isinstance(row, pyodbc.Row):
                        # Convertir pyodbc.Row a diccionario
                        resultado[idx] = row_to_dict(row, cursor_sqlserver)  # Usa el cursor que generó la fila
                elif isinstance(resultado, list):
                    for idx, row in enumerate(resultado):
                        # print(f"Fila {idx}: {type(row)}")  # Imprimir el tipo de cada fila

                        if isinstance(row, pyodbc.Row):
                            # print("Convertir pyodbc.Row a diccionario")
                            resultado[idx] = row_to_dict(row, cursor_sqlserver)  # Usa el cursor que generó la fila

        donde = "Fin"
        return resultado

    except Exception as e:
        param.error_sistema()
        graba_log({"ret_code": param.ret_code, "ret_txt": param.ret_txt}, f"Excepción tarifas_a_TPV.proceso-{donde}", e)
        raise

    finally:
        if conn_sqlserver:
            conn_sqlserver.close()
