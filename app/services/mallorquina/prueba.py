import pandas as pd
import os
from datetime import datetime

# Ruta local de los archivos
RUTA_ICONOS = os.path.join("app/ficheros/imagen/", "alergenos/")
RUTA_LOGO = os.path.join("app/ficheros/imagen/", "Logotipo con tagline - negro.svg")
RUTA_EXCEL = os.path.join("app/ficheros/datos/alergenos/", "fichas_tecnicas.xlsx")
RUTA_HTML = os.path.join("app/ficheros/datos/alergenos/", "fichas_tecnicas.html")

# Leer el archivo Excel
try:
    df = pd.read_excel(RUTA_EXCEL, sheet_name=0)
    print(f"Datos cargados correctamente, {len(df)} filas encontradas.")
except Exception as e:
    print(f"Error al leer el archivo Excel: {e}")
    exit()

# Filtrar filas donde la columna 'TPV' tenga el valor 'Si'
if 'TPV' in df.columns:
    df_filtrado = df[df['TPV'] == 'Sí']
    print(f"{len(df_filtrado)} filas después del filtro 'TPV = Sí'.")
else:
    print("No se encontró la columna 'TPV' en el Excel.")
    exit()

# Iniciar HTML
html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ficha Técnica</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
        }}
        header {{
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
        }}
        header img {{
            max-height: 50px;
            margin-right: 10px;
        }}
        footer {{
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
        }}
        main {{
            margin: 80px 20px 60px 20px;
        }}
        .index-item {{
            margin-bottom: 10px;
        }}
        .allergens img {{
            height: 20px;
            margin-right: 5px;
        }}
        .technical-sheet {{
            margin-bottom: 40px;
        }}
    </style>
</head>
<body>
    <header>
        <img src="{RUTA_LOGO}" alt="Logotipo">
        <h1>Ficha Técnica de Productos</h1>
    </header>
    <main>
        <section class="index">
            <h2>Índice</h2>
            <ul>
"""

# Generar índice
for _, row in df_filtrado.iterrows():
    codigo = row['Código']
    nombre = row['Nombre']
    alergenos = ''.join(
        f'<img src="{os.path.join(RUTA_ICONOS, col[0] + ".webp")}" alt="{col}">'
        for col in df.columns[3:17] if row[col] in ['Sí', 'Traza']
    )
    html += f"<li class=\"index-item\"><a href=\"#{codigo}\">{codigo} - {nombre}</a> {alergenos}</li>\n"

html += "</ul></section><section class=\"technical-sheets\">"

# Generar fichas técnicas
for _, row in df_filtrado.iterrows():
    html += f"""
    <article id="{row['Código']}" class="technical-sheet">
        <h3>{row['Nombre']}</h3>
        <p>Composición: {row.get('Composición del producto', '')}</p>
        <p>Condiciones de conservación: {row.get('Condiciones conservación', '')}</p>
    </article>
    """

# Finalizar HTML
html += f"""
        </section>
    </main>
    <footer>
        <span class="date">Generado el: {datetime.now().strftime('%d/%m/%Y')}</span>
        <a href="#" class="back-link">Volver a inicio</a>
    </footer>
</body>
</html>
"""

# Guardar el archivo HTML
try:
    with open(RUTA_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML generado correctamente en {RUTA_HTML}")
except Exception as e:
    print(f"Error al guardar el archivo HTML: {e}")
