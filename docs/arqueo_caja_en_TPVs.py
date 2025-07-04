from datetime import datetime, timedelta

import json

from app.models.mll_cfg import obtener_cfg_general, actualizar_en_ejecucion
from app.models.mll_cfg_bbdd import obtener_conexion_bbdd_origen
from app.config.db_mallorquina import get_db_connection_sqlserver, get_db_connection_mysql, close_connection_mysql
from app.services.auxiliares.sendgrid_service import enviar_email

from app.utils.mis_excepciones import MiException
from app.utils.utilidades import graba_log, imprime
from app.utils.InfoTransaccion import InfoTransaccion

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def proceso(param: InfoTransaccion) -> list:
    funcion = "arqueo_caja.proceso"
    param.debug="Inicio"
    resultado = []
    conn_mysql = None # para que no de error en el finally
    cursor_mysql = None # para que no de error en el finally
    fecha = param.parametros[0]

    try:
        config = obtener_cfg_general(param)
        
        if  not config.get("ID", False): 
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
        cursor_mysql.execute("SELECT * FROM mll_cfg_bbdd where cierre_caja = 'S'") 
        lista_bbdd = cursor_mysql.fetchall()

        for bbdd in lista_bbdd:
            imprime([f"📚 Procesando TIENDA: {bbdd['nombre']} - {json.loads(bbdd['Conexion'])['database']}"], "-")
            fechas = []
            if not fecha: # si no tiene parametro fecha
                # if bbdd['ultimo_cierre']: # si tiene último cierre
                #     fecha_inicial = datetime.strptime(bbdd['ultimo_cierre'].isoformat(), "%Y-%m-%d")
                #     fecha_final = datetime.now()
                #     imprime(["Uno:", type(bbdd['ultimo_cierre']),  bbdd['ultimo_cierre'], fecha_inicial, fecha_final], "=")
                # else:
                #     # Crear una lista de fechas
                #     fecha_inicial = datetime.strptime("2024-12-01", "%Y-%m-%d")
                #     fecha_final = datetime.now()
                #     imprime(["Dos:", fecha_inicial, fecha_final], "=")

                fecha_inicial = datetime.strptime("2024-12-01", "%Y-%m-%d")
                fecha_final = datetime.now()
                while fecha_inicial <= fecha_final:
                    fechas.append(fecha_inicial.strftime("%Y-%m-%d"))
                    fecha_inicial += timedelta(days=1)
            else:
                fechas = [fecha]


            # Aquí va la lógica específica para cada bbdd
            for fecha in fechas:
                print(fecha)
                resultado_dict = consultar_y_grabar(param, bbdd["ID"], conn_mysql, fecha)
                resultado.extend(resultado_dict)

            param.debug = "update"
            cursor_mysql.execute(
                "UPDATE mll_cfg_bbdd SET ultimo_cierre = %s WHERE ID = %s",
                (fecha, bbdd["ID"])
            )
        
        conn_mysql.commit()

        return resultado


    except Exception as e:
        param.error_sistema(e=e, debug="proceso.Exception")
        raise
        
    finally:
        close_connection_mysql(conn_mysql, cursor_mysql)

        actualizar_en_ejecucion(param, 0)
        enviar_email(config["Lista_emails"],
                     "Proceso finalizado",
                     "El proceso de sincronización ha terminado."
        )


