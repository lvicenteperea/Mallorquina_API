import pandas as pd
from datetime import datetime
from fastapi import HTTPException
from jinja2 import Template

import os

from app.utils.functions import graba_log, imprime
from app.utils.mis_excepciones import MadreException
from app.utils.InfoTransaccion import InfoTransaccion
from app.config.settings import settings

# Rutas de los archivos
RUTA_ICONOS = os.path.join("D:/Nube/GitHub/Mallorquina_API/", settings.RUTA_IMAGEN, "alergenos/")
RUTA_LOGO = os.path.join("D:/Nube/GitHub/Mallorquina_API/", settings.RUTA_IMAGEN, "Logotipo con tagline - negro.svg")
RUTA_EXCEL = os.path.join(settings.RUTA_DATOS, "alergenos/fichas_tecnicas.xlsx")
RUTA_PLANTILLA = os.path.join(settings.RUTA_DATOS, "alergenos/plantilla_html_FT.txt")
RUTA_PLANTILLA_PROD = os.path.join(settings.RUTA_DATOS, "alergenos/plantilla_producto_FT.txt")
RUTA_HTML = os.path.join(settings.RUTA_DATOS, "alergenos/fichas_tecnicas.html")


#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
# Leer el archivo Excel
def leer_excel():
    try:
        df = pd.read_excel(RUTA_EXCEL)
        return df
    except Exception as e:
        print(f"Error al leer el archivo Excel: {e}")
        exit()

#----------------------------------------------------------------------------------------
# Generar índice con filtro y orden
#----------------------------------------------------------------------------------------
def generar_indice(df, ordenar_por):
    df_filtrado = df[df['TPV'] == 'Sí']
    df_ordenado = df_filtrado.sort_values(by=ordenar_por)
    indice_html = "<ul>"
    #cabeceras=df.columns.tolist()
    for _, row in df_ordenado.iterrows():
        codigo = row['Código']
        nombre = row['Nombre']
        alergenos = ''.join(
            f'<img src="{os.path.join(RUTA_ICONOS, col+ ".webp")}" alt="{col}" class="icono-alergeno">'
            for col in df.columns[3:17] if row[col] in ['Sí', 'Traza']
        )
        indice_html += f"<li><a href='#{codigo}'  class='icono-alergeno'>{codigo} - {nombre.capitalize()}</a> {alergenos}</li>\n"
    
    indice_html += "</ul>"
    return indice_html

