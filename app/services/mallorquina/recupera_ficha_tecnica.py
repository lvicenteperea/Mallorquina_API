import os
import shutil
from datetime import datetime
import pymysql

from app.utils.utilidades import graba_log, imprime
from app.config.db_mallorquina import get_db_connection_mysql, close_connection_mysql
from app.utils.InfoTransaccion import InfoTransaccion
from app.config.settings import settings

# Rutas de los archivos
LOGO =        os.path.join(settings.WEB_RUTA_LOCAL, settings.WEB_RUTA_IMAGEN, "Logotipo con tagline - negro.svg")
RUTA_ICONOS = os.path.join(settings.WEB_RUTA_LOCAL, settings.WEB_RUTA_IMAGEN, "alergenos/")

PLANTILLA       = os.path.join(settings.RUTA_ALERGENOS, "plantilla_productos.html")
PLANTILLA_FICHA = os.path.join(settings.RUTA_ALERGENOS, "plantilla_ficha_tecnica.html")

FICH_NO_IMPRIMIBLES = os.path.join(settings.RUTA_ALERGENOS_HTML, "no_imprimibles.csv")

#----------------------------------------------------------------------------------------
# Principal del Proceso de generación de html
#----------------------------------------------------------------------------------------
def proceso(param: InfoTransaccion) -> list:
    resultado = []
    param.debug = "proceso"

    try:
        param.debug = "parámetros"
        if param.parametros[0]:
            id_producto = int(param.parametros[0])
        else:
            raise Exception

        conn_mysql = get_db_connection_mysql()
        cursor_mysql = conn_mysql.cursor(pymysql.cursors.DictCursor)

        cursor_mysql.execute("""SELECT  t.ID, 
                                        t.nombre, 
                                        t.codigo_barras, 
                                        t.composicion_etiqueta, 
                                        t.composicion_completa, 
                                        t.temporada, 
                                        t.descatalogado, 
                                        t.familia_cod, 
                                        t.familia_desc, 
                                        t.grupo_de_carta, 
                                        t.centro_preparacion_1, t.centro_preparacion_2, t.centro_preparacion_3, 
                                        t.alta_tpv,             t.alta_glovo,           t.alta_web,             t.alta_catering, 
                                        t.codigo_alergenos,     t.listado_alergenos,    t.nombre_alergenos, 
                                        -- Alérgenos: toma de la fila de alérgenos si corresponde
                                        CASE WHEN t.codigo_alergenos != t.ID AND t_alerg.ID IS NOT NULL THEN t_alerg.huevo ELSE t.huevo END AS huevo,
                                        CASE WHEN t.codigo_alergenos != t.ID AND t_alerg.ID IS NOT NULL THEN t_alerg.leche ELSE t.leche END AS leche,
                                        CASE WHEN t.codigo_alergenos != t.ID AND t_alerg.ID IS NOT NULL THEN t_alerg.crustaceos ELSE t.crustaceos END AS crustaceos,
                                        CASE WHEN t.codigo_alergenos != t.ID AND t_alerg.ID IS NOT NULL THEN t_alerg.cascara ELSE t.cascara END AS cascara,
                                        CASE WHEN t.codigo_alergenos != t.ID AND t_alerg.ID IS NOT NULL THEN t_alerg.gluten ELSE t.gluten END AS gluten,
                                        CASE WHEN t.codigo_alergenos != t.ID AND t_alerg.ID IS NOT NULL THEN t_alerg.pescado ELSE t.pescado END AS pescado,
                                        CASE WHEN t.codigo_alergenos != t.ID AND t_alerg.ID IS NOT NULL THEN t_alerg.altramuz ELSE t.altramuz END AS altramuz,
                                        CASE WHEN t.codigo_alergenos != t.ID AND t_alerg.ID IS NOT NULL THEN t_alerg.mostaza ELSE t.mostaza END AS mostaza,
                                        CASE WHEN t.codigo_alergenos != t.ID AND t_alerg.ID IS NOT NULL THEN t_alerg.cacahuetes ELSE t.cacahuetes END AS cacahuetes,
                                        CASE WHEN t.codigo_alergenos != t.ID AND t_alerg.ID IS NOT NULL THEN t_alerg.apio ELSE t.apio END AS apio,
                                        CASE WHEN t.codigo_alergenos != t.ID AND t_alerg.ID IS NOT NULL THEN t_alerg.sulfitos ELSE t.sulfitos END AS sulfitos,
                                        CASE WHEN t.codigo_alergenos != t.ID AND t_alerg.ID IS NOT NULL THEN t_alerg.soja ELSE t.soja END AS soja,
                                        CASE WHEN t.codigo_alergenos != t.ID AND t_alerg.ID IS NOT NULL THEN t_alerg.moluscos ELSE t.moluscos END AS moluscos,
                                        CASE WHEN t.codigo_alergenos != t.ID AND t_alerg.ID IS NOT NULL THEN t_alerg.sesamo ELSE t.sesamo END AS sesamo,
                                        -- resto de campos igual que antes
                                        t.poblacion_diana, 
                                        t.uso_esperado, 
                                        t.condiciones_almacenamiento, 
                                        t.condiciones_conservacion, 
                                        t.vida_fri_desde_fabric, 
                                        t.peso_neto_aprox, 
                                        t.rec_aerobios_totales, 
                                        t.rec_enterobacterias, 
                                        t.rec_escherichia_coli, 
                                        t.rec_staphylococcus_aureus, 
                                        t.det_salmonella_cpp, 
                                        t.rec_listeria_monocytogenes, 
                                        t.rec_mohos_y_levaduras, 
                                        t.valor_energetico_kcal_kj, 
                                        t.grasas_g, 
                                        t.de_las_cuales_saturadas_g, 
                                        t.hidratos_de_carbono_g, 
                                        t.de_los_cuales_azucares_g, 
                                        t.proteinas_g, 
                                        t.sal_g, 
                                        t.fibra_dietetica_g, 
                                        t.otros, 
                                        t.fec_modificacion
                                   FROM erp_productos t
                                    LEFT JOIN erp_productos t_alerg ON t.codigo_alergenos = t_alerg.ID
                                    WHERE t.ID = %s""",
                             (id_producto,))
        producto = cursor_mysql.fetchone()
        close_connection_mysql(conn_mysql, cursor_mysql)


        # Generación del HTML
        html = generar_html(param, producto)

        resultado = [f"Ficheros generados correctamente", html]
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
def generar_html(param: InfoTransaccion, producto: dict) -> str: 
    param.debug = "generar_html"
    html_final = ""

    try:
        fichas_html = cargar_plantilla(param, PLANTILLA_FICHA)

        # Generar las fichas técnicas
        fichas_content = ""
        composicion = imprimible(param, producto)
        if 1 == 1: # composicion: 
            id_producto = producto['ID']
            # imprime([producto], "-    ..... Datos de productos .....", 2)
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

                'Poblacion_diana': producto.get("poblacion_diana", "").strip() or " ",
                'uso_esperado': producto.get("uso_esperado", "").strip() or " ",
                'Condiciones_conservacion': producto.get("condiciones_conservación", "").strip() or " ",

                'vida_en_lugar_fresco_y_seco': producto.get("vida_en_lugar_fresco_y_seco", "").strip() or " ",
                'vida_en_refrigeracion': producto.get("vida_en_refrigeracion", "").strip() or " ",
                'vida_en_congelacion': producto.get("vida_en_congelacion", "").strip() or " ",
            }
            fichas_content += reemplazar_campos(fichas_html, ficha_campos)
            # imprime([ficha_campos], "-    ..... Datos de la ficha técnica .....", 2)

        return fichas_content
    
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
def reemplazar_fijos(param, plantilla):
    html = plantilla
    try:
        ruta = os.path.join(RUTA_ICONOS, "")

        html = html.replace("{LOGO}", LOGO)
        html = html.replace("{titulo_principal}", "Listado de productos")
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
        param.error_sistema(e=e, debug="reemplazar_fijos.Exception")
        raise 



