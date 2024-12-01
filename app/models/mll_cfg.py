from app.config.db_mallorquina import get_db_connection_mysql, close_connection_mysql

#----------------------------------------------------------------------------------------
def obtener_configuracion_general():
    conn = get_db_connection_mysql()

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM mll_cfg LIMIT 1")
    config = cursor.fetchone()

    close_connection_mysql(conn, cursor)
    return config

#----------------------------------------------------------------------------------------
def actualizar_en_ejecucion(estado):
    conn = get_db_connection_mysql()

    cursor = conn.cursor()
    cursor.execute("UPDATE mll_cfg SET En_Ejecucion = %s", (estado,))
    conn.commit()

    close_connection_mysql(conn, cursor)
