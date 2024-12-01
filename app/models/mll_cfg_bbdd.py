import json
# from config.database import conexion_mysql

def obtener_conexion_bbdd_origen(conn, id_bbdd):
    # conn = conexion_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT Conexion FROM mll_cfg_bbdd WHERE ID = %s", (id_bbdd,))
    conexion_json = cursor.fetchone()["Conexion"]
    conexion = json.loads(conexion_json)
    cursor.close()
    # conn.close()
    return conexion