#----------------------------------------------------------------------------------------
# Reemplazar placeholders en la plantilla
#----------------------------------------------------------------------------------------
def reemplazar_campos(plantilla, campos):
    for placeholder, valor in campos.items():
        # imprime([placeholder, "{"+f"{placeholder}"+"}", valor, valor or f"{placeholder}"],'=')
        plantilla = plantilla.replace("{"+f"{placeholder}"+"}", f"{valor}" or f"{placeholder}")

    return plantilla



#----------------------------------------------------------------------------------------
# Comprueba que tenemos descripción de la composición del productos, porque si no tiene, 
# no se puede imprimir
#----------------------------------------------------------------------------------------
def imprimible(param: InfoTransaccion, fila):
    try:
        composicion = fila.get("composicion_completa", "").strip() or ""
        if not composicion: 
            composicion = fila.get("composicion_etiqueta", "").strip() or ""
            
        if not composicion:
            param.ret_code += 1

        return composicion
   
    except Exception as e:
        param.error_sistema(e=e, debug="cargar_plantilla.Exception")
        raise 


#----------------------------------------------------------------------------------------
# Graba un archivo pero previamente hace una copia del mismo si ya existe
#----------------------------------------------------------------------------------------
# def graba_archivo(param: InfoTransaccion, archivo: str, contenido: str):
#     try: 
#         # Verificar si el archivo ya existe
#         if os.path.exists(archivo):
#             # Crear el nombre del archivo de copia con fecha y hora
#             timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
#             backup_nombre = f"{os.path.splitext(archivo)[0]}_{timestamp}.html"

#             # Copiar el archivo con el nuevo nombre
#             shutil.copy(archivo, backup_nombre)

#         # Guardar el nuevo archivo
#         with open(archivo, 'w', encoding='utf-8') as f:
#             f.write(contenido)



#     except Exception as e:
#         param.error_sistema(e=e, debug="graba_archivo.Exception")
#         raise 

