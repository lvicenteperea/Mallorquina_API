
def obtener_campos_tabla(conn, id_tabla):

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM mll_campos WHERE ID_Tabla = %s", (id_tabla,))
    campos = cursor.fetchall()
    cursor.close()

    return campos

def crear_tabla_destino(conn_mysql, nombre_tabla, campos):
    cursor = conn_mysql.cursor()

    columnas = ", ".join([f"{campo['Nombre_Destino']} {campo['Tipo']}" for campo in campos])
    columnas += ", Origen_BBDD VARCHAR(100)"
    query = f"""CREATE TABLE IF NOT EXISTS {nombre_tabla} ({columnas},
            created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
            modified_by varchar(45) DEFAULT NULL )
            ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4"""

    cursor.execute(query)
    conn_mysql.commit()
    cursor.close()
    
def drop_tabla(conn_mysql, tabla):
    cursor_mysql = conn_mysql.cursor()
    cursor_mysql.execute(f"DROP TABLE IF EXISTS {tabla}")
    cursor_mysql.close()
