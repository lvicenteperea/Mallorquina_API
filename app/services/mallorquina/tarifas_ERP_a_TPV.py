import pandas as pd
from datetime import datetime

from app.utils.functions import graba_log, imprime
from app.utils.mis_excepciones import MadreException
from app.utils.InfoTransaccion import InfoTransaccion
from app.config.settings import settings


PATH: str = f"{settings.RUTA_DATOS}tarifas_a_TPV/"
# Definición de las tiendas y su correspondencia con id_bbdd
TIENDAS = {
    5: "Sol",
    4: "Quevedo",
    1: "Velazquez",
    6: "Moraleja",
    7: "Salon_SOL"
}

COLUMNAS_EXCEL = [
    "Id Plato", "Descripcion", "Barra", "Comedor", "Terraza", "Hotel",
    "Reservado", "Menú", "Orden Factura", "Orden Cocina", "OrdenTactil",
    "Grupo Carta 1", "Grupo Carta 2", "Grupo Carta 3", "Grupo Carta 4",
    "Familia", "Código Barras", "Centro", "Centro 2", "Centro 3"
]

# Consulta SQL para obtener los datos de ambas tablas
QUERY = """
SELECT 
    p.ID AS 'Id Plato', 
    p.nombre AS 'Descripcion',
    p.codigo_barras AS 'Código Barras',
    p.grupo_de_carta AS 'Grupo Carta 1',
    p.centro_preparacion_1 AS 'Centro',
    p.centro_preparacion_2 AS 'Centro 2',
    p.centro_preparacion_3 AS 'Centro 3',
    pv.id_bbdd,
    pv.tipo,
    pv.pvp
FROM erp_productos p
LEFT JOIN erp_productos_pvp pv ON p.ID = pv.id_producto
WHERE pv.id_bbdd IN (1, 4, 5, 6, 7)
"""





#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def proceso(param: InfoTransaccion) -> list:
    resultado = []
    param.debug = "proceso"

    try:
        output_path = f"{PATH}tarifas_{datetime.now().strftime('%Y%m%d%H%M%S')}_"

        print("5---------------------------------------- ")
        df = obtener_datos(param)
        resultado = generar_excel(param, df, output_path)
        
        return resultado

    except Exception as e:
        param.error_sistema()
        graba_log(param, "proceso.Exception", e)
        raise 
        

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
# Generar los archivos Excel por tienda
def generar_excel(param: InfoTransaccion, df, output_path: str) -> list:
    resultado = []
    print("1---------------------------------------- ")
    try:
        for id_bbdd, tienda in TIENDAS.items():
            df_tienda = df[df["id_bbdd"] == id_bbdd]

            # Preparar datos para el archivo de cada tienda
            data = []
            for producto_id in df_tienda["Id Plato"].unique():
                producto = df_tienda[df_tienda["Id Plato"] == producto_id]

                barra = producto.loc[producto["tipo"] == "Barra", "pvp"].values[0] if "Barra" in producto["tipo"].values else ""
                comedor = producto.loc[producto["tipo"] == "Comedor", "pvp"].values[0] if "Comedor" in producto["tipo"].values else ""
                terraza = producto.loc[producto["tipo"] == "Terraza", "pvp"].values[0] if "Terraza" in producto["tipo"].values else ""

                # Si todas las columnas de precio están vacías, omitir el registro
                if not barra and not comedor and not terraza:
                    continue

                data.append([
                    producto.iloc[0]["Id Plato"],
                    producto.iloc[0]["Descripcion"],
                    barra, comedor, terraza,
                    "", "", "", "", "", "",
                    producto.iloc[0]["Grupo Carta 1"], "", "", "",
                    "", producto.iloc[0]["Código Barras"],
                    producto.iloc[0]["Centro"], producto.iloc[0]["Centro 2"], producto.iloc[0]["Centro 3"]
                ])

            filas = len(data)
            print("2---------------------------------------- ")
            if filas == 0:
                print(f"No hay datos para la tienda {tienda}")
                resultado.append(f"No hay datos para la tienda {tienda}")
            else:
                # Crear DataFrame y exportar a Excel
                df_export = pd.DataFrame(data, columns=COLUMNAS_EXCEL)
                output_file = f"{output_path}{tienda}.xlsx"
                df_export.to_excel(output_file, index=False)
                print(f"Archivo generado: {output_file}")
                resultado.append(f'Archivo "{output_file}" generado  con {len(data)}')

        return resultado

    except Exception as e:
        print("3---------------------------------------- ")
        param.error_sistema()
        graba_log(param, "proceso.Exception", e)
        raise 
#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
# Conectar a la base de datos y obtener los datos

from app.config.db_mallorquina import get_db_connection_mysql, close_connection_mysql

def obtener_datos(param: InfoTransaccion) -> pd.DataFrame:
    try: 
        print("4---------------------------------------- ")
        param.debug = "obtener_datos"
        conn_mysql = get_db_connection_mysql()

        param.debug = "read_sql_query"
        df = pd.read_sql_query(QUERY, conn_mysql)

        conn_mysql.close()
        return df

    except Exception as e:
        param.error_sistema()
        graba_log(param, "obtener_datos.Exception", e)
        raise 

    finally:
        close_connection_mysql(conn=conn_mysql, cursor=None)