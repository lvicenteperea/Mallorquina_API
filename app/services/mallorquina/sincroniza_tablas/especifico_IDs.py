from datetime import datetime
import pymysql
from app.config.db_mallorquina import get_db_connection_sqlserver, close_connection_sqlserver
from app.services.mallorquina.sincroniza_tablas.especifico_fechas import grabar_datos # extraer_campos_para_order, convertir_datos

from app.utils.InfoTransaccion import InfoTransaccion

TAMAÑO_LOTE: int = 500
SALTO: int = 10000
FUNCION = "especifico_IDs"
MAX_INTENTOS_VACIOS = 3  # Límite de consultas vacías consecutivas

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def proceso(param: InfoTransaccion, conn_mysql, entidad, tabla, bbdd_config, campos, tabla_config) -> list:
    param.debug=f"{FUNCION}.proceso"
    registros: list = [None, 0, 0, '']  # [valor_max, insertados, actualizados, error]
    conn_sqlserver = None  # para que no de error en el finally
    
    try:
        campos_origen = [campo['Nombre'] for campo in campos]
        campos_destino = [campo['Nombre_Destino'] for campo in campos]

        valores = tabla['ult_valor'].replace(" ", "").split(",")  
        if not tabla['ult_valor'] or not valores:
            raise ValueError(f"No está parametrizado el ult_valor de Facturas Cabeceras: {tabla['ult_valor']} - {valores} ç {desde}")
        
        desde = int(valores[0])  # ID

        # ------------------------------------------------------------------------------------------------------------------------
        param.debug = "conn origen especifico_fechas"
        # conextamos con esta bbdd origen
        conn_sqlserver = get_db_connection_sqlserver(param, bbdd_config)

        # ------------------------------------------------------------------------------------------------------------------------
        registros = obtener_y_grabar(param, conn_sqlserver, conn_mysql, entidad, tabla, desde, campos_origen, campos_destino, tabla_config)
        # ------------------------------------------------------------------------------------------------------------------------
        
        return registros

    except Exception as e:
        param.error_sistema(e=e, debug=f"{FUNCION}.proceso")
        raise e
    
    finally:
        # param.debug = f"cierra conexión sqlserver: {param.debug}"
        close_connection_sqlserver(param, conn_sqlserver, None)
