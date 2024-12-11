import pandas as pd

# Cargar los archivos Excel
origen_path = "/mnt/data/export sql.xlsx"
destino_path = "/mnt/data/plantilla importa TPV.xlsx"

# Leer el archivo de origen y destino
origen_df = pd.read_excel(origen_path)
destino_df = pd.read_excel(destino_path)

# Crear un DataFrame vacío con las columnas del destino
columns_destino = [
    "Id Plato", "Descripcion", "Barra", "Comedor", "Terraza", "Hotel", 
    "Reservado", "Menú", "Orden Factura", "Orden Cocina", "OrdenTactil",
    "Grupo Carta 1", "Grupo Carta 2", "Grupo Carta 3", "Grupo Carta 4",
    "Familia", "Código Barras", "Centro", "Centro 2", "Centro 3"
]
converted_df = pd.DataFrame(columns=columns_destino)

# Mapear las columnas según las indicaciones
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

# Mapear centros de preparación a "X"
converted_df["Centro"] = origen_df["CENTRO PREPARACION CAFETERA"].apply(lambda x: "X" if not pd.isna(x) else "")
converted_df["Centro 2"] = origen_df["CENTRO PREPARACION PLANCHA"].apply(lambda x: "X" if not pd.isna(x) else "")
converted_df["Centro 3"] = origen_df["CENTRO PREPARACION COCINA"].apply(lambda x: "X" if not pd.isna(x) else "")

# Guardar el resultado
output_path = "/mnt/data/converted_plantilla_importa_TPV.xlsx"
converted_df.to_excel(output_path, index=False)

output_path
