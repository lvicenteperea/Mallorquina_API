from fastapi import HTTPException
from datetime import datetime
from decimal import Decimal

import json

from app import mi_libreria as mi


from app.utils.functions import graba_log
from app.models.mll_cfg import obtener_configuracion_general, actualizar_en_ejecucion
from app.models.mll_cfg_bbdd import obtener_conexion_bbdd_origen
from app.config.db_mallorquina import get_db_connection_sqlserver, get_db_connection_mysql, close_connection_mysql
from app.services.auxiliares.sendgrid_service import enviar_email

from app.utils.InfoTransaccion import InfoTransaccion

'''
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
'''
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

    donde = "get_db_connection_mysql"
    try:
        conn_mysql = get_db_connection_mysql()
        cursor_mysql = conn_mysql.cursor(dictionary=True)

        donde = "Select"
        cursor_mysql.execute("SELECT * FROM mll_cfg_bbdd where activo= 'S'") # where id=1")
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
        graba_log({"ret_code": -1, "ret_txt": f"{donde}"}, "Excepción arqueCaja.proceso", e)
        param.ret_code = -1
        param.ret_txt = "Error General, contacte con su administrador"

    finally:
        close_connection_mysql(conn_mysql, cursor_mysql)

        actualizar_en_ejecucion(0)
        enviar_email(config["Lista_emails"],
                     "Proceso finalizado",
                     "El proceso de sincronización ha terminado."
        )


#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def consultar_y_grabar(tabla, conn_mysql, param: InfoTransaccion) -> list:
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
                                        0 as Operaciones,
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

                resultado = grabar(param, conn_mysql, tabla, datos)
                if param.ret_code != 0:
                    mi.imprime(["resultado", resultado, param.ret_code, param.ret_txt], "-")

    except Exception as e:
        graba_log({"ret_code": -3, "ret_txt": "arqueo_caja.consultar_y_grabar"}, "Excepción", e)
        resultado = []
        param.ret_code = -1
        param.ret_txt = "Error General, contacte con su administrador"

    finally:
        if conn_sqlserver:
            conn_sqlserver.close()

        return resultado
    

#----------------------------------------------------------------------------------------
'''
para operaciones:

SELECT *
From [Facturas Cabecera] FC
 WHERE FC.[Id Relacion] = 842480

 select *
from caja
where [Id relacion factura] =842480
 
'''
#----------------------------------------------------------------------------------------
def grabar(param: InfoTransaccion, conn_mysql, tabla, datos) -> list:
    resultado = [0 , 0]
    donde = "Inicio"

    try: 
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

            mi.imprime(["Resultado: "]+list(row))

            if key not in ventas_diarias:
                ventas_diarias[key] = {
                    "id_tienda": id_tienda,
                    "id_tpv": id_puesto,
                    "fecha": fecha,
                    "ventas": 0,
                    "operaciones": 0,
                    "detalles": []
                }

            ventas_diarias[key]["ventas"] += row.Importe
            ventas_diarias[key]["operaciones"] += row.Operaciones
            ventas_diarias[key]["detalles"].append(row)
            print("Parcial: ", id_apertura, ventas_diarias[key]["ventas"])
            resultado[0] = resultado[0] + float(ventas_diarias[key]["ventas"])
            resultado[1] += ventas_diarias[key]["operaciones"]

        # Insertar en mll_rec_ventas_diarias
        cierre_descs = ["Mañana", "Tarde", "Noche"]
        for idx, (key, data) in enumerate(ventas_diarias.items()):
            cierre_tpv_desc = cierre_descs[idx] if idx < len(cierre_descs) else f"Cierre {idx - len(cierre_descs) + 1}"

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
                    cierre_tpv_desc,
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
        resultado[0] = float(resultado[0]) 

    except Exception as e:
        graba_log({"ret_code": -1, "ret_txt": "arqueo_caja.grabar - "+ donde}, "Excepción", e)
        resultado = [0 , 0]
        param.ret_code = -1
        param.ret_txt = "Error General, contacte con su administrador"

    finally:
        return resultado