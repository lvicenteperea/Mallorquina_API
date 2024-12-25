from fastapi import HTTPException
from datetime import datetime
#from decimal import Decimal

import json

# Para trabajar con Excel PANDA
import pandas as pd

# Para trabajar con Excel OPENPYXL
from openpyxl import Workbook
from openpyxl.styles import numbers

from app import mi_libreria as mi

from app.models.mll_cfg import obtener_configuracion_general
from app.config.db_mallorquina import get_db_connection_mysql, close_connection_mysql
from app.services.auxiliares.sendgrid_service import enviar_email

from app.utils.functions import graba_log
from app.utils.InfoTransaccion import InfoTransaccion

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def informe(param: InfoTransaccion) -> list:
    donde="Inicio"
    config = obtener_configuracion_general()
    resultado = []
    tienda = param.parametros[1]

    donde = "get_db_connection_mysql"
    try:
        conn_mysql = get_db_connection_mysql()
        cursor_mysql = conn_mysql.cursor(dictionary=True)

        donde = "Select"
        if tienda == 0:
            query = "SELECT * FROM mll_cfg_bbdd WHERE activo='S'"
            cursor_mysql.execute(query)
        else:
            query = "SELECT * FROM mll_cfg_bbdd WHERE id = %s AND activo='S'"
            cursor_mysql.execute(query, (tienda,))

        lista_bbdd = cursor_mysql.fetchall()

        for bbdd in lista_bbdd:
            mi.imprime([f"Procesando TIENDA: {json.loads(bbdd['Conexion'])['database']}"], "-")
            resultado.append(consultar(bbdd["ID"], conn_mysql, param))

        a_excel_con_pd(param, resultado)
        a_excel_con_openpyxl(param, resultado)
        
    except Exception as e:
        graba_log({"ret_code": -1, "ret_txt": f"{donde}"}, "Excepción arqueCajaInfo.informe", e)
        resultado = []
        param.ret_code = -1
        param.ret_txt = "Error General, contacte con su administrador"

    finally:
        close_connection_mysql(conn_mysql, cursor_mysql)

        enviar_email(config["Lista_emails"],
                     "Proceso finalizado",
                     ["El proceso de informes de arqueo de caja ha terminado."]
        )
        return resultado


#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def consultar(tienda, conn_mysql, param: InfoTransaccion) -> list:
    resultado = []
    donde="Inicio"
    fecha = param.parametros[0]

    donde = "get_db_connection_mysql"
    try:
        cursor_mysql = conn_mysql.cursor(dictionary=True)

        donde = "Select"
        query = f"""SELECT 
                        vd.id_tienda,
                        t.nombre Tienda,
                        vd.id_tpv,
                        tpv.descripcion Nombre_TPV,
                        vd.fecha,
                        vd.cierre_tpv_id,
                        vd.cierre_tpv_desc,
                        vmp.id_medios_pago,
                        mp.nombre Nombre_MdP,
                        SUM(vmp.ventas) AS total_ventas,
                        SUM(vmp.operaciones) AS total_operaciones
                    FROM mll_rec_ventas_diarias vd
                        JOIN  mll_rec_ventas_medio_pago vmp ON vd.id = vmp.id_ventas_diarias
                    LEFT JOIN mll_cfg_bbdd t         ON vd.id_tienda = t.id
                    LEFT JOIN tpv_puestos_facturacion tpv ON vd.id_tpv = tpv.id_puesto and vd.id_tienda = tpv.Origen_BBDD
                    LEFT JOIN mll_mae_medios_pago mp ON vmp.id_medios_pago = mp.id
                    where vd.id_tienda={tienda}
                      and vd.fecha = STR_TO_DATE('{fecha}', '%Y-%m-%d')
                    GROUP BY 
                        vd.id_tienda,
                        t.nombre,
                        vd.id_tpv,
                        tpv.descripcion,
                        vd.fecha,
                        vd.cierre_tpv_id,
                        vd.cierre_tpv_desc,
                        vmp.id_medios_pago,
                        mp.nombre
                 """
        donde="execute del cursor"
        cursor_mysql.execute(query)
        datos = cursor_mysql.fetchall()

        donde= "en el FOR"
        for row in datos:
            resultado.append(row)

    except Exception as e:
        graba_log({"ret_code": -1, "ret_txt": f"{donde}"}, "Excepción arqueCajaInfo.consultar", e)
        resultado = []
        param.ret_code = -1
        param.ret_txt = "Error General, contacte con su administrador"

    finally:        
        return resultado



