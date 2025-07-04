import os
from datetime import datetime

from app.utils.utilidades import graba_log, imprime
from app.config.db_mallorquina import get_db_connection_mysql, close_connection_mysql
from app.utils.InfoTransaccion import InfoTransaccion
from app.config.settings import settings

# Rutas de los archivos
LOGO =        os.path.join(settings.WEB_RUTA_LOCAL, settings.WEB_RUTA_IMAGEN, "Logotipo con tagline - negro.svg")
RUTA_ICONOS = os.path.join(settings.WEB_RUTA_LOCAL, settings.WEB_RUTA_IMAGEN, "alergenos/")

PLANTILLA       = os.path.join(settings.RUTA_ALERGENOS, "plantilla.html")
FICH_NO_IMPRIMIBLES = os.path.join(settings.RUTA_ALERGENOS_HTML, "no_imprimibles.csv")

#----------------------------------------------------------------------------------------
# Principal del Proceso de generación de html
#----------------------------------------------------------------------------------------
def proceso(param: InfoTransaccion) -> list:
    resultado = []
    param.debug = "proceso"
    punto_venta = param.parametros[1]

    try:
        # Conectar a la base de datos
        conn_mysql = get_db_connection_mysql()
        cursor_mysql = conn_mysql.cursor(dictionary=True)

        param.debug = f"Punto de venta: {punto_venta}"
        # imprime([punto_venta], "*  punto_venta")

        # Consultar los datos principales  CUANDO CARGEMOS LOS PRECIOS BIEN, HAY QUE CAMBIAR el WHERE para solo coger productos que se vendan en "punto_venta"
        cursor_mysql.execute("""SELECT distinct a.* 
                                  FROM erp_productos a
                                 where (alta_tpv = 'Sí'
                                    or alta_glovo = 'Sí'
                                    or alta_web = 'Sí' 
                                    or alta_catering = 'Sí')
                                   and listado_alergenos = 'Sí'
                                   and codigo_alergenos = a.id
                                 ORDER BY familia_desc, nombre""")
        productos = cursor_mysql.fetchall()

        # imprime([productos, len(productos)], "*", 2)

        close_connection_mysql(conn_mysql, cursor_mysql)

        param.debug = "Generar HTML"
        # Generación del HTML
        html = generar_html(param, productos, punto_venta)

        resultado = [f"Listado generado correctamente", html]
        return resultado
    

    except Exception as e:
        param.error_sistema(e=e, debug="proceso.Exception")
        raise 

    finally:
        param.debug = "cierra conn"
        close_connection_mysql(conn_mysql, cursor_mysql)


#----------------------------------------------------------------------------------------
# Generar el HTML completo
#----------------------------------------------------------------------------------------
def generar_html(param: InfoTransaccion, productos: list, punto_venta: int) -> str: 
    param.debug = "generar_html"
    html_final = ""

    try:
        # Cargar la plantilla
        plantilla = cargar_plantilla(param, PLANTILLA)
        plantilla_html = reemplazar_fijos(param, plantilla, punto_venta)

        # Secciones dinámicas
        indice_alergenos = indice(param, productos, punto_venta)

        # Reemplazar las secciones dinámicas en la plantilla
        html_final = reemplazar_campos(plantilla_html, {
            'indice_alergenos': indice_alergenos,
            # 'fichas': fichas_content
        })

        # imprime([html_final[2001:8000]], "*")

        return html_final
    
    except Exception as e:
        param.error_sistema(e=e, debug="generar_html.Exception")
        raise 


#----------------------------------------------------------------------------------------
# Leer la plantilla HTML
#----------------------------------------------------------------------------------------
def cargar_plantilla(param, ruta):
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            return f.read()

   
    except Exception as e:
        param.error_sistema(e=e, debug="cargar_plantilla.Exception")
        raise 


#----------------------------------------------------------------------------------------
# Reemplazar Fijos
#----------------------------------------------------------------------------------------
def reemplazar_fijos(param, plantilla, punto_venta):
    html = plantilla

    try:
        punto_venta_desc = "La Mallorquina"

        ruta = os.path.join(RUTA_ICONOS, "")
        html = html.replace("{LOGO}", LOGO)

        html = html.replace("{titulo_principal}", f"Alérgenos Alimentarios {punto_venta_desc}")

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

        # porque usamos la misma plantilla para las fichas de los productos
        html = html.replace("{fichas}", "")
        

        return html
    
    except Exception as e:
        param.error_sistema(e=e, debug="reemplazar_fijos.Exception")
        raise 



#----------------------------------------------------------------------------------------
# Reemplazar INDICE
#----------------------------------------------------------------------------------------
def indice(param, productos, punto_venta):
    indice_alergenos = ""
    try:
        # Generar las filas de la tabla principal
        familia_actual = None
        for producto in productos:
            if listable(param, producto, punto_venta): 
                if producto['familia_desc'] != familia_actual:
                    indice_alergenos += f"<tr id='familia'><td colspan='15'><p class='lista-familia'>{producto['familia_desc']}</p></td></tr>\n"
                    familia_actual = producto['familia_desc']

                indice_alergenos += f"<tr id='producto'>"
                # indice_alergenos += f"<td><p class='lista-producto'><a href='fichas/{producto['ID']}.html' target='_blank' rel='noopener noreferrer'>{producto['nombre']}</a></p></td>"
                indice_alergenos += f"<td><p class='lista-producto'>{producto['nombre']}</p></td>"

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
        param.error_sistema(e=e, debug="indice.Exception")
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
# Comprueba que tenemos descripción de la composición del productos, porque si no tiene, 
# no se puede imprimir
#----------------------------------------------------------------------------------------
def listable(param: InfoTransaccion, fila, punto_venta):
    try:


        return True
    
   
    except Exception as e:
        param.error_sistema(e=e, debug="listable.Exception")
        raise 