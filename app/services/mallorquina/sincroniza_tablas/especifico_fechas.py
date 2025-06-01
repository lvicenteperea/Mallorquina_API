from datetime import date, datetime, timedelta
from decimal import Decimal
import re
import pymysql

from app.utils.utilidades import graba_log, imprime
from app.config.db_mallorquina import get_db_connection_sqlserver, close_connection_sqlserver

from app.utils.InfoTransaccion import InfoTransaccion
#from app.utils.mis_excepciones import MiException

TAMAÑO_LOTE: int = 500
SALTO: int = 10000
FUNCION = "especifico_fechas"

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def proceso(param: InfoTransaccion, conn_mysql, entidad, tabla, bbdd_config, campos, tabla_config) -> list:
    param.debug=f"{FUNCION}.proceso"
    registros: list = [None, 0, 0, '']  # [valor_max, insertados, actualizados, error]
    conn_sqlserver = None  # para que no de error en el finally
    
    try:
        campos_origen = [campo['Nombre'] for campo in campos]
        campos_destino = [campo['Nombre_Destino'] for campo in campos]
        # imprime([f"entidad: {entidad}",  
        #          f"Tabla: {tabla}",  
        #          f"bbdd_config: {bbdd_config}",  
        #          f"Campos Origen: {campos_origen}",    
        #          f"Campos Destino: {campos_destino}",  
        #          f"Campos placeholders: {', '.join(['%s'] * len(campos_destino))}", 
        #          f"tabla_config: {tabla_config}"], 
        #          f"*...¿Que parametros?...", 2)     
        # ------------------------------------------------------------------------------------------------------------------------
        # Validaciones
        # para [Facturas Cabecera] ULT_VALOR debe tener la fecha de siguiente carga y los dias a cargar de una tirada, 
        # por ejemplo: "2025-01-01, 1" que indica que la próxima carga desde empezar en el día 01/01/2025 y se debe cargar un dia.
        # ------------------------------------------------------------------------------------------------------------------------
        valores = tabla['ult_valor'].replace(" ", "").split(",")  
        desde = valores[0]  # fecha en formato yyyy-mm-dd

        if desde:
            desde = datetime.strptime(f"{desde} 00:00:00", "%Y-%m-%d %H:%M:%S")
        else:
            raise ValueError("No está parametrizado el ult_valor de Facturas Cabeceras")
        # ------------------------------------------------------------------------------------------------------------------------
        if desde.date() < datetime.now().date():
            param.debug = "conn origen especifico_fechas"
            # conextamos con esta bbdd origen
            conn_sqlserver = get_db_connection_sqlserver(param, bbdd_config)

            # ------------------------------------------------------------------------------------------------------------------------
            registros = obtener_y_grabar(param, conn_sqlserver, conn_mysql, entidad, tabla, desde.date(), campos_origen, campos_destino, tabla_config)
            # ------------------------------------------------------------------------------------------------------------------------
            # imprime([f"Segundos: {(datetime.now()-empieza).total_seconds()}",
            #         f"Registros: {len(registros)} - desde {empieza} a {datetime.now()}",
            #         f"Fechas tratadas: {desde} - {hasta}"],
            #         "*", 2)
        
        return registros

    except Exception as e:
        param.error_sistema(e=e, debug=f"{FUNCION}.proceso")
        raise e
    
    finally:
        # param.debug = f"cierra conexión sqlserver: {param.debug}"
        close_connection_sqlserver(param, conn_sqlserver, None)
