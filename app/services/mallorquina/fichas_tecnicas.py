import os
import pandas as pd
from datetime import datetime
from fastapi import HTTPException

from app.utils.functions import graba_log, imprime
from app.config.db_mallorquina import get_db_connection_mysql, close_connection_mysql, get_db_connection_sqlserver, close_connection_sqlserver
from app.utils.mis_excepciones import MadreException
from app.utils.InfoTransaccion import InfoTransaccion
from app.config.settings import settings

# Rutas de los archivos
RUTA_ICONOS = os.path.join("D:/Nube/GitHub/Mallorquina_API/", settings.RUTA_IMAGEN, "alergenos/")
LOGO = os.path.join("D:/Nube/GitHub/Mallorquina_API/", settings.RUTA_IMAGEN, "Logotipo con tagline - negro.svg")
PLANTILLA = os.path.join(settings.RUTA_DATOS, "alergenos/plantilla_completa.html")
RUTA_HTML = os.path.join(settings.RUTA_DATOS, "alergenos/")
FICH_NO_IMPRIMIBLES = os.path.join(settings.RUTA_DATOS, "alergenos/no_imprimibles.csv")



#----------------------------------------------------------------------------------------
# Comprueba que tenemos descripción de la composición del productos, porque si no tiene, 
# no se puede imprimir
#----------------------------------------------------------------------------------------
def imprimible(fila):
    composicion = '' if pd.isna(fila.get('Composición completa', '')) else fila.get('Composición completa', '')
    if not composicion: 
        composicion = '' if pd.isna(fila.get('Composición del producto', '')) else fila.get('Composición del producto', '')
        
    if not composicion:
        with open(FICH_NO_IMPRIMIBLES, "a") as f:
            f.write(f"{fila['Código']};{fila['Nombre']}" + "\n")  # Escribir el registro con salto de línea

    return composicion

#----------------------------------------------------------------------------------------
# Leer la plantilla HTML
#----------------------------------------------------------------------------------------
def cargar_plantilla(ruta):
    with open(ruta, 'r', encoding='utf-8') as f:
        return f.read()


#----------------------------------------------------------------------------------------
# Reemplazar placeholders en la plantilla
#----------------------------------------------------------------------------------------
def reemplazar_campos(plantilla, campos):
    for placeholder, valor in campos.items():
        #imprime([placeholder, "{"+f"{placeholder}"+"}", valor, valor or f"{placeholder}"],'=')
        plantilla = plantilla.replace("{"+f"{placeholder}"+"}", f"{valor}" or f"{placeholder}")

    return plantilla

#----------------------------------------------------------------------------------------
# Generar el HTML completo
#----------------------------------------------------------------------------------------
def generar_html(param: InfoTransaccion) -> list:
    resultado = []
    param.debug = "generar_html"
    funcion = "fichas_tecnicas.generar_html"

    try:
        param.debug = "rutas"
        if not param.parametros[0]:
            salida = os.path.join(RUTA_HTML, f"fichas_tecnicas-{datetime.now().strftime('%Y-%m-%d')}.html")
        else:
            salida = os.path.join(RUTA_HTML, param.parametros[0]) # Nombre del archivo HTML viene en el segundo parámetro

        param.debug = f"{salida}"
        # Conectar a la base de datos
        conn_mysql = get_db_connection_mysql()
        cursor_mysql = conn_mysql.cursor(dictionary=True)

        # Consultar los datos principales
        cursor_mysql.execute("SELECT * FROM erp_productos WHERE alta_tpv = 'Sí' ORDER BY familia_desc, nombre")
        productos = cursor_mysql.fetchall()
        print('=========', len(productos))

        # Consultar los precios
        cursor_mysql.execute("SELECT * FROM erp_productos_pvp")
        precios = cursor_mysql.fetchall()

        # Crear un diccionario de precios por ID
        precios_dict = {}
        for precio in precios:
            id_producto = precio['id_producto']
            if id_producto not in precios_dict:
                precios_dict[id_producto] = []
            precios_dict[id_producto].append(precio)

        # Cargar la plantilla
        plantilla = cargar_plantilla(PLANTILLA)

        # Secciones dinámicas
        main_content = ""
        fichas_content = ""
        precios_content = ""

        # Generar las filas de la tabla principal
        familia_actual = None
        x = 0
        for producto in productos:
            x += 1
            print('-------', x, producto)
            if producto['familia_desc'] != familia_actual:
                main_content += f"<tr id='familia'><td colspan='15'><p class='lista-familia'>{producto['familia_desc']}</p></td></tr>\n"
                familia_actual = producto['familia_desc']

            main_content += f"<tr id='producto'>"
            main_content += f"<td><a href='#{producto['ID']}' class='lista-producto'>{producto['nombre']}</a></td>"
            for alergeno in ['Huevo', 'Lacteos', 'Crustaceos', 'Cáscara', 'Gluten', 'Pescado', 'Altramuz', 'Mostaza', 'Cacahuetes', 'Apio', 'Sulfitos', 'Soja', 'Moluscos', 'Sésamo']:
                valor = producto.get(alergeno, "")
                if valor == "Sí":
                    main_content += f"<td><p class='lista-X'>X</p></td>"
                elif valor == "Trazas":
                    main_content += f"<td><p class='lista-T'>T</p></td>"
                else:
                    main_content += "<td></td>"
            main_content += "</tr>\n"

        # Generar las fichas técnicas
        for producto in productos:
            ficha_campos = {
                'codigo': producto['ID'],
                'nombre': producto['nombre'],
                'categoria': producto.get('categoria', ''),
                'temporada': producto.get('temporada', ''),
                'fecha': datetime.now().strftime("%d/%m/%Y"),
                'composicion_completa': producto.get('composicion_completa', ''),
                'LOGO': LOGO,
            }
            fichas_content += reemplazar_campos(plantilla, ficha_campos)

        # Generar la sección de precios
        for producto in productos:
            id_producto = producto['ID']
            if id_producto in precios_dict:
                precios_content += f"<h3>Precios para {producto['nombre']}</h3><ul>"
                for precio in precios_dict[id_producto]:
                    precios_content += f"<li>{precio['tipo']}: {precio['pvp']}</li>"
                precios_content += "</ul>"

        # Reemplazar las secciones dinámicas en la plantilla
        html_final = reemplazar_campos(plantilla, {
            'main': main_content,
            'fichas': fichas_content,
            'precios': precios_content,
        })

        # Guardar el archivo HTML
        with open(salida, 'w', encoding='utf-8') as f:
            f.write(html_final)

        print(f"HTML generado correctamente: {salida}")

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

    finally:
        param.debug = "cierra conn"
        close_connection_mysql(conn_mysql, cursor_mysql)