#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def obtener_y_grabar(param: InfoTransaccion, conn_sqlserver, conn_mysql, entidad, tabla, desde, campos_origen, campos_destino, tabla_config) -> list:
    param.debug=f"{FUNCION}.obtener_y_grabar"
    stIdEnt = entidad["stIdEnt"]
    insertados = 0
    actualizados = 0
    registros = [None, insertados, actualizados, '']  # [valor_max, insertados, actualizados, error]

    try:
        param.debug = f"{FUNCION}.Maximo ID Principal"
        cursor_sqlserver = conn_sqlserver.cursor()
        query_global = f"""SELECT MIN([Id Principal]), MAX([Id Principal]), COUNT(*) 
                             FROM {tabla_config['Tabla_Origen']} 
                            WHERE stIdEnt = ? AND [Id Principal] >= ?
                        """
        cursor_sqlserver.execute(query_global, (stIdEnt,desde,))
        min_global, max_global, total_registros = cursor_sqlserver.fetchone()
        cursor_sqlserver.close()
        # Generar los tramos óptimos
        if min_global is None or max_global is None:
            tramos = []
        else:
            tramos = obtener_registros_por_tramos(param, conn_sqlserver, tabla_config['Tabla_Origen'], stIdEnt, min_global, max_global)

        cursor_sqlserver = conn_sqlserver.cursor()
        # Leer datos desde SQL Server
        param.debug = f"{FUNCION}.crear cursor"
        cursor_sqlserver = conn_sqlserver.cursor()
       
        # --------------------------------------------------------------------------------
        param.debug = f"{FUNCION}.Inicio" 

        # vamos a tratar todos los dias desde que se quedó hasta la fecha de hoy (ayer)
        for min_id, max_id, count in tramos:
            param.debug = f"{FUNCION}.Ejecución select {min_id} - {max_id}"
            cadena_select = ', '.join(campos_origen)
            # orden = extraer_campos_para_order(param, tabla_config['where'])
        
            select_query = f"""SELECT {cadena_select.replace("{0}", f"{entidad['ID']}  as id_entidad" )} 
                                FROM {tabla_config['Tabla_Origen']} t
                                WHERE t.stIdEnt = ? 
                                AND {tabla_config['where']} --  where debe llevar un formato con dos parametros tipo: "t.[id] >= ?  AND t.[id] < ?"  o "? = ?"
                                -- ORDER BY orden
                                ;
                            """
            cursor_sqlserver.execute(select_query, (stIdEnt, min_id, max_id))

            registros[0]  = max_id
            # Procesar los registros de este tramo
            while True:
                datos = cursor_sqlserver.fetchmany(1000)  # Leer en lotes pequeños
                if not datos or len(datos) == 0:   # hemos terminado
                    break   # insertados, actualizados = 0, 0

                param.debug = f"{FUNCION}.Llamada a Grabar"
                insertados, actualizados = grabar_datos(param, conn_mysql, entidad['id_bbdd'], datos, campos_destino, tabla_config)

                registros[1] += insertados
                registros[2] += actualizados

            # FIN DIA cerramos con conexión con MysqlServer
            # actualizamos control y COMMIT
            # cursor_mysql = conn_mysql.cursor(dictionary=True)
            cursor_mysql = conn_mysql.cursor(pymysql.cursors.DictCursor)
            param.debug = "Execute fec_ult_act"
            cursor_mysql.execute("""UPDATE mll_cfg_tablas_entidades
                                    SET Fecha_Ultima_Actualizacion = %s, 
                                        ult_valor = COALESCE(%s, ult_valor)
                                    WHERE ID = %s""",
                                (datetime.now(), {max_id+1}, tabla["ID"]) # max_id+1 proque max_id lo ha cargado
                                )
            conn_mysql.commit()
            
        # FIN WHILE PRINCIPAL  ---------------------------------------------------------------

        cursor_sqlserver.close()
        return registros

    except Exception as e:
        param.error_sistema(e=e, debug=f"{FUNCION}.Excepción")
        raise 
        


#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def obtener_registros_por_tramos(param: InfoTransaccion, conn_mysql, tabla, stIdEnt, desde, hasta_global, saltos=SALTO):
    cursor_sqlserver = conn_mysql.cursor()
    tramos = []
    intentos_vacios = 0

    try:    
        while desde < hasta_global and intentos_vacios < MAX_INTENTOS_VACIOS:
            # Calcular el "hasta" tentativo para este tramo
            hasta_tentativo = min(desde + saltos, hasta_global)
            
            # Consulta para ver si hay registros en este rango
            query = f"""SELECT MIN([Id Principal]), MAX([Id Principal]), COUNT(*) 
                          FROM {tabla} 
                         WHERE stIdEnt = ? AND [Id Principal] BETWEEN ? AND ?
                    """
            cursor_sqlserver.execute(query, (stIdEnt, desde, hasta_tentativo))
            min_id, max_id, count = cursor_sqlserver.fetchone()
            
            if count > 0:
                param.debug = f"{FUNCION}.obtener_registros_por_tramos.Encontrados {count} registros entre {desde} y {hasta_tentativo} (min: {min_id}, max: {max_id})"
                # Si hay registros, añadir este tramo
                tramos.append((min_id, max_id, count))
                desde = max_id + 1  # Saltamos al siguiente ID después del máximo encontrado
                intentos_vacios = 0
                
                # Ajustar dinámicamente el tamaño del salto (opcional)
                saltos = min(saltos * 2, 100000)  # No superar 100k para no perder granularidad
            else:
                param.debug = f"{FUNCION}.obtener_registros_por_tramos.No se encontraron registros entre {desde} y {hasta_tentativo}. Intentos vacíos: {intentos_vacios + 1}"
                # Si no hay registros, saltar un bloque más grande
                desde = hasta_tentativo + 1
                intentos_vacios += 1
                saltos = min(saltos * 10, 100000)  # Saltos más grandes cuando no hay datos
        
        return tramos

    except Exception as e:
        param.error_sistema(e=e, debug=f"{FUNCION}.obtener_registros_por_tramos.Excepcion")
        raise 

    finally:
        cursor_sqlserver.close()