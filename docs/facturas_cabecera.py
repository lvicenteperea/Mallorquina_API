
from datetime import datetime, timedelta
from decimal import Decimal

from app.utils.utilidades import graba_log, imprime

from app.config.db_mallorquina import get_db_connection_sqlserver, close_connection_sqlserver

from app.utils.InfoTransaccion import InfoTransaccion
#from app.utils.mis_excepciones import MiException

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
        imprime([f"entidad: {entidad}",  
                 f"Tabla: {tabla}",  
                 f"bbdd_config: {bbdd_config}",  
                 f"nombre_tabla: {nombre_tabla}", 
                 # f"Campos: {campos}", 
                 f"tabla_config: {tabla_config}"], 
                 f"*...¿Que parametros?...", 2)     
        # ------------------------------------------------------------------------------------------------------------------------
        # Validaciones
        # para [Facturas Cabecera] ULT_VALOR debe tener la fecha de siguiente carga y los dias a cargar de una tirada, 
        # por ejemplo: "2025-01-01, 1" que indica que la próxima carga desde empezar en el día 01/01/2025 y se debe cargar un dia.
        # ------------------------------------------------------------------------------------------------------------------------
        print("   --- Ult Valor", tabla['ult_valor'])
        valores = tabla['ult_valor'].replace(" ", "").split(",")  
        print("   --- valores", valores)
        desde = valores[0]  # fecha en formato yyyy-mm-dd
        print("   --- desde", desde)
        dias = int(valores[1]) if len(valores) > 1 else 1  # Si falta, asigna 1
        print("   --- dias", dias)

        if desde:
            desde = datetime.strptime(f"{desde} 00:00:00", "%Y-%m-%d %H:%M:%S")
        else:
            raise ValueError("No está parametrizado el ult_valor de Facturas Cabeceras")

        hasta = desde + timedelta(days=1)
        # ------------------------------------------------------------------------------------------------------------------------

        param.debug = "conn origen"
        # conextamos con esta bbdd origen
        conn_sqlserver = get_db_connection_sqlserver(param, bbdd_config)

        # Hacer un bucle por fechas pedidas
        empieza = datetime.now()
        # ------------------------------------------------------------------------------------------------------------------------
        registros = obtener_y_grabar(param, conn_sqlserver, conn_mysql, entidad, tabla, desde, hasta, dias)
        # ------------------------------------------------------------------------------------------------------------------------
        imprime([f"Segundos: {(datetime.now()-empieza).total_seconds()}",f"Registros: {len(registros)}-{datetime.now()}"], "*", 2)
        
        return registros

    except Exception as e:
        param.error_sistema(e=e)
        graba_log(param, "proceso_general.Exception", e)
        raise 

    finally:
        param.debug = f"cierra conexión sqlserver: {param.debug}"
        close_connection_sqlserver(param, conn_sqlserver, None)

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def obtener_y_grabar(param: InfoTransaccion, conn_sqlserver, conn_mysql, entidad, tabla, desde, hasta, dias) -> list:
    param.debug="Obtener_datos_origen"
    mi_entidad = entidad["stIdEnt"]
    valor_max = None
    insertados = 0
    actualizados = 0
    registros = [valor_max, insertados, actualizados]

    

    try:
        # Leer datos desde SQL Server
        param.debug = "crear cursor"
        cursor_sqlserver = conn_sqlserver.cursor()
       
        # --------------------------------------------------------------------------------
        param.debug = "Inicio"
        vez = 1
        while vez <= dias:
            vez += 1
            param.debug = "Ejecución select 2"
            # pongo todos los campos a mano, pero con el tiempo se hará de forma dinámica, ya que en campos["nombre"] están los nombres de los campos de la tabla tratada
            select_query = f"""SELECT Fecha, [Hora Cobro], Tiempo, [Id Salon], [Id Mesa], Comensales, Tarifa, Idioma, [Id Turno], [Id Camarero], [Id Cliente Habitacion], [Id Apertura Puesto Cobro], [Factura Num], [Iva %], [Descuento %], Base, Descuento, Impuesto, Total, Propina, [Serie Puesto Facturacion], [Id Relacion], [Id Relacion Cocina], [Recien Abierta], Bk, Bk1, [Nombre Cajero], Anulada, [Fusion], Base2, Descuento2, [Iva2 %], Impuesto2, [Dcto Manual], [Importe Impresion], [Salida Receta], [IdCobro Propina], [Descripcion Cobro Propina], lVeces_Impreso, Edad, IdTipoCli, IdEvento, [Factura Num Cliente], [Cocina - Evento], [Cocina - Pedido], bDetenerComandaCocina_Mesa, [Cocina - Pedido 2], [CM Id_Reserva], [CM Id_Cliente], [Id Envio GS], bEnviando, [Id Envio Realizado], bNoCompCocina, stIdEnt, {entidad['ID']} 
                                FROM [Facturas Cabecera] fc
                                 WHERE fc.[Fecha] >= ?
                                   AND fc.[Fecha] < ?
                                   AND fc.stIdEnt = ?"""
            # imprime([f"{type(select_query)}: {select_query}", f"{type(id_cierre)}: {id_cierre}"], "=...Parametros...", 2)
            cursor_sqlserver.execute(select_query, (desde, hasta, entidad['stIdEnt'])) 
            datos = cursor_sqlserver.fetchall()
            
            # -----------------------------------------------------------------------------------
            param.debug = "Llamada a Grabar"
            valor_max, insertados, actualizados = grabar_datos(param, conn_mysql, entidad, tabla, datos, hasta)
            # -----------------------------------------------------------------------------------

            registros[0]  = valor_max
            registros[1] += insertados
            registros[2] += actualizados
            # registros.append(f"Fecha: {fecha} - cierre: {id_cierre}: {num_leidos} registros leidos y {num_escritos} escritos. {'✅' if num_leidos == num_escritos else '❌'}")


        cursor_sqlserver.close()
        # ---------------------------------------------------------------

        return registros

    except Exception as e:
        param.error_sistema(e=e)
        graba_log(param, "Obtener_datos_origen.Exception", e)
        raise 
        

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def grabar_datos(param: InfoTransaccion, conn_mysql, entidad, tabla, datos, hasta) -> list:
    param.debug="facturas_cabecera"
    cursor_mysql = None # para que no de error en el finally
    valor_max = hasta
    insertados = 0
    actualizados = 0

    try:
        insert_query = """INSERT INTO tpv_facturas_cabecera (Fecha, Hora_Cobro, Tiempo, Id_Salon, Id_Mesa, Comensales, Tarifa, Idioma, Id_Turno, Id_Camarero, Id_Cliente_Habitacion, Id_Apertura_Puesto_Cobro, Factura_Num, Iva_porc, Descuento_porc, Base, Descuento, Impuesto, Total, Propina, Serie_Puesto_Facturacion, Id_Relacion, Id_Relacion_Cocina, Recien_Abierta, Bk, Bk1, Nombre_Cajero, Anulada, Fusion, Base2, Descuento2, Iva2_porc, Impuesto2, Dcto_Manual, Importe_Impresion, Salida_Receta, IdCobro_Propina, Descripcion_Cobro_Propina, lVeces_Impreso, Edad, IdTipoCli, IdEvento, Factura_Num_Cliente, Cocina_Evento, Cocina_Pedido, bDetenerComandaCocina_Mesa, Cocina_Pedido_2, CM_Id_Reserva, CM_Id_Cliente, Id_Envio_GS, bEnviando, Id_Envio_Realizado, bNoCompCocina, stIdEnt, id_entidad)
                                                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"""
        datos_aux = [convertir_datos(fila) for fila in datos]
        datos_convertidos = [tupla for tupla in datos_aux]
        # imprime([f"Datos: {datos[0]}", 
        #          f"Convertidos: {datos_convertidos[0]}", 
        #          f"INSERT: {insert_query}",
        #          f"Tamaño: {len(datos[0])}-{type(datos[0])} - {len(datos_convertidos[0])}-{type(datos_convertidos[0])}", 
        #         ], 
        #          f"*...Datos...", 
        #          2)        

        for i in range(0, len(datos_convertidos), 1):
            lote = [tuple(registro) for registro in datos_convertidos[i:i + 1]]  # Convertir a tuplas extrayendo una porción de la lista
            if len(lote[0]) != 55:
                imprime([f"lote: {lote[0]}"], f"*...Lote: {i}-{len(lote[0])}...", 2)
                raise ValueError(f"Error en el lote {i} de {len(lote[0])} elementos")


        with conn_mysql.cursor() as cursor_mysql:
            leidos = len(datos_convertidos)
            param.debug = f"Bucle1 de {0} a {TAMAÑO_LOTE} de {leidos}"
            for i in range(0, leidos, TAMAÑO_LOTE):
                param.debug = f"Bucle2 de {i} a {i+TAMAÑO_LOTE} de {leidos}"
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
                            (datetime.now(), f'{hasta.strftime("%Y-%m-%d")}, 1', tabla["ID"]) # lo hacemos con el hasta porque hemos cargado < HASTA
                            )
        conn_mysql.commit()
        
        
        return [valor_max, insertados, actualizados]

    except Exception as e:
        param.error_sistema(e=e)
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