#----------------------------------------------------------------------------------------
# Creamos el escritor de Excel con la librería PANDA
#----------------------------------------------------------------------------------------
def a_excel_con_pd(param: InfoTransaccion, todos_los_conjuntos):
    path = "app/datos/cierre_caja/"

    with pd.ExcelWriter(f"{path}resultado_panda.xlsx") as writer:
        for sublista in todos_los_conjuntos:
            # Si la sublista está vacía, pasamos de largo
            if not sublista:
                continue
            
            # 1. Convertimos la sublista (lista de dicts) a DataFrame
            df = pd.DataFrame(sublista)

            # 2. Eliminamos las columnas que NO queremos exportar
            columnas_a_eliminar = ["id_tienda", "id_tpv", "cierre_tpv_id", "id_medios_pago"]
            df.drop(columns=columnas_a_eliminar, axis=1, inplace=True)

            # 3. Convertimos 'fecha' a formato dd/mm/aaaa
            #    Primero la parseamos a datetime y luego la formateamos
            df["fecha"] = pd.to_datetime(df["fecha"]).dt.strftime('%d/%m/%Y')

            # 4. Convertimos 'total_ventas' y 'total_operaciones' a floats, luego a strings con coma decimal
            df["total_ventas"] = df["total_ventas"].astype(float).map(
                lambda x: f"{x:.2f}".replace('.', ',')  # 2 decimales con coma
            )
            df["total_operaciones"] = df["total_operaciones"].astype(float).map(
                lambda x: f"{x:.0f}"  # sin decimales (asumiendo que es un entero), 
                                    # si quisieras 2 decimales: f"{x:.2f}".replace('.', ',')
            )

            # 5. Nombramos la hoja según la columna "Tienda" (limitamos a 31 caracteres para Excel)
            nombre_tienda = df["Tienda"].iloc[0]
            nombre_hoja = nombre_tienda[:31]

    # 6. Exportamos este DataFrame a una hoja en el Excel
    df.to_excel(writer, sheet_name=nombre_hoja, index=False)

    print("¡Excel creado con éxito!")


#----------------------------------------------------------------------------------------
# Creamos el escritor de Excel con la librería PANDA
#----------------------------------------------------------------------------------------
def a_excel_con_openpyxl(param: InfoTransaccion, todos_los_conjuntos):
    # 1. Creamos el libro de Excel y removemos la hoja por defecto
    wb = Workbook()
    ws_default = wb.active
    wb.remove(ws_default)
    path = "app/datos/cierre_caja/"

    # 2. Columnas que NO queremos mostrar
    columnas_excluir = {"id_tienda", "id_tpv", "cierre_tpv_id", "id_medios_pago"}

    for sublista in todos_los_conjuntos:
        # Si la sublista está vacía, la saltamos
        if not sublista:
            continue

        # 3. Preprocesamos la sublista para convertir valores y eliminar columnas
        #    - Convertimos "fecha" a datetime
        #    - Convertimos "total_ventas" y "total_operaciones" a float
        #    - Quitamos las columnas que no queremos
        datos_procesados = []
        for fila in sublista:
            # Creamos una copia limpia
            nueva_fila = {}
            for k, v in fila.items():
                if k in columnas_excluir:
                    continue  # saltar columnas no deseadas

                if k == "fecha":
                    # Convertir "AAAA-MM-DD" a datetime
                    #nueva_fila[k] = datetime.strptime(v, "%Y-%m-%d").date()
                    nueva_fila[k] = datetime.strptime(v, "%Y-%m-%d").date()

                elif k in ("total_ventas", "total_operaciones"):
                    # Convertir a float
                    nueva_fila[k] = float(v)
                else:
                    # Dejar el valor tal cual
                    nueva_fila[k] = v
            datos_procesados.append(nueva_fila)

        # 4. Obtenemos el nombre de la tienda (primer elemento)
        nombre_tienda = datos_procesados[0]["Tienda"]
        # Máximo 31 caracteres para el nombre de la hoja
        sheet_name = nombre_tienda[:31]

        # 5. Creamos una hoja nueva con el nombre de la tienda
        ws = wb.create_sheet(title=sheet_name)

        # 6. Escribimos la CABECERA
        #    Obtenemos las columnas del primer registro (ordenadas)
        columnas = list(datos_procesados[0].keys())
        ws.append(columnas)  # primera fila con los nombres de columna

        # 7. Escribimos los datos fila por fila
        for fila in datos_procesados:
            row_data = [fila[col] for col in columnas]
            ws.append(row_data)

        # 8. Aplicamos FORMATO a las celdas
        #    - Fecha en formato dd/mm/yyyy
        #    - total_ventas con 2 decimales
        #    - total_operaciones con 0 decimales (o lo que prefieras)
        
        # Calculamos los índices de columna para "fecha", "total_ventas", etc.
        # ojo: openpyxl usa 1-based index, ws["A1"] es row=1,col=1
        idx_fecha = columnas.index("fecha") + 1 if "fecha" in columnas else None
        idx_ventas = columnas.index("total_ventas") + 1 if "total_ventas" in columnas else None
        idx_operaciones = columnas.index("total_operaciones") + 1 if "total_operaciones" in columnas else None

        # Recorremos las filas de datos (comienzan en la 2, ya que la 1 es cabecera)
        for row in range(2, 2 + len(datos_procesados)):
            # Fecha (dd/mm/yyyy)
            if idx_fecha:
                cell_fecha = ws.cell(row=row, column=idx_fecha)
                # Indicamos que es un formato de fecha dd/mm/yyyy
                cell_fecha.number_format = "DD/MM/YYYY"

            # total_ventas con 2 decimales
            if idx_ventas:
                cell_ventas = ws.cell(row=row, column=idx_ventas)
                cell_ventas.number_format = "#,##0.00"

            # total_operaciones sin decimales
            if idx_operaciones:
                cell_oper = ws.cell(row=row, column=idx_operaciones)
                cell_oper.number_format = "#,##0"

    # 9. Guardamos el archivo
    wb.save(f"{path}resultado_openpyxl.xlsx")
    print("¡Excel creado con éxito con openpyxl!")
