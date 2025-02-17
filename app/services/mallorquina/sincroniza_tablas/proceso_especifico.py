import importlib

from app.utils.functions import graba_log, imprime

# import app.services.mallorquina.sincroniza_tablas.facturas_cabecera as facturas_cabecera
# import app.services.mallorquina.sincroniza_tablas.facturas_comanda as facturas_comanda
# import app.services.mallorquina.sincroniza_tablas.tikets_cabecera as tikets_cabecera

from app.utils.InfoTransaccion import InfoTransaccion

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def proceso(param: InfoTransaccion, conn_mysql, entidad, tabla, bbdd_config, campos, tabla_config):
    param.debug="proceso_especifico"
    valor_max = None

    try:
        mi_metodo = tabla_config["proceso_carga"]
        mi_modulo = importlib.import_module("app.services.mallorquina.sincroniza_tablas."+mi_metodo)
        func = getattr(mi_modulo, "proceso", None)  # Obtener la función desde otro módulo

        # if mi_metodo == "facturas_cabecera":
        #     func = getattr(facturas_cabecera, mi_metodo, None)  # Obtener la función desde otro módulo
        # elif mi_metodo == "facturas_comanda":
        #     func = getattr(facturas_comanda, mi_metodo, None)  # Obtener la función desde otro módulo
        # elif mi_metodo == "tikets_cabecera":
        #     func = getattr(tikets_cabecera, "proceso", None)  # Obtener la función desde otro módulo
        # elif mi_metodo == "tikets_comanda":
        #     func = getattr(tikets_comanda, mi_metodo, None)  # Obtener la función desde otro módulo

        imprime([func, tabla_config['Tabla_Destino'], entidad, tabla, bbdd_config, tabla_config], "=   --- proceso_especifico ---   ", 2)
        if func:
            resultado = func(param, conn_mysql, entidad, tabla, bbdd_config, campos, tabla_config)  # Ejecutar la función
        else:
            param.debug = f"no se encontró el módulo {mi_metodo} para cargar la tabla {tabla_config['Tabla_Destino']} con la tabla {tabla_config['Tabla_Origen']}."
            raise ValueError(f"El módulo {mi_metodo} no se encontró en 'app.services.mallorquina.sincroniza_tablas'.")

        return resultado

    except Exception as e:
        param.error_sistema()
        graba_log(param, "proceso_especifico.Exception", e)
        raise e
