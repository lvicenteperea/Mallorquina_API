import pymysql

import json
from app.utils.utilidades import graba_log, imprime

def obtener_conexion_bbdd_origen(conn_mysql, id_bbdd):
    try:
        select = "SELECT Conexion FROM mll_cfg_bbdd WHERE ID = %s"
        donde = "select"
        # cursor_mysql = conn_mysql.cursor(dictionary=True)
        cursor_mysql = conn_mysql.cursor(pymysql.cursors.DictCursor)
        cursor_mysql.execute(select, (id_bbdd,))
        donde = "Conectado"

        conexion_json = cursor_mysql.fetchone()["Conexion"]
        donde = "conexion_json"

        conexion = json.loads(conexion_json)
        donde = "conexion"
        
        cursor_mysql.close()
        # conn.close()

        return conexion
    
    except Exception as e:
        graba_log({"ret_code": -1, "ret_txt": f"obtener_conexion_bbdd_origen: {donde}"}, "Excepción", e)
