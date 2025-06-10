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
        # if punto_venta == 0:
        cursor_mysql.execute("""SELECT distinct ID
                                      ,IF(TRIM(nombre_alergenos) = '' OR nombre_alergenos IS NULL, nombre, nombre_alergenos) AS nombre
                                      ,huevo, leche, crustaceos, cascara, gluten, pescado, altramuz, mostaza, cacahuetes, apio, sulfitos, soja, moluscos, sesamo
                                  FROM erp_productos
                                 where listado_alergenos in ('Sí', "Si")
                                   and ifnull(codigo_alergenos, id) = id
                                 ORDER BY nombre""")
        productos = cursor_mysql.fetchall()

        # Calcula la fecha del la última modificación que es el registro con la fecha mas alta, independientemente de que salga en el listado o no
        cursor_mysql.execute("SELECT ifnull(max(fec_modificacion), now())  as fec_max_modificacion FROM erp_productos")
        fec_max_mod_str = cursor_mysql.fetchone()

        if fec_max_mod_str["fec_max_modificacion"]:
            # imprime([fec_max_mod_str], "*     VAMOS A VER LA FECHA    ", 2)
            fec_max_mod = datetime.strptime(fec_max_mod_str["fec_max_modificacion"], "%Y-%m-%d %H:%M:%S")
        else:
            fec_max_mod = datetime.now().strftime('%d/%m/%Y')


        param.debug = "Generar HTML"
        # Generación del HTML
        html = generar_html(param, cursor_mysql, productos, punto_venta)

        close_connection_mysql(conn_mysql, cursor_mysql)

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
def generar_html(param: InfoTransaccion, cursor_mysql, productos: list, punto_venta: int) -> str: 
    param.debug = "generar_html"
    html_final = ""

    try:
        # Cargar la plantilla
        plantilla = cargar_plantilla(param, PLANTILLA)
        plantilla_html = reemplazar_fijos(param, plantilla, punto_venta)

        # Secciones dinámicas
        indice_alergenos = indice(param, cursor_mysql, productos, punto_venta)

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
        if punto_venta == 4:
            punto_venta_desc = "Tiendas" # "(Sol - Quevedo)"
        elif punto_venta == 1:
            punto_venta_desc = "Tiendas." # "(Velázquez - MG)"
        elif punto_venta == 7:
            punto_venta_desc = "Tienda" # "(Salón SOL)"
        elif punto_venta == 90:  
            punto_venta_desc = "(Catering)"
        elif punto_venta == 91:  
            punto_venta_desc = "(Web)"
        elif punto_venta == 92:  
            punto_venta_desc = "(Glovo)"
        else:
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
def indice(param, cursor_mysql, productos, punto_venta):
    indice_alergenos = ""
    registros = 0

    try:
        # Generar las filas de la tabla principal
        # familia_actual = None
        for producto in productos:
            if listable(param, cursor_mysql, producto, punto_venta, producto['ID']): 
                registros += 1
                # if producto['familia_desc'] != familia_actual:
                #     indice_alergenos += f"<tr id='familia'><td colspan='15'><p class='lista-familia'>{producto['familia_desc']}</p></td></tr>\n"
                #     familia_actual = producto['familia_desc']

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

        indice_alergenos =  f"<tr> <td><p></p></td> <td><p>{registros}</p> </td><td><p></p></td> </tr> {indice_alergenos}"

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
def existe_alguno_en_alta(param: InfoTransaccion, cursor_mysql, id_producto, tipo_alta):
    query_inicial = "select count(*) as valor from erp_productos a where codigo_alergenos = %s and {TIPO_ALTA}"
    try:
        query_final = query_inicial.replace("{TIPO_ALTA}", tipo_alta)
        cursor_mysql.execute(query_final, (id_producto, ))
        existe = cursor_mysql.fetchone()
        # imprime([query_final, id_producto, len(existe), existe], "*  --  query_final  --  ")
        if existe['valor'] and existe['valor'] > 0:
            return True
        else:
            return False
       
    except Exception as e:
        param.error_sistema(e=e, debug="existe_alguno_en_alta.Exception")
        raise 


# --------------------------------------------------------------------------------------
def listable(param: InfoTransaccion, cursor_mysql, fila, punto_venta, id_producto):
    try:

        if punto_venta == 0:  
            return True
        if punto_venta == 90:
            if fila.get('alta_catering') in ('Sí', "Si"):  
                return True
            else:
                return existe_alguno_en_alta(param, cursor_mysql, id_producto, "alta_catering in ('Si', 'Sí')")
        elif punto_venta == 91:
            if fila.get('alta_web') in ('Sí', "Si"):  
                return True
            else:
                return existe_alguno_en_alta(param, cursor_mysql, id_producto, "alta_web in ('Si', 'Sí')")
        elif punto_venta == 92:
            if fila.get('alta_glovo') in ('Sí', "Si"):   
                return True
            else:
                return existe_alguno_en_alta(param, cursor_mysql, id_producto, "alta_glovo in ('Si', 'Sí')")
        elif punto_venta in (1,2,3,4,5,6,7):
            if fila.get('alta_tpv') in ('Sí', "Si"):  
                return True
            else:
                return existe_alguno_en_alta(param, cursor_mysql, id_producto, "alta_tpv in ('Si', 'Sí')")


        return False
    
   
    except Exception as e:
        param.error_sistema(e=e, debug="listable.Exception")
        raise 