import os
import pandas as pd
from datetime import datetime

from app.utils.functions import graba_log, imprime
from app.config.db_mallorquina import get_db_connection_mysql, close_connection_mysql, get_db_connection_sqlserver, close_connection_sqlserver
from app.utils.InfoTransaccion import InfoTransaccion
from app.config.settings import settings

# Rutas de los archivos
RUTA_ICONOS = os.path.join("D:/Nube/GitHub/Mallorquina_API/", settings.RUTA_IMAGEN, "alergenos/")
LOGO = os.path.join("D:/Nube/GitHub/Mallorquina_API/", settings.RUTA_IMAGEN, "Logotipo con tagline - negro.svg")
PLANTILLA = os.path.join(settings.RUTA_DATOS, "alergenos/plantilla.html")
PLANTILLA_FICHA = os.path.join(settings.RUTA_DATOS, "alergenos/plantilla_producto.html")
RUTA_HTML = os.path.join(settings.RUTA_DATOS, "alergenos/")
FICH_NO_IMPRIMIBLES = os.path.join(settings.RUTA_DATOS, "alergenos/no_imprimibles.csv")



#----------------------------------------------------------------------------------------
# Comprueba que tenemos descripción de la composición del productos, porque si no tiene, 
# no se puede imprimir
#----------------------------------------------------------------------------------------
def imprimible(param, fila):
    try:
        composicion = fila.get("composicion_completa", "").strip() or ""
        if not composicion: 
            composicion = fila.get("composicion_etiqueta", "").strip() or ""
            
        if not composicion:
            with open(FICH_NO_IMPRIMIBLES, "a") as f:
                f.write(f"{fila.get('codigo')};{fila.get('nombre')}" + "\n")  # Escribir el registro con salto de línea

        return composicion
   
    except Exception as e:
        param.error_sistema()
        graba_log(param, "cargar_plantilla.Exception", e)
        raise 

#----------------------------------------------------------------------------------------
# Leer la plantilla HTML
#----------------------------------------------------------------------------------------
def cargar_plantilla(param, ruta):
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            return f.read()

   
    except Exception as e:
        param.error_sistema()
        graba_log(param, "cargar_plantilla.Exception", e)
        raise 

#----------------------------------------------------------------------------------------
# Reemplazar placeholders en la plantilla
#----------------------------------------------------------------------------------------
def reemplazar_campos(plantilla, campos):
    for placeholder, valor in campos.items():
        #imprime([placeholder, "{"+f"{placeholder}"+"}", valor, valor or f"{placeholder}"],'=')
        plantilla = plantilla.replace("{"+f"{placeholder}"+"}", f"{valor}" or f"{placeholder}")

    return plantilla


#----------------------------------------------------------------------------------------
# Reemplazar Fijos
#----------------------------------------------------------------------------------------
def reemplazar_fijos(param, plantilla):
    html = plantilla
    try:
        ruta = os.path.join(RUTA_ICONOS, "")
        html = html.replace("{LOGO}", LOGO)
        html = html.replace("{Huevo}", f"{ruta}Huevo.ico")
        html = html.replace("{Leche}", f"{ruta}Leche.ico")
        html = html.replace("{Crustaceos}", f"{ruta}Crustaceos.ico")
        html = html.replace("{Cascara}", f"{ruta}Cáscara.ico")
        html = html.replace("{Gluten}", f"{ruta}Gluten.ico")
        html = html.replace("{Pescado}", f"{ruta}Pescado.ico")
        html = html.replace("{Altramuz}", f"{ruta}Altramuz.ico")
        html = html.replace("{Mostaza}", f"{ruta}Mostaza.ico")
        html = html.replace("{Cacahuetes}", f"{ruta}Cacahuetes.ico")
        html = html.replace("{Apio}", f"{ruta}Apio.ico")
        html = html.replace("{Sulfitos}", f"{ruta}Sulfitos.ico")
        html = html.replace("{Soja}", f"{ruta}Soja.ico")
        html = html.replace("{Moluscos}", f"{ruta}Moluscos.ico")
        html = html.replace("{Sesamo}", f"{ruta}Sésamo.ico")
        html = html.replace("{fecha}", datetime.now().strftime('%d/%m/%Y'))

        return html
    
    except Exception as e:
        param.error_sistema()
        graba_log(param, "reemplazar_fijos.Exception", e)
        raise 

