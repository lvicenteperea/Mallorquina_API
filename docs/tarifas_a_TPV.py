import pandas as pd
# from openpyxl import Workbook, load_workbook
# from openpyxl.styles import Alignment
from datetime import datetime

# import os

from app.utils.functions import graba_log, imprime
from app.utils.mis_excepciones import MiException
from app.utils.InfoTransaccion import InfoTransaccion
from app.config.settings import settings

'''
SOL:
    Barra:   PVP TIENDA SOL,QUEVEDO,
    Comedor: PVP TIENDA SOL,QUEVEDO
    
QUEVEDO:
    Barra:  PVP TIENDA SOL,QUEVEDO
    Comedor: PVP TIENDA SOL,QUEVEDO
    Terraza: PVP TERRAZA QUEVEDO
MG:
    Barra: PVP TIENDA VELAZ,MORAL.
    Comedor: PVP TIENDA VELAZ,MORAL.
    
VELAZQUEZ:
    Barra: PVP TIENDA VELAZ,MORAL.
    Comedor: PVP TIENDA VELAZ,MORAL.

SALON_SOL:
    Barra: PVP SALON SOL
    Comedor: PVP SALON SOL

'''

PATH: str = f"{settings.RUTA_DATOS}tarifas_a_TPV/"
TIENDAS: str = {
                "SOL": {
                    "Barra": "PVP TIENDA SOL,QUEVEDO",
                    "Comedor": "PVP TIENDA SOL,QUEVEDO",
                    "Terraza": None
                },
                "QUEVEDO": {
                    "Barra": "PVP TIENDA SOL,QUEVEDO",
                    "Comedor": "PVP TIENDA SOL,QUEVEDO",
                    "Terraza": "PVP TERRAZA QUEVEDO"
                },
                "MG": {
                    "Barra": "PVP TIENDA VELAZ,MORAL.",
                    "Comedor": "PVP TIENDA VELAZ,MORAL.",
                    "Terraza": None
                },
                "VELAZQUEZ": {
                    "Barra": "PVP TIENDA VELAZ,MORAL.",
                    "Comedor": "PVP TIENDA VELAZ,MORAL.",
                    "Terraza": None
                },
                "SALON_SOL": {
                    "Barra": "PVP TIENDA SOL,QUEVEDO",
                    "Comedor": "PVP SALON SOL",
                    "Terraza": None
                }
               }

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def proceso(param: InfoTransaccion) -> list:
    """
    Convierte un archivo Excel de origen al formato deseado y lo guarda en el destino.

    Args:
        origen_path (str): Ruta del archivo de origen.
        output_path (str): Ruta donde se guardará el archivo convertido.

        origen_path = "app/datos/export_sqlpyme.xlsx"
        destino_path = "app/datos/importa_TPV.xlsx"
    """
    resultado = []
    param.debug = "proceso"

    try:
        if param.parametros and param.parametros[0]:
            origen_path = f"{PATH}{param.parametros[0]}"
        else:
            param.ret_code = -1
            param.ret_txt = "No ha llegado fichero origen para crear el nuevo fichero"
            return
                
        
        output_path = f"{PATH}tarifas_{datetime.now().strftime('%Y%m%d%H%M%S')}_"

        param.debug = "convierte_con_pd"
        resultado = convierte_con_pd(param, origen_path, output_path)
        
        return resultado

    except Exception as e:
        param.error_sistema(e=e)
        graba_log(param, "proceso.Exception", e)
        raise 
        

