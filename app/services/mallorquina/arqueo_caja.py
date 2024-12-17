from fastapi import HTTPException
from datetime import datetime
#from decimal import Decimal

import json

from app import mi_libreria as mi

from app.models.mll_cfg import obtener_configuracion_general, actualizar_en_ejecucion
from app.models.mll_cfg_bbdd import obtener_conexion_bbdd_origen
from app.config.db_mallorquina import get_db_connection_sqlserver, get_db_connection_mysql, close_connection_mysql
from app.services.auxiliares.sendgrid_service import enviar_email

from app.utils.functions import graba_log
from app.utils.mis_excepciones import MadreException
from app.utils.InfoTransaccion import InfoTransaccion

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def proceso(param: InfoTransaccion) -> InfoTransaccion:
    donde="Inicio"
    config = obtener_configuracion_general()
    param.resultados = []

    if not config.get("ID", False):
        param.ret_code = -11
        param.ret_txt = f"..No se han encontrado datos de configuración: {config['En_Ejecucion']}"
        raise MadreException({"ret_code": -1, 
                              "ret_txt": f"No se han encontrado datos de configuración: {config['En_Ejecucion']}"}, 
                              400)
    
    if config["En_Ejecucion"]:
        param.ret_code = -11
        param.ret_txt = "..El proceso ya está en ejecución."
        raise MadreException({"ret_code": -1, 
                              "ret_txt": "El proceso ya está en ejecución."}, 
                              400)

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
            if not param.parametros[0]: # si no tiene parametro fecha
                #mi.imprime([type(json.loads(bbdd['Conexion'])['ultimo_cierre'])],'.')
                if bbdd['ultimo_cierre']: # si tiene último cierre
                    param.parametros[0] = bbdd['ultimo_cierre']
                else:
                    param.parametros[0] = datetime.now().strftime('%Y-%m-%d')

            # Aquí va la lógica específica para cada bbdd
            param.resultados.extend(consultar_y_grabar(bbdd["ID"], conn_mysql, param))

            donde = "update"
            cursor_mysql.execute(
                "UPDATE mll_cfg_bbdd SET ultimo_cierre = %s WHERE ID = %s",
                (param.parametros[0], bbdd["ID"])
            )
        
        conn_mysql.commit()

        return param

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


#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def consultar_y_grabar(tabla, conn_mysql, param: InfoTransaccion) -> list:
    param.resultados = []

    try:
        # Buscamos la conexión que necesitamos para esta bbdd origen
        bbdd_config = obtener_conexion_bbdd_origen(conn_mysql,tabla)

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
            cursor_sqlserver.execute(select_query, param.parametros)
            apertura_ids_lista = cursor_sqlserver.fetchall()
            ids_cierre = [item[0] for item in apertura_ids_lista]
            
            if ids_cierre:
                # buscamos los cierres de estos IDs
                placeholders = ", ".join(["?"] * len(ids_cierre))
                select_query = f"""SELECT Ca.[Id Apertura Puesto Cobro] as ID_Apertura,
                                          FORMAT(Ca.Fecha, 'dd/MM/yyyy') as Fecha,
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
                                    group by Ca.[Id Apertura Puesto Cobro], FORMAT(Ca.Fecha, 'dd/MM/yyyy'),
                                             Ca.[Id Cobro],                 Ca.[Descripcion Cobro],
                                             AC.[Realizado],                AC.[Id Rel],
                                             CdC.[Id Puesto]
                        """
                cursor_sqlserver.execute(select_query, ids_cierre)
                datos = cursor_sqlserver.fetchall()

                param.resultados = grabar(param, conn_mysql, tabla, datos)
                if param.ret_code != 0:
                    mi.imprime(["resultado", param.resultados, param.ret_code, param.ret_txt], "-")

    except Exception as e:
        graba_log({"ret_code": -3, "ret_txt": "arqueo_caja.consultar_y_grabar"}, "Excepción", e)
        param.resultados = []
        param.ret_code = -1
        param.ret_txt = "Error General, contacte con su administrador"

    finally:
        if conn_sqlserver:
            conn_sqlserver.close()

        return param
    

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def grabar(param: InfoTransaccion, conn_mysql, tabla, datos) -> list:
    param.resultados = [0 , 0]
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
            
            param.resultados[0] = param.resultados[0] + float(ventas_diarias[key]["ventas"])
            param.resultados[1] += ventas_diarias[key]["operaciones"]

        orden = 1 # porque en la primera alteración quiero que sea 0
        # Insertar en mll_rec_ventas_diarias
        for idx, (key, data) in enumerate(ventas_diarias.items()):
            orden = orden ^ 1  # Alternar entre 0 y 1
            donde = "insert"
            
            insert_diarias = """
                INSERT INTO mll_rec_ventas_diarias (id_tienda, id_tpv, fecha, ventas, operaciones, cierre_tpv_id, cierre_tpv_desc)
                VALUES (%s, %s, STR_TO_DATE(%s, '%d/%m/%Y'), %s, %s, %s, %s)
            """
            cursor_mysql.execute(
                insert_diarias,
                (
                    data["id_tienda"],
                    data["id_tpv"],
                    data["fecha"],
                    data["ventas"],
                    data["operaciones"],
                    key[2],  # ID_Apertura
                    cierre_descs[orden],
                )
            )

            id_ventas_diarias = cursor_mysql.lastrowid  # Obtener el ID insertado

            # Insertar en mll_rec_ventas_medio_pago
            for detalle in data["detalles"]:
                if detalle.Importe != 0 or detalle.Operaciones != 0:
                    insert_medio_pago = """
                        INSERT INTO mll_rec_ventas_medio_pago (id_ventas_diarias, id_medios_pago, ventas, operaciones)
                        VALUES (%s, %s, %s, %s)
                    """
                    cursor_mysql.execute(insert_medio_pago,(
                                                            id_ventas_diarias,
                                                            detalle.ID_Cobro,
                                                            detalle.Importe,
                                                            detalle.Operaciones,
                                                        )
                                        )
        param.resultados[0] = float(param.resultados[0]) 

    except Exception as e:
        graba_log({"ret_code": -1, "ret_txt": "arqueo_caja.grabar - "+ donde}, "Excepción", e)
        param.resultados = [0 , 0]
        param.ret_code = -1
        param.ret_txt = "Error General, contacte con su administrador"

    finally:
        return param