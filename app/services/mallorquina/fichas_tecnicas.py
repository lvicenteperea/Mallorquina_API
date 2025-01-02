import pandas as pd
from datetime import datetime
from fastapi import HTTPException

import os

from app.utils.functions import graba_log, imprime
from app.utils.mis_excepciones import MadreException
from app.utils.InfoTransaccion import InfoTransaccion
from app.config.settings import settings

# RUTA_BASE: str = "app/ficheros/"
# RUTA_IMAGEN: str = "app/ficheros/imagen/"
# RUTA_DATOS: str = "app/ficheros/datos/"

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
# Función para procesar el Excel y generar el HTML
def generar_html(param: InfoTransaccion) -> list:
    resultado = []
    param.debug = "proceso"

    try:
        # Rutas de los archivos
        RUTA_BASE = f"{settings.RUTA_DATOS}ficheros"
        RUTA_ICONOS = os.path.join(settings.RUTA_IMAGEN, "alergenos")
        RUTA_LOGO = os.path.join(settings.RUTA_IMAGEN, "Logotipo con tagline - negro.svg")
        RUTA_EXCEL = os.path.join(settings.RUTA_DATOS, "alergenos/fichas_tecnicas.xlsx")
        RUTA_HTML = os.path.join(settings.RUTA_DATOS, "alergenos/fichas_tecnicas.html")

        # Leer el Excel
        df = pd.read_excel(RUTA_EXCEL, sheet_name=0)

        # Filtrar filas donde la columna "TPV" (AR) tenga el valor "Si"
        df_filtrado = df[df['TPV'] == 'Si']

        # Iniciar HTML
        html = """<!DOCTYPE html>
    <html lang=\"es\">
    <head>
        <meta charset=\"UTF-8\">
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
        <title>Ficha Técnica</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                flex-direction: column;
            }
            header {
                position: fixed;
                top: 0;
                width: 100%;
                background-color: #fff;
                border-bottom: 1px solid #ccc;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 10px;
                z-index: 1000;
            }
            header img {
                max-height: 50px;
                margin-right: 10px;
            }
            footer {
                position: fixed;
                bottom: 0;
                width: 100%;
                background-color: #fff;
                border-top: 1px solid #ccc;
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px;
                z-index: 1000;
            }
            footer .date {
                font-size: 0.9em;
            }
            footer .back-link {
                font-size: 0.9em;
                color: #007BFF;
                text-decoration: none;
            }
            main {
                margin: 80px 20px 60px 20px;
            }
            .index {
                margin-bottom: 20px;
            }
            .index-item {
                display: flex;
                justify-content: space-between;
                margin-bottom: 10px;
            }
            .allergens img {
                height: 20px;
                margin-right: 5px;
            }
            .technical-sheet {
                margin-bottom: 40px;
            }
        </style>
    </head>
    <body>
        <header>
            <img src=\"{logo}\" alt=\"Logotipo\">
            <h1>Ficha Técnica de Productos</h1>
        </header>

        <main>
            <section class=\"index\">
                <h2>Índice</h2>
                <ul>
        """.format(logo=RUTA_LOGO)

        # Generar el índice
        for _, row in df_filtrado.iterrows():
            codigo = row['A']
            nombre = row['B']
            alergenos = ''.join(
                f'<img src="{os.path.join(RUTA_ICONOS, col[0] + ".webp")}" alt="{col}">'
                for col in df.columns[3:17] if row[col] in ['Sí', 'Traza']
            )
            html += f"<li class=\"index-item\"><a href=\"#{codigo}\">{codigo} - {nombre}</a>{alergenos}</li>\n"

        html += """</ul>
            </section>

            <section class=\"technical-sheets\">
                <h2>Fichas Técnicas</h2>
        """

        # Generar las fichas técnicas
        for _, row in df_filtrado.iterrows():
            html += f"""
            <article id=\"{row['A']}\" class=\"technical-sheet\">
                <h3>{row['B']}</h3>
                <p>Composición: {row.get('Composición del producto', '')}</p>
                <p>Condiciones de conservación: {row.get('Condiciones conservación', '')}</p>
                <!-- Agregar más datos según las columnas -->
            </article>
            """

        # Finalizar HTML
        html += """</section>
        </main>

        <footer>
            <span class=\"date\">Generado el: {fecha}</span>
            <a href=\"#\" class=\"back-link\">Volver a inicio</a>
        </footer>
    </body>
    </html>""".format(fecha=datetime.now().strftime('%d/%m/%Y'))

        # Guardar el archivo HTML
        os.makedirs(os.path.dirname(RUTA_HTML), exist_ok=True)
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