# -----------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------
def convierte_con_pd(param: InfoTransaccion, origen_path, output_path):
    resultado = []
    param.debug = "convierte_con_pd"
    
    try:
        error_log_path = f"{PATH}errores.log"
        errores = []

        origen_df = pd.read_excel(origen_path)
        num_registros_origen = origen_df.shape[0]

        origen_df["GRUPO DE CARTA VALIDADO"] = origen_df.apply(
            lambda row: row["GRUPO DE CARTA"] if validar_grupo_carta(row["GRUPO DE CARTA"], errores, row["Código"], row["Nombre"]) else None,
            axis=1
        )
        origen_df.dropna(subset=["GRUPO DE CARTA VALIDADO"], inplace=True)

        columns_destino = [
                            "Id Plato", "Descripcion", "Barra", "Comedor", "Terraza", "Hotel", 
                            "Reservado", "Menú", "Orden Factura", "Orden Cocina", "OrdenTactil",
                            "Grupo Carta 1", "Grupo Carta 2", "Grupo Carta 3", "Grupo Carta 4",
                            "Familia", "Código Barras", "Centro", "Centro 2", "Centro 3"
                          ]
        converted_df = pd.DataFrame(columns=columns_destino)
        #converted_df = pd.DataFrame()

        converted_df["Id Plato"] = origen_df["Código"]
        converted_df["Descripcion"] = origen_df["Nombre"]

        # converted_df["Código Barras"] = validar_codigo_barras(origen_df["Código de barras"], origen_df["Código"]) # origen_df["Código de barras"].apply(validar_codigo_barras)
        converted_df["Código Barras"] = origen_df["Código de barras"].apply(lambda x: str(x).split('.')[0] if pd.notna(x) else "")

        converted_df["Hotel"] = ""
        converted_df["Reservado"] = ""
        converted_df["Menú"] = ""
        converted_df["Orden Factura"] = ""
        converted_df["Orden Cocina"] = ""
        converted_df["OrdenTactil"] = ""
        converted_df["Grupo Carta 1"] = origen_df["GRUPO DE CARTA"]
        converted_df["Grupo Carta 2"] = ""
        converted_df["Grupo Carta 3"] = ""
        converted_df["Grupo Carta 4"] = ""
        converted_df["Familia"] = ""
        converted_df["Centro"] = origen_df["CENTRO PREPARACION CAFETERA"] # .apply(lambda x: "X" if not pd.isna(x) else "")
        converted_df["Centro 2"] = origen_df["CENTRO PREPARACION PLANCHA"] # .apply(lambda x: "X" if not pd.isna(x) else "")
        converted_df["Centro 3"] = origen_df["CENTRO PREPARACION COCINA"] # .apply(lambda x: "X" if not pd.isna(x) else "")

        for tienda, config in TIENDAS.items():
            df_tienda = converted_df.copy()

            # df_tienda["Barra"] = origen_df[config["Barra"]].apply(limpiar_ceros) if config["Barra"] else ""
            # df_tienda["Comedor"] = origen_df[config["Comedor"]].apply(limpiar_ceros) if config["Comedor"] else ""
            # df_tienda["Terraza"] = origen_df[config["Terraza"]].apply(limpiar_ceros) if config["Terraza"] else ""

            df_tienda["Barra"] = origen_df[config["Barra"]].apply(lambda x: limpiar_ceros(str(x)).replace(',', '.')) if config["Barra"] else ""
            df_tienda["Comedor"] = origen_df[config["Comedor"]].apply(lambda x: limpiar_ceros(str(x)).replace(',', '.')) if config["Comedor"] else ""
            df_tienda["Terraza"] = origen_df[config["Terraza"]].apply(lambda x: limpiar_ceros(str(x)).replace(',', '.')) if config["Terraza"] else ""




            df_tienda = df_tienda[
                (df_tienda["Barra"] != "") |
                (df_tienda["Comedor"] != "") |
                (df_tienda["Terraza"] != "")
            ]

            fic_salida = f"{output_path}{tienda}.xlsx"
            if not df_tienda.empty:
                df_tienda.to_excel(fic_salida, index=False)
                resultado.append(f"Archivo generado para tienda: {tienda} con {df_tienda.shape[0]} registros de un total de {num_registros_origen}")

        if errores:
            with open(error_log_path, "w") as error_file:
                for error in errores:
                    error_file.write(error + "\n")

        return resultado

    except Exception as e:
        param.error_sistema(e=e)
        graba_log(param, "proceso.Exception", e)
        raise

# -----------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------
def limpiar_ceros(valor):
    if pd.isna(valor) or str(valor).strip() == "" or str(valor).strip() == "0" or valor == 0:
        return ""
    return valor

# -----------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------
def validar_codigo_barras(codigo_barras, codigo_erp):
    # if pd.isna(codigo_barras) or len(str(codigo_barras).strip()) <= 6:
    if isinstance(codigo_barras, pd.Series):
        return codigo_barras.apply(lambda x: "" if pd.isna(x) or len(str(x).strip()) <= 6 else str(x))
    
    if pd.isna(codigo_barras) or len(str(codigo_barras).strip()) <= 6:
        return ""

    return codigo_barras

