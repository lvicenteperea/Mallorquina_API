import os
from fastapi import HTTPException
import pandas as pd

from app.models.mll_cfg import obtener_cfg_general, close_connection_mysql
from app.models.mll_cfg_bbdd import obtener_conexion_bbdd_origen
from app.config.db_mallorquina import get_db_connection_sqlserver, get_db_connection_mysql, close_connection_mysql
from app.services.auxiliares.sendgrid_service import enviar_email

from app.utils.mis_excepciones import MadreException
from app.utils.functions import graba_log, imprime
from app.utils.InfoTransaccion import InfoTransaccion
from app.config.settings import settings

# -----------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------
def proceso(param: InfoTransaccion) -> list:
    funcion = "carga_productos_erp.proceso"
    param.debug="Inicio"
    resultado = []

    try:
        config = obtener_cfg_general(param)

        if len(param.parametros) >= 1  and param.parametros[0]:
            excel = os.path.join(f"{settings.RUTA_DATOS}/erp", f"{param.parametros[0]}")

        else:
            param.registrar_error(ret_txt= "No ha llegado fichero origen para cargar", debug=f"{funcion}.sin parametro entrada")
            raise MadreException(param = param)

        # Aquí va la lógica específica para cada bbdd
        resultado = carga(param, excel)

        return resultado

    except MadreException as e:
        raise
                    
    except HTTPException as e:
        param.error_sistema()
        graba_log(param, "proceso.HTTPException", e)
        raise

    except Exception as e:
        param.error_sistema()
        graba_log(param, "proceso.Exception", e)
        raise HTTPException(status_code=e.status_code, detail=e.detail)
        
    finally:
        enviar_email(config["Lista_emails"],
                     "Proceso finalizado",
                     "El proceso de carga ha terminado."
        )

