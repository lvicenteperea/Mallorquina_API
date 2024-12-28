from fastapi import HTTPException
from datetime import datetime
#from decimal import Decimal

import json

from app.models.mll_cfg import obtener_configuracion_general, actualizar_en_ejecucion
from app.models.mll_cfg_bbdd import obtener_conexion_bbdd_origen
from app.config.db_mallorquina import get_db_connection_sqlserver, get_db_connection_mysql, close_connection_mysql
from app.services.auxiliares.sendgrid_service import enviar_email

from app.utils.functions import graba_log, imprime
from app.utils.InfoTransaccion import InfoTransaccion

#----------------------------------------------------------------------------------------
'''
def proceso(param: InfoTransaccion) -> InfoTransaccion:
    donde="Inicio"
    config = obtener_configuracion_general()
    resultado = param
    resultado.resultados = []

    if not config.get("ID", False):
        resultado.ret_code = -1
        resultado.ret_txt = f"No se han encontrado datos de configuración: {config['En_Ejecucion']}"
        raise Exception
    
    if config["En_Ejecucion"]:
        resultado.ret_code = -1
        resultado.ret_txt = "El proceso ya está en ejecución."
        raise Exception

    donde="actualizar_en_ejecucion"
    actualizar_en_ejecucion(1)

    donde = "get_db_connection_mysql"
    try:
        conn_mysql = get_db_connection_mysql()
        cursor_mysql = conn_mysql.cursor(dictionary=True)

        donde = "Select"
        cursor_mysql.execute("SELECT * FROM mll_cfg_bbdd where activo= 'S'") 
        lista_bbdd = cursor_mysql.fetchall()

        for bbdd in lista_bbdd:
            mi.imprime([f"Procesando TIENDA: {json.loads(bbdd['Conexion'])['database']}"], "-")

            if not resultado.parametros[0]: # si no tiene parametro fecha
                #mi.imprime([type(json.loads(bbdd['Conexion'])['ultimo_cierre'])],'.')
                if bbdd['ultimo_cierre']: # si tiene último cierre
                    resultado.parametros[0] = bbdd['ultimo_cierre']
                else:
                    resultado.parametros[0] = datetime.now().strftime('%Y-%m-%d')

            # Aquí va la lógica específica para cada bbdd
            resultado.resultados.extend(consultar_y_grabar(bbdd["ID"], conn_mysql, resultado))

            donde = "update"
            cursor_mysql.execute(
                "UPDATE mll_cfg_bbdd SET ultimo_cierre = %s WHERE ID = %s",
                (param.parametros[0], bbdd["ID"])
            )
        
        conn_mysql.commit()

    except MadreException as e:
        param.resultados = []
        graba_log({"ret_code": -1, "ret_txt": f"{donde}"}, "MadreException mll_arqueo_caja", e)
        raise HTTPException(status_code=500, detail={"ret_code": param.ret_code,
                                                "ret_txt": param.ret_txt,
                                                "error": str(e)
                                            }
                           ) 
    except Exception as e:
        graba_log({"ret_code": -1, "ret_txt": f"{donde}"}, "Excepción arqueCaja.proceso", e)
        param.resultados = []
        param.ret_code = -1
        param.ret_txt = "Error General, contacte con su administrador"

    finally:
        close_connection_mysql(conn_mysql, cursor_mysql)

        actualizar_en_ejecucion(0)
        enviar_email(config["Lista_emails"],
                     "Proceso finalizado",
                     "El proceso de sincronización ha terminado."
        )

        return param


'''
#----------------------------------------------------------------------------------------
def proceso(param: InfoTransaccion) -> list:
    donde="Inicio"
    config = obtener_configuracion_general()
    resultado = []
    fecha = param.parametros[0]

    if not config.get("ID", False):
        param.ret_code = -1
        param.ret_txt = f"No se han encontrado datos de configuración: {config['En_Ejecucion']}"
        return
    
    if config["En_Ejecucion"]:
        param.ret_code = -1
        param.ret_txt = "El proceso ya está en ejecución."
        return

    donde="actualizar_en_ejecucion"
    actualizar_en_ejecucion(1)

    donde = "get_db_connection_mysql"
    try:
        conn_mysql = get_db_connection_mysql()
        cursor_mysql = conn_mysql.cursor(dictionary=True)

        donde = "Select"
        cursor_mysql.execute("SELECT * FROM mll_cfg_bbdd where activo= 'S'") 
        lista_bbdd = cursor_mysql.fetchall()

        for bbdd in lista_bbdd:
            imprime([f"Procesando TIENDA: {json.loads(bbdd['Conexion'])['database']}"], "-")

            if not fecha: # si no tiene parametro fecha
                #mi.imprime([type(json.loads(bbdd['Conexion'])['ultimo_cierre'])],'.')
                if bbdd['ultimo_cierre']: # si tiene último cierre
                    fecha = bbdd['ultimo_cierre']
                else:
                    fecha = datetime.now().strftime('%Y-%m-%d')

            # Aquí va la lógica específica para cada bbdd
            resultado_dict = consultar_y_grabar(param, bbdd["ID"], conn_mysql)
            resultado.append(resultado_dict)

            donde = "update"
            cursor_mysql.execute(
                "UPDATE mll_cfg_bbdd SET ultimo_cierre = %s WHERE ID = %s",
                (fecha, bbdd["ID"])
            )
        
        conn_mysql.commit()

    except Exception as e:
        graba_log({"ret_code": -1, "ret_txt": f"{donde}"}, "Excepción arqueCaja.proceso", e)
        resultado = []
        param.ret_code = -1
        param.ret_txt = "Error General, contacte con su administrador"
        raise

    finally:
        close_connection_mysql(conn_mysql, cursor_mysql)

        actualizar_en_ejecucion(0)
        enviar_email(config["Lista_emails"],
                     "Proceso finalizado",
                     "El proceso de sincronización ha terminado."
        )
        return resultado


