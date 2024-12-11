from app.models.mll_cfg_tablas import obtener_campos_tabla, crear_tabla_destino #, drop_tabla
from app.models.mll_cfg_bbdd import obtener_conexion_bbdd_origen
from app.config.db_mallorquina import get_db_connection_sqlserver

def procesar_tabla(tabla, conn_mysql):
    # Obtener configuración y campos necesarios
    cursor_mysql = conn_mysql.cursor(dictionary=True)
    
    # Obtener nombre de la tabla y si se debe borrar
    cursor_mysql.execute("SELECT * FROM mll_cfg_tablas WHERE ID = %s", (tabla["ID_Tabla"],))

    tabla_config = cursor_mysql.fetchone()
    nombre_tabla = tabla_config["Tabla_Origen"]
    nombre_tabla_destino = tabla_config["Tabla_Destino"]
    # borrar_tabla = tabla_config["Borrar_Tabla"]
    cursor_mysql.close()

    # Obtener campos de la tabla
    campos = obtener_campos_tabla(conn_mysql, tabla["ID_Tabla"])

    '''
    no puede estar aquí porque cada vez que lea una bbdd diferente borro la tabla y solo se debe borrar en la primera carga, si podemos hacer esto.
    # Borrar tabla si corresponde
    if borrar_tabla:
       drop_tabla(conn_mysql, nombre_tabla_destino)
    '''

    # Crear tabla si no existe
    crear_tabla_destino(conn_mysql, nombre_tabla_destino, campos)

    # Buscamos la conexión que necesitamos para esta bbdd origen
    bbdd_config = obtener_conexion_bbdd_origen(conn_mysql,tabla["ID_BBDD"])

    # conextamos con esta bbdd origen
    conn_sqlserver = get_db_connection_sqlserver(bbdd_config)

    try:
        # Leer datos desde SQL Server
        cursor_sqlserver = conn_sqlserver.cursor()
        select_query = f"SELECT {', '.join([campo['Nombre'] for campo in campos])} FROM {nombre_tabla}"
        cursor_sqlserver.execute(select_query)
        registros = cursor_sqlserver.fetchall()

        # Preparar los cursores para MySQL
        cursor_mysql = conn_mysql.cursor()
        columnas_mysql = [campo["Nombre_Destino"] for campo in campos] + ["Origen_BBDD"]

        # Identificar el campo PK basado en mll_cfg_campos
        pk_campos = [campo for campo in campos if campo.get("PK", 0) >= 1]
        if not pk_campos:
            raise ValueError(f"No se encontró ningún campo PK en {nombre_tabla}.")

        # Usamos el primer campo PK encontrado
        pk_campo = pk_campos[0]["Nombre_Destino"]

        # Generar consultas dinámicas
        insert_query = f"""
            INSERT INTO {nombre_tabla_destino} ({', '.join(columnas_mysql)})
            VALUES ({', '.join(['%s'] * len(columnas_mysql))})
        """
        # update_query = f"""
        #     UPDATE {nombre_tabla_destino}
        #     SET {', '.join([f'{campo["Nombre_Destino"]} = %s' for campo in campos])}
        #     WHERE {pk_campo} = %s AND Origen_BBDD = %s
        # """
        campos_update = [campo for campo in campos if campo["Nombre_Destino"] != pk_campo]
        update_query = f"""
            UPDATE {nombre_tabla_destino}
            SET {', '.join([f'{campo["Nombre_Destino"]} = %s' for campo in campos_update])}
            WHERE {pk_campo} = %s AND Origen_BBDD = %s
        """

        for registro in registros:
            # Obtener el valor del campo PK desde el registro
            pk_index = [campo["Nombre"] for campo in campos].index(pk_campos[0]["Nombre"])
            pk_value = registro[pk_index]

            select = f"""SELECT COUNT(*) 
                                       FROM {nombre_tabla_destino} 
                                      WHERE {pk_campo} = %s
                                        AND Origen_BBDD = {tabla["ID_BBDD"]}"""

            # Comprobar si el registro ya existe en la tabla destino
            cursor_mysql.execute(select, (pk_value,))
            existe = cursor_mysql.fetchone()[0] > 0  # Si existe, devuelve True

            if existe:
                # Realizar un UPDATE
                valores_update = list(registro) + [tabla["ID_BBDD"], pk_value]  # Campos + Origen + PK
                valores_update = [registro[[campo["Nombre"] for campo in campos].index(campo["Nombre"])]
                                            for campo in campos_update] + [pk_value, tabla["ID_BBDD"]]
                cursor_mysql.execute(update_query, valores_update)
            else:
                # Realizar un INSERT
                registro_destino = list(registro) + [tabla["ID_BBDD"]]  # Campos + Origen
                cursor_mysql.execute(insert_query, registro_destino)

        conn_mysql.commit()
        cursor_mysql.close()

    finally:
        conn_sqlserver.close()
