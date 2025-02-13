import os
from datetime import datetime
import pandas as pd

from app.models.mll_cfg import obtener_cfg_general, close_connection_mysql
from app.config.db_mallorquina import get_db_connection_mysql, close_connection_mysql
from app.services.auxiliares.sendgrid_service import enviar_email

from app.utils.mis_excepciones import MiException
from app.utils.functions import graba_log, imprime
from app.utils.InfoTransaccion import InfoTransaccion
from app.config.settings import settings

RUTA = os.path.join(f"{settings.RUTA_DATOS}", "encargos")

# -----------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------
def proceso(param: InfoTransaccion) -> list:
    funcion = "carga_productos_erp.proceso"
    param.debug="Inicio"
    resultado = []

    try:
        config = obtener_cfg_general(param)

        param.debug = "archivos"
        archivos = [f for f in os.listdir(RUTA) if f.endswith(".xlsx")]

        param.debug = "get_db_connection_mysql"
        conn_mysql = get_db_connection_mysql()
        param.debug = "cursor_____"
        cursor = conn_mysql.cursor(dictionary=True)

        # creamos la tabla si existe
        crear_tabla(conn_mysql)

        # Aquí va la lógica específica para cada bbdd
        resultado = carga(param, archivos, conn_mysql, cursor)

        # Confirmar transacciones y cerrar conexión
        conn_mysql.commit()

        return resultado

    except Exception as e:
        param.error_sistema()
        graba_log(param, "proceso.Exception", e)
        raise 
        
    finally:
        close_connection_mysql(conn_mysql, cursor)

        enviar_email(config["Lista_emails"],
                     "Proceso finalizado",
                     "El proceso de carga ha terminado."
        )

# -----------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------
def carga (param: InfoTransaccion, archivos: list, conn_mysql, cursor):
    resultado = []
    param.debug = "encargos_navidad.carga"
    
    try:

        for archivo in archivos:
            tienda = archivo.split(" ")[0]
            ruta_archivo = os.path.join(RUTA, archivo)

            xls = pd.ExcelFile(ruta_archivo)
            hojas_validas = [hoja for hoja in xls.sheet_names if "-" in hoja]

            for hoja in hojas_validas:
                df = pd.read_excel(xls, sheet_name=hoja)

                for _, row in df.iterrows():
                    num_pedido = row.iloc[0] if not pd.isna(row.iloc[0]) else "" # Columna A
                    param.debug= f"archivo: {archivo}  -  pedido: {num_pedido}  -  Producto: {num_pedido}  "
                    imprime([f"archivo: {archivo}", f"pedido: {num_pedido}", f"Producto: {row.iloc[6]}"], "=")

                    # num_pedido = int(row.iloc[0]) if not pd.isna(row.iloc[0]) else None # Columna A
                    nombre = row.get("NOMBRE", "")  if not pd.isna(row.get("NOMBRE", "?")) else "?"
                    apellidos = row.get("APELLIDOS", "")  if not pd.isna(row.get("APELLIDOS", "?")) else "?"
                    direccion = row.get("DIRECCIÓN", "")  if not pd.isna(row.get("DIRECCIÓN", "?")) else "?"
                    telefono = row.get("TEEFONO", row.get("TELEFONO", "?"))  if not pd.isna(row.get("TEEFONO", row.get("TELEFONO", "?"))) else "?"

                    unidades_str = str(row.get("UNIDADES", "0")) if not pd.isna(row.get("UNIDADES", "0")) else "0"
                    if ''.join(filter(str.isdigit, unidades_str)):
                        unidades = int(''.join(filter(str.isdigit, unidades_str)))
                    else:
                        unidades = 0

                    productos = row.get("PRODUCTOS", "")  if not pd.isna(row.get("PRODUCTOS", "?")) else "?"
                    pagado = row.get("PAGADO", "") if not pd.isna(row.get("PAGADO", "?")) else "?"  # Validar NaN
                    dia_entrega = pd.to_datetime(row.get("DIA ENTREGA", None), errors='coerce')
                    hora_entrega = row.get("HORA ENTREGA", "")  if not pd.isna(row.get("HORA ENTREGA", "?")) else "?"
                    dia_venta = pd.to_datetime(row.get("DIA VENTA", None), errors='coerce')
                    entregado = row.get("ENTREGADO", "")  if not pd.isna(row.get("ENTREGADO", "?")) else "?"
                    observaciones = row.get("OBSERVACIONES", "")  if not pd.isna(row.get("OBSERVACIONES", "?")) else "?"

                    query = """
                    INSERT INTO mll_otr_encargos_navidad (
                        tienda, hoja, campaign, num_pedido, nombre, apellidos, direccion, telefono, unidades, unidades_str,
                        productos, pagado, dia_entrega, hora_entrega, dia_venta, entregado, observaciones
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    imprime([f"query: {query}",tienda, hoja, "Navidad 2024", num_pedido, nombre, apellidos, direccion, telefono, unidades, unidades_str,
                        productos, pagado, dia_entrega, hora_entrega, dia_venta, entregado, observaciones], "=")

                    values = (
                        tienda, hoja.strip(), "Navidad 2024", num_pedido, nombre, apellidos, direccion, telefono, unidades, unidades_str,
                        productos, pagado, dia_entrega, hora_entrega, dia_venta, entregado, observaciones
                    )

                    cursor.execute(query, values)

            resultado.append(archivo)

        return resultado


    except Exception as e:
        param.error_sistema()
        graba_log(param, "carga.Exception", e)
        raise 

# -----------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------
def crear_tabla(conn_mysql):
    query = """CREATE TABLE IF NOT EXISTS mll_otr_encargos_navidad (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    campaign VARCHAR(50),
                    tienda VARCHAR(255) NOT NULL,
                    hoja VARCHAR(5) not null,
                    num_pedido VARCHAR(50),
                    nombre VARCHAR(255),
                    apellidos VARCHAR(255),
                    direccion VARCHAR(255),
                    telefono VARCHAR(50),
                    unidades_str VARCHAR(20),
                    unidades INT,
                    productos VARCHAR(255),
                    pagado VARCHAR(50),
                    dia_entrega DATE,
                    hora_entrega VARCHAR(50),
                    dia_venta DATE,
                    entregado VARCHAR(50),
                    observaciones TEXT
               ) ENGINE=InnoDB;
            """
    cursor = conn_mysql.cursor()
    cursor.execute(query)
    cursor.close()

# -----------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------
def convertir_a_decimal(valor):
    try:
        return float(str(valor).replace(',', '.'))
    except ValueError:
        return 0.0


