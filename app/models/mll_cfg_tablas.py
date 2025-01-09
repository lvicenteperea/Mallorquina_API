import re
#from app.utils.functions import imprime

def obtener_campos_tabla(conn, id_tabla):

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM mll_cfg_campos WHERE ID_Tabla = %s", (id_tabla,))
    campos = cursor.fetchall()
    cursor.close()

    return campos

def crear_tabla_destino(conn_mysql, nombre_tabla, campos):
    cursor = conn_mysql.cursor()

    # columnas = ", ".join([f"{campo['Nombre_Destino']} {campo['Tipo']}" for campo in campos])
    """
    re.search(r'{(.+?)}', campo['Nombre']):
        - Busca contenido dentro de las llaves {} en campo['Nombre'].
        - Si encuentra algo, devuelve un objeto de búsqueda (Match).
    
    re.search(...).group(1):
        - Extrae el contenido dentro de las llaves {} (el texto sin las llaves).
    
    {'default ' + contenido if ... else ''}:
        - Si el contenido dentro de las llaves existe, añade default seguido del contenido extraído.
        - Si no hay llaves, no añade nada adicional.
    
    .strip():
        - Elimina espacios adicionales al final de la cadena generada.
    """
    columnas = ", ".join([
        f"{campo['Nombre_Destino']} {campo['Tipo']} {'default ' + re.search(r'{(.+?)}', campo['Nombre']).group(1) if re.search(r'{(.+?)}', campo['Nombre']) else ''}".strip()
        for campo in campos
    ])


    columnas += ", Origen_BBDD VARCHAR(100)"
    query = f"""CREATE TABLE IF NOT EXISTS {nombre_tabla} 
                    (ID INT NOT NULL AUTO_INCREMENT,
                     {columnas},
                     created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
                     updated_at timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
                     modified_by varchar(45) DEFAULT NULL,
                     PRIMARY KEY (`ID`))
                ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4"""
    #imprime(query, "=")
    cursor.execute(query)
    conn_mysql.commit()
    cursor.close()
    
def drop_tabla(conn_mysql, tabla):
    cursor_mysql = conn_mysql.cursor()
    cursor_mysql.execute(f"DROP TABLE IF EXISTS {tabla}")
    cursor_mysql.close()