#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def consultar_y_grabar(param: InfoTransaccion, tabla, conn_mysql) -> dict:
    resultado = {}
    donde = "Inicio"

    try:
        donde = "Buscamos la conexión que necesitamos para esta bbdd origen"
        bbdd_config = obtener_conexion_bbdd_origen(conn_mysql,tabla)

        donde = "conextamos con esta bbdd origen"
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
            donde = "Ejecución select 1"
            cursor_sqlserver.execute(select_query, param.parametros) # parametros es la fecha
            apertura_ids_lista = cursor_sqlserver.fetchall()
            ids_cierre = [item[0] for item in apertura_ids_lista]
            
            if ids_cierre:
                # buscamos los cierres de estos IDs
                donde = "Ejecución select 2"
                placeholders = ", ".join(["?"] * len(ids_cierre))
                select_query = f"""SELECT Ca.[Id Apertura Puesto Cobro] as ID_Apertura,
                                          -- FORMAT(Ca.Fecha, 'dd/MM/yyyy') as Fecha,
                                          FORMAT(AC.[Fecha Hora], 'dd/MM/yyyy') as Fecha,
                                          Ca.[Id Cobro] as ID_Cobro,
                                          Ca.[Descripcion Cobro] as Medio_Cobro,
                                          AC.[Realizado] as Realizado,
                                          AC.[Id Rel] as ID_Relacion,
                                          CdC.[Id Puesto] as ID_Puesto,
                                          sum(Ca.[Entrada]-Ca.[Salida]) as Importe,
                                          count(*) as Operaciones
                                     FROM Caja Ca
                                    inner join [Arqueo Ciego] AC on AC.[Id Apertura] = Ca.[Id Apertura Puesto Cobro] and ac.[Id Cobro] = ca.[Id Cobro]
                                    inner join [Cierres de Caja] CdC on CdC.[Id Cierre] = AC.[Id Apertura]
                                    WHERE Ca.[Id Apertura Puesto Cobro] IN ({placeholders})
                                    group by Ca.[Id Apertura Puesto Cobro], FORMAT(AC.[Fecha Hora], 'dd/MM/yyyy'),
                                             Ca.[Id Cobro],                 Ca.[Descripcion Cobro],
                                             AC.[Realizado],                AC.[Id Rel],
                                             CdC.[Id Puesto]
                        """
                cursor_sqlserver.execute(select_query, ids_cierre)
                datos = cursor_sqlserver.fetchall()

                donde = "Llamada a Grabar"
                resultado = grabar(param, conn_mysql, tabla, datos)

    except Exception as e:
        graba_log({"ret_code": -99, "ret_txt": donde}, "Excepción arqueo_caja.consultar_y_grabar", e)
        resultado = {}
        param.ret_code = -99
        param.ret_txt = "Error General, contacte con su administrador"
        raise

    finally:
        if conn_sqlserver:
            conn_sqlserver.close()

        return resultado
    

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def grabar(param: InfoTransaccion, conn_mysql, tabla, datos) -> dict:
    resultado = {}
    donde = "Inicio"

    try: 
        cierre_descs = ["Mañana", "Tarde"]
        cursor_mysql = conn_mysql.cursor()
        # Agrupar resultados por tienda, puesto y apertura
        ventas_diarias = {}
        for row in datos:
            id_tienda = tabla
            id_puesto = row.ID_Puesto
            id_apertura = row.ID_Apertura
            fecha = row.Fecha

            # Clave única para agrupación
            key = (id_tienda, id_puesto, id_apertura)

            if key not in ventas_diarias:
                ventas_diarias[key] = {
                    "id_tienda": id_tienda,
                    "id_tpv": id_puesto,
                    "fecha": fecha,
                    "ventas": 0,
                    "operaciones": 0,
                    "detalles": [],
                }

            ventas_diarias[key]["ventas"] += row.Importe
            ventas_diarias[key]["operaciones"] += row.Operaciones
            ventas_diarias[key]["detalles"].append(row)
            

        orden = 1 # porque en la primera alteración quiero que sea 0
        # Insertar en mll_rec_ventas_diarias
        for idx, (key, data) in enumerate(ventas_diarias.items()):
            orden = orden ^ 1  # Alternar entre 0 y 1
            donde = "insert"
            ID_Apertura = key[2]

            insert_diarias = """
                INSERT INTO mll_rec_ventas_diarias (id_tienda, id_tpv, fecha, ventas, operaciones, cierre_tpv_id, cierre_tpv_desc)
                VALUES (%s, %s, STR_TO_DATE(%s, '%d/%m/%Y'), %s, %s, %s, %s)
            """
            cursor_mysql.execute( insert_diarias,
                                  (data["id_tienda"],
                                   data["id_tpv"],
                                   data["fecha"],
                                   data["ventas"],
                                   data["operaciones"],
                                   ID_Apertura,
                                   cierre_descs[orden],
                                  )
                                )

            id_ventas_diarias = cursor_mysql.lastrowid  # Obtener el ID insertado

            # Insertar en mll_rec_ventas_medio_pago
            for detalle in data["detalles"]:
                if detalle.Importe != 0 or detalle.Operaciones != 0:
                    clave = (ID_Apertura, data["fecha"], data["id_tpv"], data["id_tienda"], cierre_descs[orden])

                    # Comprobamos si la clave existe en el diccionario
                    if clave not in resultado:
                        # Creamos el registro si no existe
                        resultado[clave] = {
                            "ventas": float(detalle.Importe),
                            "operaciones": int(detalle.Operaciones)
                        }
                        imprime(["0->"
                                    , (resultado[clave]["ventas"])
                                    , (resultado[clave]["operaciones"])
                                   ]
                                   ,'-')
                    else:
                        # Incrementamos los valores existentes si la clave ya está
                        resultado[clave]["ventas"] = resultado[clave]["ventas"] + float(detalle.Importe)
                        resultado[clave]["operaciones"] += int(detalle.Operaciones)
 
                    
                    insert_medio_pago = """
                        INSERT INTO mll_rec_ventas_medio_pago (id_ventas_diarias, id_medios_pago, ventas, operaciones)
                        VALUES (%s, %s, %s, %s)
                    """
                    cursor_mysql.execute(insert_medio_pago,(id_ventas_diarias,
                                                            detalle.ID_Cobro,
                                                            detalle.Importe,
                                                            detalle.Operaciones,
                                                           )
                                        )

    except Exception as e:
        graba_log({"ret_code": -1, "ret_txt": donde}, "Excepción arqueo_caja.grabar", e)
        resultado = [0 , 0]
        param.ret_code = -99
        param.ret_txt = "Error General, contacte con su administrador"
        raise

    finally:
        return resultado