#----------------------------------------------------------------------------------------
# Reemplazar INDICE
#----------------------------------------------------------------------------------------
def indice(param, productos):
    indice_alergenos = ""
    try:
        # Generar las filas de la tabla principal
        familia_actual = None
        for producto in productos:
            if producto['familia_desc'] != familia_actual:
                indice_alergenos += f"<tr id='familia'><td colspan='15'><p class='lista-familia'>{producto['familia_desc']}</p></td></tr>\n"
                familia_actual = producto['familia_desc']

            indice_alergenos += f"<tr id='producto'>"
            indice_alergenos += f"<td><p class='lista-producto'><a href='#{producto['ID']}'>{producto['nombre']}</a></p></td>"
            for alergeno in ['huevo', 'leche', 'crustaceos', 'cascara', 'gluten', 'pescado', 'altramuz', 'mostaza', 'cacahuetes', 'apio', 'sulfitos', 'soja', 'moluscos', 'sesamo']:
                valor = producto.get(alergeno, "")
                if valor == "Sí":
                    indice_alergenos += f"<td><p class='lista-X'>X</p></td>"
                elif valor == "Trazas":
                    indice_alergenos += f"<td><p class='lista-T'>T</p></td>"
                else:
                    indice_alergenos += f"<td><p class='lista-X'>&nbsp;</p></td>"
            indice_alergenos += "</tr>\n"

        return indice_alergenos
    
    except Exception as e:
        param.error_sistema()
        graba_log(param, "indice.Exception", e)
        raise 

#----------------------------------------------------------------------------------------
# Reemplazar FICHAS
#----------------------------------------------------------------------------------------
def fichas(param: InfoTransaccion, productos: list, precios: dict):
    fichas_html = cargar_plantilla(param, PLANTILLA_FICHA)
    fichas_content = ""
    precios_content = ""

    try:
        # Generar las fichas técnicas
        for producto in productos:
            composicion = imprimible(param, producto)
            if composicion: 
                id_producto = producto['ID']
                """
                imprime([producto, type(producto)], "=")

                {'familia_cod': None, 
                'familia_desc': '4- BOMBONERIA/6. Productos Venta Directa', 
                'grupo_de_carta': '', 
                'alta_tpv': 'Sí', 
                'alta_glovo': '', 
                'alta_web': '', 
                'alta_catering': '', 
                'peso_neto_aprox': '', 
                'fibra_dietetica_g': '', 
                'otros': '', 
                'fec_modificacion': '', 
                'created_at': datetime.datetime(2025, 1, 5, 19, 15, 18), 
                'updated_at': None, 
                'modified_by': None}
                """

                ficha_campos = {
                    'codigo': id_producto,
                    'nombre': producto.get("nombre", "").strip() or " ",
                    'categoria': producto.get("categoria", "").strip() or " ",
                    'temporada': producto.get("temporada", "").strip() or " ",
                    'fecha': datetime.now().strftime("%d/%m/%Y"),
                    'composicion_completa': composicion,
                    'LOGO': LOGO,
                    'Gluten': "X" if producto.get('gluten', '') == "Sí" else "Traza" if producto.get('gluten', '') == "Traza" else " ",
                    'Cascara': "X" if producto.get('cascara', '') == "Sí" else "Traza" if producto.get('cascara', '') == "Traza" else " ",
                    'Crustaceos': "X" if producto.get('crustaceos', '') == "Sí" else "Traza" if producto.get('crustaceos', '') == "Traza" else " ",
                    'Apio': "X" if producto.get('apio', '') == "Sí" else "Traza" if producto.get('apio', '') == "Traza" else " ",
                    'Huevo': "X" if producto.get('huevo', '') == "Sí" else "Traza" if producto.get('huevo', '') == "Traza" else " ",
                    'Mostaza': "X" if producto.get('mostaza', '') == "Sí" else "Traza" if producto.get('mostaza', '') == "Traza" else " ",
                    'Pescado': "X" if producto.get('pescado', '') == "Sí" else "Traza" if producto.get('pescado', '') == "Traza" else " ",
                    'Sesamo': "X" if producto.get('sesamo', '') == "Sí" else "Traza" if producto.get('sesamo', '') == "Traza" else " ",
                    'Cacahuetes': "X" if producto.get('cacahuetes', '') == "Sí" else "Traza" if producto.get('cacahuetes', '') == "Traza" else " ",
                    'Sulfitos': "X" if producto.get('sulfitos', '') == "Sí" else "Traza" if producto.get('sulfitos', '') == "Traza" else " ",
                    'Soja': "X" if producto.get('soja', '') == "Sí" else "Traza" if producto.get('soja', '') == "Traza" else " ",
                    'Altramuz': "X" if producto.get('altramuz', '') == "Sí" else "Traza" if producto.get('altramuz', '') == "Traza" else " ",
                    'Leche': "X" if producto.get('leche', '') == "Sí" else "Traza" if producto.get('leche', '') == "Traza" else " ",
                    'Moluscos': "X" if producto.get('moluscos', '') == "Sí" else "Traza" if producto.get('moluscos', '') == "Traza" else " ",

                    'Valor_energetico_Kcal_Kj': producto.get("valor_energetico_kcal_kj", "").strip() or " ",
                    'Grasas_g': producto.get("grasas_g", "").strip() or " ",
                    'De_las_cuales_SATURADAS_g': producto.get("de_las_cuales_saturadas_g", "").strip() or " ",
                    'Hidratos_de_carbono_g': producto.get("hidratos_de_carbono_g", "").strip() or " ",
                    'De_los_cuales_AZUCARES_g': producto.get("de_los_cuales_azucares_g", "").strip() or " ",
                    'Proteinas_g': producto.get("proteinas_g", "").strip() or " ",
                    'Sal_g': producto.get("sal_g", "").strip() or " ",

                    'Rec_Enterobacterias': producto.get("rec_enterobacterias", "").strip() or " ",
                    'Rec_Aerobios_totales': producto.get("rec_aerobios_totales", "").strip() or " ",
                    'Rec_Escherichia_Coli': producto.get("rec_escherichia_coli", "").strip() or " ",
                    'Rec_Staphylococcus_Aureus': producto.get("rec_staphylococcus_aureus", "").strip() or " ",
                    'Det_Salmonella_cpp': producto.get("det_salmonella_cpp", "").strip() or " ",
                    'Rec_Listeria_Monocytogenes': producto.get("rec_listeria_monocytogenes", "").strip() or " ",
                    'Rec_Mohos_y_levaduras': producto.get("rec_mohos_y_levaduras", "").strip() or " ",

                    'Población_diana': producto.get("poblacion_diana", "").strip() or " ",
                    'uso_esperado': producto.get("uso_esperado", "").strip() or " ",
                    'Condiciones_conservación': producto.get("Condiciones_conservación", "").strip() or " ",

                    'vida_en_lugar_fresco_y_seco': producto.get("condiciones_conservacion", "").strip() or " ",
                    'vida_en_refrigeracion': producto.get("condiciones_almacenamiento", "").strip() or " ",
                    'vida_en_congelacion': producto.get("vida_fri_desde_fabric", "").strip() or " ",
                }
                fichas_content += reemplazar_campos(fichas_html, ficha_campos)
                """
                # Generar la sección de precios
                if id_producto in precios:
                    precios_content += f"<h3>Precios para {producto['nombre']}</h3><ul>"
                    for precio in precios[id_producto]:
                        precios_content += f"<li>{precio['tipo']}: {precio['pvp']}</li>"
                    precios_content += "</ul>"
                fichas_content = reemplazar_campos(fichas_content, {'precios': precios_content})
                """
        return fichas_content
    
    except Exception as e:
        param.error_sistema()
        graba_log(param, "fichas.Exception", e)
        raise 


