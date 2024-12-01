from models.mll_tablas import obtener_campos_tabla, crear_tabla_destino #, drop_tabla
from models.mll_cfg_bbdd import obtener_conexion_bbdd_origen
from config.db_mallorquina import get_db_connection_sqlserver

def procesar_tabla(tabla, conn_mysql):
    # Obtener configuración y campos necesarios
    cursor_mysql = conn_mysql.cursor(dictionary=True)
    
    # Obtener nombre de la tabla y si se debe borrar
    cursor_mysql.execute("SELECT * FROM mll_tablas WHERE ID = %s", (tabla["ID_Tabla"],))

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

        # Preparar e insertar los registros en BD_Mallorquina
        # conn_mysql = conexion_mysql()
        cursor_mysql = conn_mysql.cursor()
        columnas_mysql = [campo["Nombre_Destino"] for campo in campos] + ["Origen_BBDD"]
        insert_query = f"""
            INSERT INTO {nombre_tabla_destino} ({', '.join(columnas_mysql)})
            VALUES ({', '.join(['%s'] * len(columnas_mysql))})
        """

        for registro in registros:
            registro_destino = list(registro) + [tabla["ID_BBDD"]]  # Añadimos el origen
            cursor_mysql.execute(insert_query, registro_destino)

        conn_mysql.commit()
        cursor_mysql.close()

    finally:
        conn_sqlserver.close()