# -----------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------
def validar_grupo_carta(grupo, errores, id_plato, nombre):
    try:
        grupo = int(grupo)  # Convertir a entero para comparación correcta
    except (ValueError, TypeError):
        errores.append(f"{id_plato} - {nombre} - Producto sin número de carta")
        return False

    if grupo not in range(1, 9):
        errores.append(f"{id_plato} - {nombre} - Producto con nº de carta fuera de rango")
        return False
    
    return True




'''
# -----------------------------------------------------------------------------------------------------
# Salon Sol: Barra y comedor
# Sol Quevedo: Barra, comedor y teerraza
# Velazquez la moraleja: Barra y comedor
# -----------------------------------------------------------------------------------------------------
def convierte_con_pd (param: InfoTransaccion, origen_path, output_path):
    resultado = []
    param.debug = "convierte_con_pd"
    
    try:
        #Leer el archivo de origen
        origen_df = pd.read_excel(origen_path)

        param.debug = "# Crear un DataFrame vacío con las columnas deseadas"
        columns_destino = [
            "Id Plato", "Descripcion", "Barra", "Comedor", "Terraza", "Hotel", 
            "Reservado", "Menú", "Orden Factura", "Orden Cocina", "OrdenTactil",
            "Grupo Carta 1", "Grupo Carta 2", "Grupo Carta 3", "Grupo Carta 4",
            "Familia", "Código Barras", "Centro", "Centro 2", "Centro 3"
        ]
        converted_df = pd.DataFrame(columns=columns_destino)

        param.debug = "# Mapear las columnas según las indicaciones"
        converted_df["Id Plato"] = origen_df["Código"]
        converted_df["Descripcion"] = origen_df["Nombre"]
        converted_df["Barra"] = origen_df["PVP TIENDA SOL,QUEVEDO"] # ["PVP TIENDA VELAZ,MORAL."]
        converted_df["Comedor"] = origen_df["PVP SALON TIENDAS"]  # ["PVP SALON SOL"]
        converted_df["Terraza"] = origen_df["PVP TERRAZA QUEVEDO"]
        converted_df["Hotel"] = ""
        converted_df["Reservado"] = ""
        converted_df["Menú"] = ""
        converted_df["Orden Factura"] = ""
        converted_df["Orden Cocina"] = ""
        converted_df["OrdenTactil"] = ""
        converted_df["Grupo Carta 1"] = origen_df["GRUPO DE CARTA"]
        converted_df["Grupo Carta 2"] = ""
        converted_df["Grupo Carta 3"] = ""
        converted_df["Grupo Carta 4"] = ""
        converted_df["Familia"] = ""
        converted_df["Código Barras"] = origen_df["Código de barras"]

        param.debug = "# Mapear centros de preparación a 'X'"
        converted_df["Centro"] = origen_df["CENTRO PREPARACION CAFETERA"].apply(lambda x: "X" if not pd.isna(x) else "")
        converted_df["Centro 2"] = origen_df["CENTRO PREPARACION PLANCHA"].apply(lambda x: "X" if not pd.isna(x) else "")
        converted_df["Centro 3"] = origen_df["CENTRO PREPARACION COCINA"].apply(lambda x: "X" if not pd.isna(x) else "")

        # Guardar el DataFrame convertido en el archivo de destino"
        param.debug = f"Guarda el archivo {output_path}.   "
        converted_df.to_excel(output_path, index=False)
        
        param.debug = f"# Contar registros generados"
        num_registros_destino = converted_df.shape[0]
        num_registros_origen = origen_df.shape[0]
        
        if num_registros_origen == num_registros_destino:
            param.ret_code = 0
            param.ret_txt = f"Ok: Ambos archivos ({origen_path} y {output_path}) tienen {num_registros_origen} registros"
        else:
            param.ret_code = -1
            param.ret_txt = f"Error: El archivo origen ({origen_path}) tiene {num_registros_origen} registros. El archivo generado ({output_path}) tiene {num_registros_destino} registros."
        
        resultado = [num_registros_origen , num_registros_destino]
        return resultado

    except Exception as e:
        param.error_sistema(e=e)
        graba_log(param, "proceso.Exception", e)
        raise         

'''