#----------------------------------------------------------------------------------------
# Generar el HTML completo
#----------------------------------------------------------------------------------------
def generar_html(param: InfoTransaccion, productos: list, precios: dict) -> str: 
    param.debug = "generar_html"
    html_final = ""

    try:
        # Cargar la plantilla
        plantilla = cargar_plantilla(param, PLANTILLA)
        plantilla_html = reemplazar_fijos(param, plantilla)

        # Secciones dinámicas
        indice_alergenos = indice(param, productos)
        fichas_content = fichas(param, productos, precios)

        # Reemplazar las secciones dinámicas en la plantilla
        html_final = reemplazar_campos(plantilla_html, {
            'indice_alergenos': indice_alergenos,
            'fichas': fichas_content
        })


        return html_final
    
    except Exception as e:
        param.error_sistema()
        graba_log(param, "generar_html.Exception", e)
        raise 


#----------------------------------------------------------------------------------------
# Principal del Proceso de generación de html
#----------------------------------------------------------------------------------------
def proceso(param: InfoTransaccion) -> list:
    resultado = []
    param.debug = "proceso"

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

        close_connection_mysql(conn_mysql, cursor_mysql)

        # Generación del HTML
        html = generar_html(param, productos, precios_dict)

        # Guardar el archivo HTML
        with open(salida, 'w', encoding='utf-8') as f:
            f.write(html)

        resultado = [f"HTML generado correctamente: {salida}"] if html else ["No se ha generado fichero"]
        return resultado
    

    except Exception as e:
        param.error_sistema()
        graba_log(param, "proceso.Exception", e)
        raise 

    finally:
        param.debug = "cierra conn"
        close_connection_mysql(conn_mysql, cursor_mysql)
