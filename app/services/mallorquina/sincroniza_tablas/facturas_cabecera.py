
from datetime import datetime, timedelta
from decimal import Decimal
import json
import re

from app.utils.functions import graba_log, imprime

from app.models.mll_cfg_tablas import obtener_campos_tabla, crear_tabla_destino
from app.models.mll_cfg_bbdd import obtener_conexion_bbdd_origen
from app.config.db_mallorquina import get_db_connection_mysql, close_connection_mysql, get_db_connection_sqlserver, close_connection_sqlserver
from app.models.mll_cfg import obtener_cfg_general, actualizar_en_ejecucion
from app.services.auxiliares.sendgrid_service import enviar_email

from app.utils.InfoTransaccion import InfoTransaccion
from app.utils.mis_excepciones import MiException

TAMAÑO_LOTE: int = 500


#----------------------------------------------------------------------------------------
'''
EJEMPLO DE PARAMETROS
---------------------
entidad: {'ID': 4, 'Nombre': 'Quevedo', 'id_bbdd': 1, 'stIdEnt': '1411221752472732', 'activo': 'S', 'Ultima_Fecha_Carga': datetime.datetime(2025, 2, 1, 6, 47, 54), 'ultimo_cierre': None, 'created_at': datetime.datetime(2025, 1, 30, 8, 19, 31), 'updated_at': datetime.datetime(2025, 2, 1, 6, 47, 54), 'modified_by': None}
Tabla: {'ID': 34, 'ID_entidad': 4, 'ID_Tabla': 5, 'Fecha_Ultima_Actualizacion': datetime.datetime(2025, 2, 1, 12, 21, 13), 'Cada_Cuanto_Ejecutar': 0, 'ult_valor': '2025-01-31 20:34:54', 'created_at': datetime.datetime(2025, 1, 31, 7, 54, 53), 'updated_at': datetime.datetime(2025, 2, 1, 12, 21, 13), 'modified_by': None, 'ID_BBDD': 1}
bbdd_config: {'host': '46.183.113.172', 'port': '1434', 'user': 'Informes_Ext', 'database': 'GR_MALLORQUINA', 'password': 'e7LDKH8PzQaGHUI'}
nombre_tabla: [Facturas Cabecera]
Campos: [{'ID': 66, 'ID_Tabla': 5, 'Nombre': '[stIdEnt]', 'Nombre_Destino': 'stIdEnt', 'Tipo': 'varchar(20) CHARACTER SET utf8mb4', 'PK': 1, 'created_at': datetime.datetime(2025, 1, 13, 23, 27, 5), 'updated_at': datetime.datetime(2025, 1, 17, 13, 20, 58), 'modified_by': None, 'ult_valor': '2025-01-31 20:34:54'}, {'ID': 13, 'ID_Tabla': 5, 'Nombre': '[Fecha]', 'Nombre_Destino': 'Fecha', 'Tipo': 'TIMESTAMP', 'PK': 2, 'created_at': datetime.datetime(2025, 1, 13, 23, 27, 4), 'updated_at': datetime.datetime(2025, 1, 17, 13, 20, 58), 'modified_by': None, 'ult_valor': '2025-01-31 20:34:54'}, {'ID': 33, 'ID_Tabla': 5, 'Nombre': '[Serie Puesto Facturacion]', 'Nombre_Destino': 'Serie_Puesto_Facturacion', 'Tipo': 'varchar(10) CHARACTER SET utf8mb4', 'PK': 3, 'created_at': datetime.datetime(2025, 1, 13, 23, 27, 4), 'updated_at': datetime.datetime(2025, 1, 17, 13, 20, 58), 'modified_by': None, 'ult_valor': '2025-01-31 20:34:54'},....]
tabla_config: {'ID': 5, 'Tabla_Origen': '[Facturas Cabecera]', 'Tabla_Destino': 'tpv_facturas_cabecera', 'campos_PK': '("stIdEnt"; "Fecha"; "[Serie Puesto Facturacion]"; "[Factura Num]"; "[Id Relacion]") ("{v1} >= \'{v2}\'"; "{v1} > CONVERT(DATETIME, \'{v2}\', 121) "; "{v1} > \'{v2}\'"; "{v1} > {v2}"; "{v1} > {v2}") (2)', 'insert_update': 'I', 'Borrar_Tabla': 0, 'created_at': datetime.datetime(2025, 1, 13, 23, 1, 13), 'updated_at': datetime.datetime(2025, 1, 31, 10, 29, 32), 'modified_by': None}
'''
#----------------------------------------------------------------------------------------
def facturas_cabecera(param: InfoTransaccion, conn_mysql, entidad, tabla, bbdd_config, nombre_tabla, campos, tabla_config) -> list:
    param.debug="facturas_cabecera"

    try:
        # imprime([f"entidad: {entidad}",  f"Tabla: {tabla}",  f"bbdd_config: {bbdd_config}",  f"nombre_tabla: {nombre_tabla}", 
        #          # f"Campos: {campos}", 
        #          f"tabla_config: {tabla_config}"], 
        #          f"*...¿Que parametros?...", 2)
        

        proxima_fecha = tabla["ult_valor"]
        param.debug = "conn origen"
        # conextamos con esta bbdd origen
        conn_sqlserver = get_db_connection_sqlserver(bbdd_config)

        # Hacer un bucle por fechas pedidas
        empieza = datetime.now()
        # imprime(tabla, f"*...Tabla...", 2)
        registros = obtener_y_grabar(param, conn_sqlserver, conn_mysql, entidad, tabla, proxima_fecha)
        imprime([f"Segundos: {(datetime.now()-empieza).total_seconds()}",f"Registros: {len(registros)}-{datetime.now()}"], "*", 2)
        
        
        return registros

    except Exception as e:
        param.error_sistema()
        graba_log(param, "proceso_general.Exception", e)
        raise 

    finally:
        param.debug = f"cierra conexión sqlserver: {param.debug}"
        close_connection_sqlserver(conn_sqlserver, None)

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def obtener_y_grabar(param: InfoTransaccion, conn_sqlserver, conn_mysql, entidad, tabla, fecha_a_tratar) -> list:
    param.debug="Obtener_datos_origen"
    registros = []
    mi_entidad = entidad["stIdEnt"]
    

    try:
        # Leer datos desde SQL Server
        param.debug = "crear cursor"
        cursor_sqlserver = conn_sqlserver.cursor()
       
        # --------------------------------------------------------------------------------
        param.debug = "Inicio"
        fecha = datetime.strptime(fecha_a_tratar, "%Y-%m-%d %H:%M:%S")

        # en realidad parametros solo tiene un elemento que es la fecha y debe ser en formato aaaa-mm-dd
        # select_query = """SELECT [Id Cierre]
        #                     FROM [Cierres de Caja] 
        #                     WHERE CAST(Fecha AS DATE) = %s
        #                       -- AND stIdEnt = %s
        #                 """
        # param.debug = "Ejecución select 1"
        # cursor_sqlserver.execute(select_query, (fecha,)) # mi_entidad,)) 
        # apertura_ids_lista = cursor_sqlserver.fetchall()
        ids_cierre = [4614, 4615, 4616, 4617]  # [item[0] for item in apertura_ids_lista]
        

        # imprime([f"{type(apertura_ids_lista)}: {apertura_ids_lista}", f"{type(ids_cierre)}: {ids_cierre}", f"{type(ult_valor)}: {ult_valor}", f"{type(fecha)}: {fecha}"], "=",2)
        # z=1/0

        for id_cierre in ids_cierre:
            # buscamos los cierres de estos IDs
            param.debug = "Ejecución select 2"
            # pongo todos los campos a mano, pero con el tiempo se hará de forma dinámica, ya que en campos["nombre"] están los nombres de los campos de la tabla tratada
            select_query = """SELECT Fecha, [Hora Cobro], Tiempo, [Id Salon], [Id Mesa], Comensales, Tarifa, Idioma, [Id Turno], [Id Camarero], [Id Cliente Habitacion], [Id Apertura Puesto Cobro], [Factura Num], [Iva %], [Descuento %], Base, Descuento, Impuesto, Total, Propina, [Serie Puesto Facturacion], [Id Relacion], [Id Relacion Cocina], [Recien Abierta], Bk, Bk1, [Nombre Cajero], Anulada, [Fusion], Base2, Descuento2, [Iva2 %], Impuesto2, [Dcto Manual], [Importe Impresion], [Salida Receta], [IdCobro Propina], [Descripcion Cobro Propina], lVeces_Impreso, Edad, IdTipoCli, IdEvento, [Factura Num Cliente], [Cocina - Evento], [Cocina - Pedido], bDetenerComandaCocina_Mesa, [Cocina - Pedido 2], [CM Id_Reserva], [CM Id_Cliente], [Id Envio GS], bEnviando, [Id Envio Realizado], bNoCompCocina, stIdEnt 
                                FROM [Facturas Cabecera] fc
                                WHERE fc.[Id Apertura Puesto Cobro] = ?
                                 AND fc.stIdEnt = ?"""
            # imprime([f"{type(select_query)}: {select_query}", f"{type(id_cierre)}: {id_cierre}"], "=...Parametros...", 2)
            cursor_sqlserver.execute(select_query, (id_cierre, mi_entidad)) 
            datos = cursor_sqlserver.fetchall()
            # imprime([f"{type(datos)}: {datos}"], "=...Datos...", 2)
            # z=1/0

            num_leidos = len(datos)
            # -----------------------------------------------------------------------------------
            param.debug = "Llamada a Grabar"
            num_escritos = grabar_datos(param, conn_mysql, entidad, tabla, datos, fecha, id_cierre)
            # -----------------------------------------------------------------------------------

            registros.append(f"Fecha: {fecha} - cierre: {id_cierre}: {num_leidos} registros leidos y {num_escritos} escritos. {'✅' if num_leidos == num_escritos else '❌'}")

        cursor_sqlserver.close()
        # ---------------------------------------------------------------

        return registros

    except Exception as e:
        param.error_sistema()
        graba_log(param, "Obtener_datos_origen.Exception", e)
        raise 
        

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def grabar_datos(param: InfoTransaccion, conn_mysql, entidad, tabla, datos, fecha, id_cierre) -> int:
    param.debug="facturas_cabecera"
    cursor_mysql = None # para que no de error en el finally
    insertados = 0

    try:
        insert_query = """INSERT INTO tpv_facturas_cabecera (Fecha, Hora_Cobro, Tiempo, Id_Salon, Id_Mesa, Comensales, Tarifa, Idioma, Id_Turno, Id_Camarero, Id_Cliente_Habitacion, Id_Apertura_Puesto_Cobro, Factura_Num, Iva_porc, Descuento_porc, Base, Descuento, Impuesto, Total, Propina, Serie_Puesto_Facturacion, Id_Relacion, Id_Relacion_Cocina, Recien_Abierta, Bk, Bk1, Nombre_Cajero, Anulada, Fusion, Base2, Descuento2, Iva2_porc, Impuesto2, Dcto_Manual, Importe_Impresion, Salida_Receta, IdCobro_Propina, Descripcion_Cobro_Propina, lVeces_Impreso, Edad, IdTipoCli, IdEvento, Factura_Num_Cliente, Cocina_Evento, Cocina_Pedido, bDetenerComandaCocina_Mesa, Cocina_Pedido_2, CM_Id_Reserva, CM_Id_Cliente, Id_Envio_GS, bEnviando, Id_Envio_Realizado, bNoCompCocina, stIdEnt, id_entidad)
                                                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"""
        datos_aux = [convertir_datos(fila) for fila in datos]
        datos_convertidos = [tupla + (entidad['ID'],) for tupla in datos_aux]
        # imprime([f"Datos: {datos[0]}", f"Convertidos: {datos_convertidos[0]}", f"INSERT: {insert_query}"], f"*...Datos: {len(datos[0])}-{type(datos[0])}...", 2)
        

        for i in range(0, len(datos_convertidos), 1):
            lote = [tuple(registro) for registro in datos_convertidos[i:i + 1]]  # Convertir a tuplas extrayendo una porción de la lista
            if len(lote[0]) != 55:
                # imprime([f"lote: {lote[0]}"], f"*...Lote: {i}-{len(lote[0])}...", 2)
                raise ValueError(f"Error en el lote {i} de {len(lote[0])} elementos")


        with conn_mysql.cursor() as cursor_mysql:
            leidos = len(datos_convertidos)
            param.debug = f"Bucle de {0} a {TAMAÑO_LOTE} de {leidos}"
            for i in range(0, leidos, TAMAÑO_LOTE):
                param.debug = f"Bucle de {i} a {i+TAMAÑO_LOTE} de {leidos}"
                # lote = datos_convertidos[i:i + TAMAÑO_LOTE]  # Extraer una porción de la lista

                lote = [tuple(registro) for registro in datos_convertidos[i:i + TAMAÑO_LOTE]]  # Convertir a tuplas extrayendo una porción de la lista
                # imprime([f"type(lote): {type(lote)}", f"type(lote[0]): {type(lote[0])}"], f"-", 2)
                # for x, fila in enumerate(lote):
                #     print(f"Fila {x}: {type(fila)} - {len(fila)} elementos")
                #     for j, valor in enumerate(fila):
                #         print(f"  🟢 Pos {j}: {type(valor)} - <{valor}>")

                cursor_mysql.executemany(insert_query, lote)  # Insertar el lote
                insertados += cursor_mysql.rowcount
       
        cursor_mysql = conn_mysql.cursor()
        param.debug = "Execute fec_ult_act"
        cursor_mysql.execute("""UPDATE mll_cfg_tablas_entidades
                                SET Fecha_Ultima_Actualizacion = %s, 
                                    ult_valor = COALESCE(%s, ult_valor)
                                WHERE ID = %s""",
                            (datetime.now(), fecha.strftime("%Y-%m-%d %H:%M:%S"), tabla["ID"])
                            )
        conn_mysql.commit()
        
        
        return insertados

    except Exception as e:
        param.error_sistema()
        graba_log(param, "grabar_datos.Exception", e)
        raise 


#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def convertir_datos(registro):
    return tuple(
        val.strftime("%Y-%m-%d %H:%M:%S") if isinstance(val, datetime) else  # Convierte datetime
        float(val)                        if isinstance(val, Decimal) else  # Convierte Decimal a float
        int(val)                          if isinstance(val, bool) else  # Convierte booleanos a 1 o 0
        # None                              if val == None else  # Reemplaza "" con None
        None                              if val == "" else  # Reemplaza "" con None
        val  # Dejar los demás valores igual
        for val in registro
    )