#----------------------------------------------------------------------------------------
# Generar fichas técnicas
#----------------------------------------------------------------------------------------
def generar_fichas(df):
    plantilla = ""
    fichas_html = ""
    
    # Cargamos la platilla de la FICHA de un producto en una variable
    with open(RUTA_PLANTILLA_PROD, "r", encoding="utf-8") as archivo:
        plantilla = archivo.read()

    #print(df.columns.tolist())
    #['Código', 'Nombre', 'Listado alergenos', 'Huevo', 'Lacteos', 'Crustaceos', 'Cascara', 'Gluten', 'Pescado', 
    # 'Altramuz', 'Mostaza', 'Cacahuetes', 'Apio', 'Sulfitos', 'Soja', 'Moluscos', 'Sésamo', 'Población diana', 
    # 'Uso esperado', 'Condiciones almacenamiento', 'Condiciones conservación', 'Vida frío desde fabric.', 
    # 'Peso neto aprox.', 'Composición del producto', 'Rec. Aerobios totales', 'Rec. Enterobacterias', 
    # 'Rec. Escherichia Coli', 'Rec. Staphylococcus Aureus', 'Det. Salmonella cpp', 'Rec. Listeria Monocytogenes', 
    # 'Rec. Mohos y levaduras', 'Valor_energetico_Kcal_Kj', 'Grasas_g', 'De_las_cuales_SATURADAS_g', 'Hidratos_de_carbono_g', 
    # 'De_los_cuales_AZUCARES_g', 'Proteinas_g', 'Sal_g', 'Fibra_dietetica_g', 'Otros', 'TEMPORADA', 'Descripción', 'Código.1', 
    # 'TPV', 'GRUPO DE CARTA']

    for _, row in df.iterrows():
        ficha = plantilla.format(
            codigo=row.get('Código', ''),
            nombre=row.get('Nombre', ''),
            temporada=row.get('Temporada', ''),
            categoria=row.get('Categoría', ''),
            composicion=row.get('Composición del producto', ''),
            Composicion_del_producto = '' if pd.isna(row.get('Composición del producto', '')) else row.get('Composición del producto', ''),

            Gluten      = "X" if row.get('Gluten', '') == "Sí" else "Traza" if row.get('Gluten', '') == "Traza" else "",
            Cascara     = "X" if row.get('Cascara', '') == "Sí" else "Traza" if row.get('Cascara', '') == "Traza" else "",
            Crustaceos  = "X" if row.get('Crustaceos', '') == "Sí" else "Traza" if row.get('Crustaceos', '') == "Traza" else "",
            Apio        = "X" if row.get('Apio', '') == "Sí" else "Traza" if row.get('Apio', '') == "Traza" else "",
            Huevo       = "X" if row.get('Huevo', '') == "Sí" else "Traza" if row.get('Huevo', '') == "Traza" else "",
            Mostaza     = "X" if row.get('Mostaza', '') == "Sí" else "Traza" if row.get('Mostaza', '') == "Traza" else "",
            Pescado     = "X" if row.get('Pescado', '') == "Sí" else "Traza" if row.get('Pescado', '') == "Traza" else "",
            Sésamo      = "X" if row.get('Sésamo', '') == "Sí" else "Traza" if row.get('Sésamo', '') == "Traza" else "",
            Cacahuetes  = "X" if row.get('Cacahuetes', '') == "Sí" else "Traza" if row.get('Cacahuetes', '') == "Traza" else "",
            Sulfitos    = "X" if row.get('Sulfitos', '') == "Sí" else "Traza" if row.get('Sulfitos', '') == "Traza" else "",
            Soja        = "X" if row.get('Soja', '') == "Sí" else "Traza" if row.get('Soja', '') == "Traza" else "",
            Altramuz    = "X" if row.get('Altramuz', '') == "Sí" else "Traza" if row.get('Altramuz', '') == "Traza" else "",
            Leche       = "X" if row.get('Leche', '') == "Sí" else "Traza" if row.get('Leche', '') == "Traza" else "",
            Moluscos    = "X" if row.get('Moluscos', '') == "Sí" else "Traza" if row.get('Moluscos', '') == "Traza" else "",

            Valor_energetico_Kcal_Kj = row.get('Valor_energetico_Kcal_Kj', ''),
            Grasas_g = row.get('Grasas_g', ''),
            De_las_cuales_SATURADAS_g = row.get('De_las_cuales_SATURADAS_g', ''),
            Hidratos_de_carbono_g = row.get('Hidratos_de_carbono_g', ''),
            De_los_cuales_AZUCARES_g = row.get('De_los_cuales_AZUCARES_g', ''),
            Proteinas_g = row.get('Proteinas_g', ''),
            Sal_g = row.get('Sal_g', ''),
            Rec_Enterobacterias = row.get('Rec. Enterobacterias', ''),
            Rec_Aerobios_totales = row.get('Rec. Aerobios totales', ''),
            Rec_Escherichia_Coli = row.get('Rec. Escherichia Coli', ''),
            Rec_Staphylococcus_Aureus = row.get('Rec. Staphylococcus Aureus', ''),
            Det_Salmonella_cpp = row.get('Det_Salmonella cpp', ''),
            Rec_Listeria_Monocytogenes = row.get('Rec. ListeriaMonocytogenes', ''),
            Rec_Mohos_y_levaduras = row.get('Rec. Mohos y levaduras', ''),
            Población_diana = row.get('Población diana', ''),
            uso_esperado = row.get('uso_esperado', ''),
            Condiciones_conservación = row.get('Condiciones_conservación', ''),
            vida_en_lugar_fresco_y_seco = row.get('vida_en_lugar_fresco_y_seco', ''),
            vida_en_refrigeración = row.get('vida_en_refrigeración', ''),
            vida_en_congelación = row.get('vida_en_congelación', '')
        )
        fichas_html += ficha
    return fichas_html


#----------------------------------------------------------------------------------------
# Generar el HTML completo
#----------------------------------------------------------------------------------------
def generar_html(param: InfoTransaccion) -> list:
    resultado = [f"HTML generado en {RUTA_HTML}"]
    param.debug = "generar_html"

    try:
        df = leer_excel()
        indice = generar_indice(df, ordenar_por='Nombre')
        fichas = generar_fichas(df)

        # Cargamos la platilla en una variable
        with open(RUTA_PLANTILLA, "r", encoding="utf-8") as archivo:
            html = archivo.read()
        # sustituimos las variables de la plantilla por los valores
        html = html.replace("{RUTA_LOGO}", RUTA_LOGO)
        html = html.replace("{indice}", indice)
        html = html.replace("{fichas}", fichas)
        html = html.replace("{fecha}", datetime.now().strftime('%d/%m/%Y'))

        # Grabamos el HTML en un archivo 
        with open(RUTA_HTML, "w", encoding="utf-8") as f:
            f.write(html)

        return resultado

    except MadreException as e:
        raise
                    
    except HTTPException as e:
        param.error_sistema()
        graba_log(param, "generar_html.HTTPException", e)
        raise

    except Exception as e:
        param.error_sistema()
        graba_log(param, "generar_html.Exception", e)
        raise HTTPException(status_code=e.status_code, detail=e.detail)
