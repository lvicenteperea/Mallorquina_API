import pandas as pd
from app.utils.functions import graba_log
from fastapi import HTTPException
from app.utils.InfoTransaccion import InfoTransaccion

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def proceso(param: InfoTransaccion) -> InfoTransaccion:
    """
    Convierte un archivo Excel de origen al formato deseado y lo guarda en el destino.

    Args:
        origen_path (str): Ruta del archivo de origen.
        output_path (str): Ruta donde se guardará el archivo convertido.

        origen_path = "app/datos/export_sqlpyme.xlsx"
        destino_path = "app/datos/importa_TPV.xlsx"
    """
    resultado = []
    path = "app/datos/"
    origen_path = f"{path}{param.parametros[0]}"
    output_path = f"{path}{param.parametros[1]}"
    try:
        donde = "#Leer el archivo de origen"
        origen_df = pd.read_excel(origen_path)

        donde = "# Crear un DataFrame vacío con las columnas deseadas"
        columns_destino = [
            "Id Plato", "Descripcion", "Barra", "Comedor", "Terraza", "Hotel", 
            "Reservado", "Menú", "Orden Factura", "Orden Cocina", "OrdenTactil",
            "Grupo Carta 1", "Grupo Carta 2", "Grupo Carta 3", "Grupo Carta 4",
            "Familia", "Código Barras", "Centro", "Centro 2", "Centro 3"
        ]
        converted_df = pd.DataFrame(columns=columns_destino)

        donde = "# Mapear las columnas según las indicaciones"
        converted_df["Id Plato"] = origen_df["Código"]
        converted_df["Descripcion"] = origen_df["Nombre"]
        converted_df["Barra"] = origen_df["PVP TIENDA"]
        converted_df["Comedor"] = origen_df["PVP SALON TIENDAS"]
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

        donde = "# Mapear centros de preparación a 'X'"
        converted_df["Centro"] = origen_df["CENTRO PREPARACION CAFETERA"].apply(lambda x: "X" if not pd.isna(x) else "")
        converted_df["Centro 2"] = origen_df["CENTRO PREPARACION PLANCHA"].apply(lambda x: "X" if not pd.isna(x) else "")
        converted_df["Centro 3"] = origen_df["CENTRO PREPARACION COCINA"].apply(lambda x: "X" if not pd.isna(x) else "")

        donde = "# Guardar el DataFrame convertido en el archivo de destino"
        converted_df.to_excel(output_path, index=False)
        
        donde = f"# Contar registros generados"
        num_registros_destino = converted_df.shape[0]
        num_registros_origen = origen_df.shape[0]
        
        if num_registros_origen == num_registros_destino:
            param.ret_code = 0
            param.ret_txt = f"Ok: Ambos archivos tienen {num_registros_origen} registros"
        else:
            param.ret_code = -1
            param.ret_txt = f"Error: El archivo origen tiene {num_registros_origen} registros. El archivo generado tiene {num_registros_destino} registros."
        raise

    except Exception as e:
        param.ret_code = -1
        param.ret_txt = "Error general. contacte con su administrador"
        graba_log({"ret_code": param.ret_code, "ret_txt": param.ret_txt}, f"Excepción convierte_excel.proceso-{donde}", e)
       

    finally:
        return InfoTransaccion( id_App=param.id_App, 
                        user=param.user, 
                        ret_code=param.ret_code, 
                        ret_txt=param.ret_txt,
                        parametros=param.parametros,
                        resultados = resultado
                        )
