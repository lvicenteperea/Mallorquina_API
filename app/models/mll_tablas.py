from config.database import conexion_mysql


def obtener_campos_tabla(conn, id_tabla):
    # conn = conexion_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM mll_campos WHERE ID_Tabla = %s", (id_tabla,))
    campos = cursor.fetchall()
    cursor.close()
    # conn.close()
    return campos

def crear_tabla_destino(conn_mysql, nombre_tabla, campos):
    # conn_mysql = conexion_mysql()

    cursor = conn_mysql.cursor()

    columnas = ", ".join([f"{campo['Nombre_Destino']} {campo['Tipo']}" for campo in campos])
    columnas += ", Origen_BBDD VARCHAR(100)"
    query = f"CREATE TABLE IF NOT EXISTS {nombre_tabla} ({columnas})"

    cursor.execute(query)
    conn_mysql.commit()
    cursor.close()
    
def drop_tabla(conn_mysql, tabla):
    # conn_mysql = conexion_mysql()

    cursor_mysql = conn_mysql.cursor()
    cursor_mysql.execute(f"DROP TABLE IF EXISTS {tabla}")
    cursor_mysql.close()
    # conn_mysql.close()