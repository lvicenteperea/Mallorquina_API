from app.utils.functions import graba_log, imprime

import app.services.mallorquina.sincroniza_tablas.facturas_cabecera as facturas_cabecera
from app.utils.InfoTransaccion import InfoTransaccion

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def proceso(param: InfoTransaccion, conn_mysql, entidad, tabla, bbdd_config, nombre_tabla, campos, tabla_config):
    param.debug="proceso_especifico"
    valor_max = None

    try:
        mi_metodo = tabla_config["proceso_carga"]

        func = getattr(facturas_cabecera, mi_metodo, None)  # Obtener la función desde otro módulo

        imprime([mi_metodo, tabla_config['Tabla_Destino'], entidad, tabla, bbdd_config, nombre_tabla, tabla_config], "=   --- proceso_especifico ---   ", 2)
        if func:
            resultado = func(param, conn_mysql, entidad, tabla, bbdd_config, nombre_tabla, campos, tabla_config)  # Ejecutar la función
        else:
            param.debug = f"no se encontró el módulo {mi_metodo} para cargar la tabla {tabla_config['Tabla_Destino']} con la tabla {nombre_tabla}."
            raise ValueError(f"La función {mi_metodo} no se encontró en el módulo.")

        return resultado

    except Exception as e:
        param.error_sistema()
        graba_log(param, "proceso_especifico.Exception", e)
        raise e
