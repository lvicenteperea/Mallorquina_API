from fastapi import HTTPException
from app.models.mll_cfg_tablas import obtener_campos_tabla, crear_tabla_destino #, drop_tabla
from app.models.mll_cfg_bbdd import obtener_conexion_bbdd_origen
from app.config.db_mallorquina import get_db_connection_sqlserver

from app.utils.functions import graba_log

import pyodbc






def row_to_dict(row, cursor):
    # print("Obtener los nombres de las columnas")
    columns = [column[0] for column in cursor.description]
    # print("columnas ", columns)

    # Combinar los nombres de las columnas con los valores del row
    datos = dict(zip(columns, row))
    # print("datos ", datos)
    return datos
    





#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
def procesar_consulta(tabla, conn_mysql, param) -> list:

    try:
        # Buscamos la conexión que necesitamos para esta bbdd origen
        bbdd_config = obtener_conexion_bbdd_origen(conn_mysql,tabla["ID_BBDD"])

        # conextamos con esta bbdd origen
        conn_sqlserver = get_db_connection_sqlserver(bbdd_config)

        if conn_sqlserver:
            # Leer datos desde SQL Server
            cursor_sqlserver = conn_sqlserver.cursor()

            # Averiguamos los IDs de dia de cierre de caja:
            placeholders = "?"
            # en realidad parametros solo tiene un elemento que es la fecha y debe ser en formato aaaa-mm-dd
            select_query = f"""SELECT [Id Cierre]
                                FROM [Cierres de Caja] WHERE CAST(Fecha AS DATE) = ?
                    """
            cursor_sqlserver.execute(select_query, param.parametros)

            apertura_ids_lista = cursor_sqlserver.fetchall()
            # Convertir el resultado de fetchall a una lista de valores
            apertura_ids = ",".join(str(row[0]) for row in apertura_ids_lista)

            # buscamos los cierres de estos IDs
            apertura_ids = [8285, 8286, 8287, 8288]
            placeholders = ", ".join(["?"] * len(apertura_ids))
            select_query = f"""SELECT [Id Apertura],
                                    [Fecha Hora],
                                    [Id Cobro],
                                    [Descripcion],
                                    [Importe],
                                    [Realizado],
                                    [Id Rel],
                                    {tabla["ID_BBDD"]}
                                FROM [Arqueo Ciego]
                                WHERE [Id Apertura] IN ({placeholders})
                                ORDER BY Descripcion
                    """
            cursor_sqlserver.execute(select_query, apertura_ids)

            resultado = cursor_sqlserver.fetchall()

            if isinstance(resultado, pyodbc.Row):
                if isinstance(row, pyodbc.Row):
                    # Convertir pyodbc.Row a diccionario
                    resultado[idx] = row_to_dict(row, cursor_sqlserver)  # Usa el cursor que generó la fila
            elif isinstance(resultado, list):
                for idx, row in enumerate(resultado):
                    # print(f"Fila {idx}: {type(row)}")  # Imprimir el tipo de cada fila

                    if isinstance(row, pyodbc.Row):
                        # print("Convertir pyodbc.Row a diccionario")
                        resultado[idx] = row_to_dict(row, cursor_sqlserver)  # Usa el cursor que generó la fila
        else:
            resultado = []

        return resultado

    except Exception as e:
        graba_log({"ret_code": -3, "ret_txt": str(e)}, "Excepción", e)
        resultado = []

    finally:
        if conn_sqlserver:
            conn_sqlserver.close()

        return resultado

    