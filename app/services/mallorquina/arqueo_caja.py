from fastapi import HTTPException
from datetime import datetime

from app.utils.functions import graba_log
import json

from app.models.mll_cfg import obtener_configuracion_general, actualizar_en_ejecucion
from app.models.mll_cfg_bbdd import obtener_conexion_bbdd_origen
from app.config.db_mallorquina import get_db_connection_sqlserver, get_db_connection_mysql, close_connection_mysql
from app.services.mallorquina.sendgrid_service import enviar_email
from app.services.mallorquina.procesar_consulta import procesar_consulta

from app.utils.InfoTransaccion import InfoTransaccion


#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def proceso(param: InfoTransaccion) -> InfoTransaccion:
    donde="Inicio"
    config = obtener_configuracion_general()

    if not config.get("ID", False):
        print("No se han encontrado datos de configuración", config["En_Ejecucion"])
        return
    
    if config["En_Ejecucion"]:
        print("El proceso ya está en ejecución.")
        return

    donde="actualizar_en_ejecucion"
    actualizar_en_ejecucion(1)

    try:
        donde = "get_db_connection_mysql"
        conn_mysql = get_db_connection_mysql()
        cursor_mysql = conn_mysql.cursor(dictionary=True)

        donde = "Select"
        cursor_mysql.execute("SELECT * FROM mll_cfg_bbdd") # where id=1")
        lista_bbdd = cursor_mysql.fetchall()
        resultado = []

        for bbdd in lista_bbdd:
            print("")
            print("---------------------------------------------------------------------------------------")
            print(f"Procesando TIENDA: {json.loads(bbdd['Conexion'])['database']}")
            print("---------------------------------------------------------------------------------------")
            print("")

            # Aquí va la lógica específica para cada bbdd
            resultado.extend(consultar_y_grabar(bbdd["ID"], conn_mysql, param))

            donde = "update"
            cursor_mysql.execute(
                "UPDATE mll_cfg_bbdd SET Ultima_fecha_Carga = %s WHERE ID = %s",
                (datetime.now(), bbdd["ID"])
            )
        
        conn_mysql.commit()

        return InfoTransaccion( id_App=param.id_App, 
                                user=param.user, 
                                ret_code=0, 
                                ret_txt="",
                                parametros=param.parametros,
                                resultados = []
                              )

    except Exception as e:
        graba_log({"ret_code": -1, "ret_txt": f"{donde}"},
                   "Excepción arqueCaja.proceso", e)
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
def consultar_y_grabar(tabla, conn_mysql, param) -> list:
    resultado = []

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
                select_query = f"""SELECT AC.[Id Apertura] as ID_Apertura,
                                        AC.[Fecha Hora] as Fecha_Hora,
                                        AC.[Id Cobro] as ID_Cobro,
                                        AC.[Descripcion] as Medio_Cobro,
                                        AC.[Importe] as Importe,
                                        AC.[Realizado] as Realizado,
                                        AC.[Id Rel] as ID_Relacion,
                                        CdC.[Id Puesto] as ID_Puesto,
                                        PF.Descripcion as Puesto_Facturacion, 
                                        {tabla} as tienda
                                    FROM [Arqueo Ciego] AC
                                    inner join [Cierres de Caja] CdC on CdC.[Id Cierre] = AC.[Id Apertura]
                                    inner join [Puestos Facturacion] PF on PF.[Id Puesto] = CdC.[Id Puesto]
                                    WHERE AC.[Id Apertura] IN ({placeholders})
                                    ORDER BY CdC.[Id Puesto], AC.[Fecha Hora]
                        """
                cursor_sqlserver.execute(select_query, ids_cierre)
                datos = cursor_sqlserver.fetchall()

                grabar(param, conn_mysql, datos)

    except Exception as e:
        graba_log({"ret_code": -3, "ret_txt": "arqueo_caja.consultar_y_grabar"}, "Excepción", e)
        resultado = []

    finally:
        if conn_sqlserver:
            conn_sqlserver.close()

        return resultado
    

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def grabar(param, conn_mysql, datos) -> list:
    resultado = []
    donde = "Inicio"

    try: 
        cursor_mysql = conn_mysql.cursor()
        # Agrupar resultados por tienda, puesto y apertura
        ventas_diarias = {}
        for row in datos:
            id_tienda = row.tienda
            id_puesto = row.ID_Puesto
            id_apertura = row.ID_Apertura
            fecha_hora = row.Fecha_Hora

            # Clave única para agrupación
            key = (id_tienda, id_puesto, id_apertura)

            if key not in ventas_diarias:
                ventas_diarias[key] = {
                    "id_tienda": id_tienda,
                    "id_tpv": id_puesto,
                    "fecha_hora": fecha_hora,
                    "ventas": 0,
                    "operaciones": 0,
                    "detalles": []
                }

            ventas_diarias[key]["ventas"] += row.Importe
            ventas_diarias[key]["operaciones"] += 0 # row.Operaciones
            ventas_diarias[key]["detalles"].append(row)

        # Insertar en mll_rec_ventas_diarias
        cierre_descs = ["Mañana", "Tarde", "Noche"]
        for idx, (key, data) in enumerate(ventas_diarias.items()):
            cierre_tpv_desc = cierre_descs[idx] if idx < len(cierre_descs) else f"Cierre {idx - len(cierre_descs) + 1}"

            donde = "insert"
            insert_diarias = """
                INSERT INTO mll_rec_ventas_diarias (id_tienda, id_tpv, fecha, ventas, operaciones, cierre_tpv_id, cierre_tpv_desc)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor_mysql.execute(
                insert_diarias,
                (
                    data["id_tienda"],
                    data["id_tpv"],
                    data["fecha_hora"],
                    data["ventas"],
                    data["operaciones"],
                    key[2],  # ID_Apertura
                    cierre_tpv_desc,
                )
            )
            id_ventas_diarias = cursor_mysql.lastrowid  # Obtener el ID insertado

            # Insertar en mll_rec_ventas_medio_pago
            for detalle in data["detalles"]:
                insert_medio_pago = """
                    INSERT INTO mll_rec_ventas_medio_pago (id_ventas_diarias, id_medios_pago, ventas, operaciones)
                    VALUES (%s, %s, %s, %s)
                """
                cursor_mysql.execute(insert_medio_pago,(
                                                        id_ventas_diarias,
                                                        detalle.ID_Cobro,
                                                        detalle.Importe,
                                                        0 # detalle.Operaciones,
                                                       )
                                    )

    except Exception as e:
        graba_log({"ret_code": -1, "ret_txt": "arqueo_caja.grabar - "+ donde}, "Excepción", e)
        resultado = []

    finally:
        return resultado