#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def consultar_y_grabar(param: InfoTransaccion, id_bbdd, conn_mysql, fecha) -> dict:
    resultado = {}
    param.debug = "Inicio"

    try:
        param.debug = "Buscamos la conexión que necesitamos para esta bbdd origen"
        bbdd_config = obtener_conexion_bbdd_origen(conn_mysql,id_bbdd)

        param.debug = "conectamos con esta bbdd origen"
        conn_sqlserver = get_db_connection_sqlserver(param, bbdd_config)

        if conn_sqlserver:
            # Leer datos desde SQL Server
            cursor_sqlserver = conn_sqlserver.cursor()

            # Averiguamos los IDs de dia de cierre de caja:
            placeholders = "?"
            # en realidad parametros solo tiene un elemento que es la fecha y debe ser en formato aaaa-mm-dd
            select_query = f"""SELECT [Id Cierre]
                                FROM [Cierres de Caja] WHERE CAST(Fecha AS DATE) = ?
                    """
            param.debug = "Ejecución select 1"
            cursor_sqlserver.execute(select_query, fecha) #param.parametros) # parametros es la fecha
            apertura_ids_lista = cursor_sqlserver.fetchall()
            # imprime([apertura_ids_lista], "=")
            ids_cierre = [item[0] for item in apertura_ids_lista]
            
            if ids_cierre:
                # buscamos los cierres de estos IDs
                param.debug = "Ejecución select 2"
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

                param.debug = "Llamada a Grabar"
                resultado = grabar(param, conn_mysql, id_bbdd, datos, fecha)

        return resultado


    except Exception as e:
        param.error_sistema(e=e, debug="consultar_y_grabar.Exception")
        raise 

    finally:
        if conn_sqlserver:
            conn_sqlserver.close()

    

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def busca_tvp(param: InfoTransaccion, conn_mysql, id_tienda,  id_tpv) -> int:
    resultado = 0
    param.debug = "busca_tvp Inicio"

    try: 

        cursor_mysql = conn_mysql.cursor(dictionary=True)

        param.debug = "Select"
        # query = f"""SELECT mtpv.nombre, pf.* FROM mll_mae_tpv mtpv 
        #              inner join tpv_puestos_facturacion pf on mtpv.ID = pf.id_mae_tpv
        #              where pf.id_puesto={id_tpv}
        #                and pf.Origen_BBDD = {id_tienda}
        #          """
        query = f"""SELECT pf.id_mae_tpv FROM tpv_puestos_facturacion pf
                     where pf.id_puesto={id_tpv}
                       and pf.Origen_BBDD = {id_tienda}
                 """
        param.debug="execute del cursor"
        cursor_mysql.execute(query)
        datos = cursor_mysql.fetchall()
        if datos:
            # imprime([type(datos), datos], "=")
            param.debug= "en el FOR, solo debería tener un registro"
            resultado = datos[0]['id_mae_tpv']


    except Exception as e:
        param.error_sistema(e=e, debug="busca_tvp.Exception")
 

    finally:
        return resultado

    

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def grabar(param: InfoTransaccion, conn_mysql, id_bbdd, datos, fecha) -> dict:
    param.debug = "Inicio"
    resultado = None
    ventas_registros = 0
    total_ventas = 0
    total_operaciones = 0
    medios_pago_registros = 0

    try: 
        cierre_descs = ["Mañana", "Tarde"]
        cursor_mysql = conn_mysql.cursor()
        # Agrupar resultados por tienda, puesto y apertura
        ventas_diarias = {}
        for row in datos:
            id_puesto = row.ID_Puesto
            id_apertura = row.ID_Apertura
            fecha = row.Fecha

            # Clave única para agrupación
            key = (id_bbdd, id_puesto, id_apertura)

            if key not in ventas_diarias:
                ventas_diarias[key] = {
                    "id_tienda": id_bbdd,
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
            param.debug = "insert"
            ID_Apertura = key[2]
            # esto igual es mejor meterlo en un array todo y aquí buscar en el array
            id_mae_tpv = busca_tvp(param, conn_mysql, data["id_tienda"],  data["id_tpv"])

            insert_diarias = """
                INSERT INTO mll_rec_ventas_diarias (id_tienda, id_tpv, id_mae_tpv, fecha, ventas, operaciones, cierre_tpv_id, cierre_tpv_desc)
                VALUES (%s, %s, %s, STR_TO_DATE(%s, '%d/%m/%Y'), %s, %s, %s, %s)
            """
            cursor_mysql.execute( insert_diarias,
                                  (data["id_tienda"],
                                   data["id_tpv"],
                                   id_mae_tpv,
                                   data["fecha"],
                                   data["ventas"],
                                   data["operaciones"],
                                   ID_Apertura,
                                   cierre_descs[orden],
                                  )
                                )
            id_ventas_diarias = cursor_mysql.lastrowid  # Obtener el ID insertado

            ventas_registros  += cursor_mysql.rowcount
            total_ventas += data["ventas"]
            total_operaciones += data["operaciones"]

            # Insertar en mll_rec_ventas_medio_pago
            for detalle in data["detalles"]:
                if detalle.Importe != 0 or detalle.Operaciones != 0:
                    # clave = (ID_Apertura, data["fecha"], data["id_tpv"], data["id_tienda"], cierre_descs[orden])
                    # # Comprobamos si la clave existe en el diccionario
                    # if clave not in resultado:
                    #     # Creamos el registro si no existe
                    #     resultado[clave] = {"ID_Apertura": ID_Apertura, 
                    #                         "fecha": data["fecha"], 
                    #                         "id_tpv": data["id_tpv"], 
                    #                         "id_tienda": data["id_tienda"], 
                    #                         "orden": cierre_descs[orden],
                    #                         "ventas": float(detalle.Importe),
                    #                         "operaciones": int(detalle.Operaciones)
                    #                        }
                    #     # imprime(["0->"
                    #     #             , (resultado[clave]["ventas"])
                    #     #             , (resultado[clave]["operaciones"])
                    #     #            ]
                    #     #            ,'-')
                    # else:
                    #     # Incrementamos los valores existentes si la clave ya está
                    #     resultado[clave]["ventas"] = resultado[clave]["ventas"] + float(detalle.Importe)
                    #     resultado[clave]["operaciones"] += int(detalle.Operaciones)
                     
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
                    medios_pago_registros  += cursor_mysql.rowcount
               
        resultado = [f"para el {fecha} y tienda {id_bbdd}: se han creado {ventas_registros} regsitros de venta, con un total de {total_ventas}€ para {total_operaciones} operaciones. En Medios de pago se han creado {medios_pago_registros} registros"]
        return resultado

    except Exception as e:
        param.error_sistema(e=e, debug="grabar.Exception")
        raise 