# -----------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------
def carga (param: InfoTransaccion, excel):
    resultado = []
    param.debug = "carga_productos_erp.carga"
    
    try:
        
        # Leer el Excel
        df = pd.read_excel(excel)

        param.debug = "get_db_connection_mysql"
        conn_mysql = get_db_connection_mysql()
        param.debug = "cursor_____"
        cursor = conn_mysql.cursor(dictionary=True)

        param.debug = "Mapeo"
        # Mapeo de columnas del Excel con los campos de la tabla
        mapping = {
            'codigo': 'ID',
            'nombre': 'nombre',
            'composicion_para_etiqueta': 'composicion_etiqueta',
            'composicion_completa': 'composicion_completa',
            'temporada': 'temporada',
            #'familia_cod': 'familia_cod',
            'descripcion': 'familia_desc',
            'grupo_de_carta': 'grupo_de_carta',
            'alta_tpv': 'alta_tpv',
            'alta_glovo': 'alta_glovo',
            'alta_web': 'alta_web',
            'alta_catering': 'alta_catering',
            'huevo': 'huevo',
            'leche': 'leche',
            'crustaceos': 'crustaceos',
            'cascara': 'cascara',
            'gluten': 'gluten',
            'pescado': 'pescado',
            'altramuz': 'altramuz',
            'mostaza': 'mostaza',
            'cacahuetes': 'cacahuetes',
            'apio': 'apio',
            'sulfitos': 'sulfitos',
            'soja': 'soja',
            'moluscos': 'moluscos',
            'sesamo': 'sesamo',
            'poblacion_diana': 'poblacion_diana',
            'uso_esperado': 'uso_esperado',
            'condiciones_almacenamiento': 'condiciones_almacenamiento',
            'condiciones_conservacion': 'condiciones_conservacion',
            'vida_fri_desde_fabric': 'vida_fri_desde_fabric',
            'peso_neto_aprox': 'peso_neto_aprox',
            'rec_aerobios_totales': 'rec_aerobios_totales',
            'rec_enterobacterias': 'rec_enterobacterias',
            'rec_escherichia_coli': 'rec_escherichia_coli',
            'rec_staphylococcus_aureus': 'rec_staphylococcus_aureus',
            'det_salmonella_cpp': 'det_salmonella_cpp',
            'rec_listeria_monocytogenes': 'rec_listeria_monocytogenes',
            'rec_mohos_y_levaduras': 'rec_mohos_y_levaduras',
            'valor_energetico_kcal_kj': 'valor_energetico_kcal_kj',
            'grasas_g': 'grasas_g',
            'de_las_cuales_saturadas_g': 'de_las_cuales_saturadas_g',
            'hidratos_de_carbono_g': 'hidratos_de_carbono_g',
            'de_los_cuales_azucares_g': 'de_los_cuales_azucares_g',
            'proteinas_g': 'proteinas_g',
            'sal_g': 'sal_g',
            'fibra_dietetica_g': 'fibra_dietetica_g',
            'otros': 'otros',
            'fec_modificacion': 'fec_modificacion'
        }

        # Procesar registros del Excel
        for x, row in df.iterrows():
            row = row.fillna('')  # Reemplazar valores NaN con cadenas vacías
            codigo = row['codigo']
            fec_modificacion = row.get('fec_modificacion', None)

            # Consultar si el producto ya existe
            param.debug = "select 1"
            cursor.execute("SELECT updated_at FROM erp_productos WHERE ID = %s", (codigo,))
            resultado = cursor.fetchone()

            if resultado:
                updated_at = resultado[0]
                # Actualizar si la fecha de modificación en el Excel es posterior
                if fec_modificacion and fec_modificacion > updated_at:
                    param.debug = "update___"
                    campos = ', '.join(f"{v} = %s" for k, v in mapping.items() if k in row)
                    valores = tuple(row[k] for k in mapping.keys() if k in row) + (codigo,)
                    cursor.execute(f"UPDATE erp_productos SET {campos} WHERE ID = %s", valores)
            else:
                # Insertar nuevo registro
                param.debug = f"insert___ {x}" #{row}"
                columnas = ', '.join(mapping.values())
                marcadores = ', '.join(['%s'] * len(mapping))
                valores = tuple(row[k] if k in row else '' for k in mapping.keys())
                valores = tuple(elemento.replace("Si", "Sí") if isinstance(elemento, str) else elemento for elemento in valores)
                # for k in mapping.keys():
                #     if k not in row:
                #         print("NO encuentra ",k)
                cursor.execute(f"INSERT INTO erp_productos ({columnas}) VALUES ({marcadores})", valores)

            # Procesar campos "pvp_*" para insertar en erp_productos_pvp
            for col in row.index:
                if col.startswith('pvp_') and row[col]:
                    id_bbdd, tipo = determinar_bbdd_y_tipo(col)
                    pvp = convertir_a_decimal(row[col])
                    # imprime([id_bbdd, tipo, pvp, col, row[col]], "=")
                    param.debug = "insert 2___"
                    for x in range(0, len(id_bbdd)):
                        cursor.execute(
                            """
                            INSERT INTO erp_productos_pvp (id_producto, id_BBDD, tipo, pvp)
                            VALUES (%s, %s, %s, %s)
                            """,
                            (codigo, id_bbdd[x], tipo, pvp)
                        )

        # Confirmar transacciones y cerrar conexión
        conn_mysql.commit()

        return resultado

    except MadreException as e:
        raise
                    
    except HTTPException as e:
        param.error_sistema()
        graba_log(param, "carga.HTTPException", e)
        raise

    except Exception as e:
        param.error_sistema()
        graba_log(param, "carga.Exception", e)
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    finally:
        close_connection_mysql(conn_mysql, cursor)


# -----------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------
def determinar_bbdd_y_tipo(columna):
    mapping_bbdd_tipo = {
        'pvp_tienda_sol_quevedo': ([4, 5], 'Tienda'),
        'pvp_tienda_resto': ([1, 3, 6, 7, 8, 9], 'Tienda'),
        'pvp_terraza_quevedo': ([4], 'Terraza'),
        'pvp_tiendas_salon': ([1, 3, 4, 6, 7, 8, 9], 'Salón'),
        'pvp_salon_sol': ([5], 'Salón'),
        'pvp_web': ([2], 'Tienda'),
        'pvp_glovo': ([10], 'Tienda'),
        'pvp_catering': ([11], 'Tienda')
    }
    return mapping_bbdd_tipo.get(columna, ([], ''))

# -----------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------
def convertir_a_decimal(valor):
    try:
        return float(str(valor).replace(',', '.'))
    except ValueError:
        return 0.0


