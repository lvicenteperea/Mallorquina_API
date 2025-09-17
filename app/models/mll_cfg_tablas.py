import pymysql

from app.utils.utilidades import graba_log
from app.utils.InfoTransaccion import InfoTransaccion

#----------------------------------------------------------------------------------------     
#----------------------------------------------------------------------------------------
def obtener_campos_tabla(conn_mysql, id_entidad, id_tabla):
    query = """SELECT a.*, b.ult_valor FROM mll_cfg_campos a
                inner join mll_cfg_tablas_entidades b on a.id_tabla = b.id_tabla and id_entidad = %s
                WHERE a.ID_Tabla = %s
                ORDER BY a.orden"""
                # ORDER BY CASE 
				#			WHEN a.PK = 0 THEN 99 
				#			ELSE a.PK 
				#		   END"""
    # cursor_mysql = conn_mysql.cursor(dictionary=True)
    cursor_mysql = conn_mysql.cursor(pymysql.cursors.DictCursor)
    cursor_mysql.execute(query, (id_entidad, id_tabla))
    campos = cursor_mysql.fetchall()
    cursor_mysql.close()

    return campos

#----------------------------------------------------------------------------------------
# #----------------------------------------------------------------------------------------
def crear_tabla_destino(param: InfoTransaccion, conn_mysql, nombre_tabla, campos):
    try:
        param.debug = "Creando tabla destino"
        cursor = conn_mysql.cursor()
        columnas = None

        from datetime import datetime

        # Lista de datos simulada
        resultado = []

        for item in campos:
            nombre = item["Nombre"].strip("{}")
            nombre_destino = item["Nombre_Destino"]
            tipo = item["Tipo"]

            if nombre == "stIdEnt":
                resultado.append(f"{nombre_destino} {tipo} DEFAULT 'SIN DEFINIR'")
            elif "{" in nombre and "}" in nombre:
                valor_entre_llaves = nombre.strip("{}")
                resultado.append(f"{nombre_destino} {tipo} DEFAULT {valor_entre_llaves}")
            else:
                resultado.append(f"{nombre_destino} {tipo}")

        if len(resultado) == 0:
            raise f"No hay columnas definidas para la tabla {nombre_tabla}"

        # Unir los elementos con coma, excepto el último
        columnas = ", ".join(resultado)
        columnas += ", Origen_BBDD VARCHAR(100)"

        query = f"""CREATE TABLE IF NOT EXISTS {nombre_tabla} 
                        (ID INT NOT NULL AUTO_INCREMENT,
                        {columnas},
                        created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
                        modified_by varchar(45) DEFAULT NULL,
                        PRIMARY KEY (`ID`))
                    ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4"""

        param.debug = query
        cursor.execute(query)
        conn_mysql.commit()

    except Exception as e:
        param.error_sistema(e=e, debug="recorre_tiendas.Exception")
        raise e
    
    finally:
        cursor.close()
    
#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def drop_tabla(conn_mysql, tabla):
    cursor_mysql = conn_mysql.cursor()
    cursor_mysql.execute(f"DROP TABLE IF EXISTS {tabla}")
    cursor_mysql.close()