#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def obtener_y_grabar(param: InfoTransaccion, conn_sqlserver, conn_mysql, entidad, tabla, desde: date, campos_origen, campos_destino, tabla_config) -> list:
    param.debug=f"{FUNCION}.obtener_y_grabar"
    stIdEnt = entidad["stIdEnt"]
    tratar_desde = desde                      # vamos a tratar un dia a la vez para Fecha >= desde
    tratar_hasta = tratar_desde + timedelta(days=1)  # vamos a tratar un dia a la vez oara fecha < hasta
    valor_max = None
    insertados = 0
    actualizados = 0
    registros = [valor_max, insertados, actualizados, '']  # [valor_max, insertados, actualizados, error]

    try:
        # Leer datos desde SQL Server
        param.debug = f"{FUNCION}.crear cursor"
        cursor_sqlserver = conn_sqlserver.cursor()
       
        # --------------------------------------------------------------------------------
        param.debug = f"{FUNCION}.Inicio" 
        # vamos a tratar todos los dias desde que se quedó hasta la fecha de hoy (ayer)
        while True:
            if tratar_desde >= date.today(): # replace(hour=0, minute=0, second=0, microsecond=0):
                break   # Nos salimos el bucle de dias porque no puede ser mayor a hoy la fecha de tratamiento

            pos = 0
            while True:
                param.debug = f"{FUNCION}.Ejecución select {tratar_desde}"
                cadena_select = ', '.join(campos_origen)
                orden = extraer_campos_para_order(param, tabla_config['where'])
            
                select_query = f"""SELECT {cadena_select.replace("{0}", f"{entidad['ID']}  as id_entidad" )} 
                                    FROM {tabla_config['Tabla_Origen']} t
                                    WHERE t.stIdEnt = ? 
                                    AND {tabla_config['where']} --  where debe llevar un formato con dos parametros tipo: "t.[Fecha] >= ?  AND t.[Fecha] < ?"  o "? = ?"
                                    ORDER BY {orden} -- t.[Fecha_Hora]
                                    OFFSET ? ROWS            -- Salta x filas
                                    FETCH NEXT {SALTO} ROWS ONLY; -- Toma las siguientes SALTO lineas
                                """
                if pos == 0:
                    imprime([select_query, stIdEnt, tratar_desde, tratar_hasta, pos], "* -- QUERY -- ", 2)

                cursor_sqlserver.execute(select_query, (stIdEnt, tratar_desde, tratar_hasta, pos)) 
                datos = cursor_sqlserver.fetchall()
                if len(datos) == 0:   # hemos terminado
                    break

                # -----------------------------------------------------------------------------------
                param.debug = f"{FUNCION}.Llamada a Grabar"
                insertados, actualizados = grabar_datos(param, conn_mysql, entidad['id_bbdd'], datos, campos_destino, tabla_config)
                # -----------------------------------------------------------------------------------

                registros[0]  = tratar_hasta 
                registros[1] += insertados
                registros[2] += actualizados
                pos          += SALTO
            # FIN WHILE secundario ---------------------------------------------------------------

            # FIN DIA cerramos con conexión con MysqlServer
            # actualizamos control y COMMIT
            # cursor_mysql = conn_mysql.cursor(dictionary=True)
            cursor_mysql = conn_mysql.cursor(pymysql.cursors.DictCursor)
            param.debug = "Execute fec_ult_act"
            cursor_mysql.execute("""UPDATE mll_cfg_tablas_entidades
                                    SET Fecha_Ultima_Actualizacion = %s, 
                                        ult_valor = COALESCE(%s, ult_valor)
                                    WHERE ID = %s""",
                                (datetime.now(), f'{tratar_hasta.strftime("%Y-%m-%d")}', tabla["ID"]) # lo hacemos con el hasta porque hemos cargado < hasta
                                )
            conn_mysql.commit()
            
            tratar_desde = tratar_hasta                      # vamos a tratar un dia a la vez para Fecha >= desde
            tratar_hasta = tratar_desde + timedelta(days=1)  # vamos a tratar un dia a la vez oara fecha < hasta
        # FIN WHILE PRINCIPAL  ---------------------------------------------------------------

        cursor_sqlserver.close()
        return registros

    except Exception as e:
        param.error_sistema(e=e, debug=f"{FUNCION}.Excepción")
        raise 
        

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def grabar_datos(param: InfoTransaccion, conn_mysql, id_BBDD, datos, campos_destino, tabla_config) -> list:
    param.debug=f"{FUNCION}facturas_cabecera"
    cursor_mysql = None # para que no de error en el finally
    insertados = 0
    actualizados = 0

    try:
        cadena_select = ', '.join(campos_destino) + ", Origen_BBDD"
        cadena_placeholders = ', '.join(['%s'] * (len(campos_destino)+1))
        insert_query = f"INSERT INTO {tabla_config['Tabla_Destino']}   ({cadena_select})  VALUES({cadena_placeholders});"

        datos_aux = [convertir_datos(fila) for fila in datos]
        datos_convertidos = [tupla + (id_BBDD,) for tupla in datos_aux]

        # Validación para ver si todos los registros y tienen el mismo número de campos.....
        # for i in range(0, len(datos_convertidos), 1):
        #     lote = [tuple(registro) for registro in datos_convertidos[i:i + 1]]  # Convertir a tuplas extrayendo una porción de la lista
        #     if len(lote[0]) != 44:
        #         imprime([f"lote: {lote[0]}"], f"*...Lote: {i}-{len(lote[0])}...", 2)
        #         raise ValueError(f"Error en el lote {i} de {len(lote[0])} elementos")

        with conn_mysql.cursor() as cursor_mysql:
            leidos = len(datos_convertidos)
            param.debug = f"Bucle1 de {0} a {TAMAÑO_LOTE} de {leidos}"
            for i in range(0, leidos, TAMAÑO_LOTE):
                param.debug = f"Bucle2 de {i} a {i+TAMAÑO_LOTE} de {leidos}"
                lote = datos_convertidos[i:i + TAMAÑO_LOTE]  # Extraer una porción de la lista

                lote = [tuple(registro) for registro in datos_convertidos[i:i + TAMAÑO_LOTE]]  # Convertir a tuplas extrayendo una porción de la lista
                # imprime([f"type(lote): {type(lote)}", f"type(lote[0]): {type(lote[0])}"], f"-", 2)
                # for x, fila in enumerate(lote):
                #     print(f"Fila {x}: {type(fila)} - {len(fila)} elementos")
                #     for j, valor in enumerate(fila):
                #         print(f"  🟢 Pos {j}: {type(valor)} - <{valor}>")
                #     break    
                cursor_mysql.executemany(insert_query, lote)  # Insertar el lote
                insertados += cursor_mysql.rowcount
       
        return [insertados, actualizados]

    except Exception as e:
        param.error_sistema(e=e, debug=f"{FUNCION}.Grabar_Datos.Excepcion")
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

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def extraer_campos_para_order(param: InfoTransaccion, campo_where):
    match = re.search(r"t\..*?\]", campo_where)

    if match:
        return match.group()  # Captura toda la coincidencia
    else:
        raise ValueError("No tenemos ORDEN")