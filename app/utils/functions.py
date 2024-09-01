from app.utils.InfoTransaccion import InfoTransaccion
import logging
import logging.config
import traceback

# ------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------
'''
Expande una lista que tenga dentro un elemento InfoTransaccion
'''
def expande_lista(lista:list):
        new_list = []

        for item in lista:
            if isinstance(item, InfoTransaccion):
                # Si el elemento es una instancia de InfoTransaccion, lo expandimos
                new_list.extend(item.to_list())
            else:
                # Si no, simplemente lo añadimos a la nueva lista
                new_list.append(item)

        return new_list



# ------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------
# esto sería con fichero de inicialización
try:
    print("inicializa logging")
    logging.config.fileConfig('app/logging.ini')
except Exception as e:
    print(f"Error configuring logging: {e}")

# Obtén los loggers
# logger = logging.getLogger('app_logger')
app_logger = logging.getLogger('app_logger')
time_logger = logging.getLogger('time_logger')


# ------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------
def graba_log(mi_mensaje:dict, origen, e, logger = app_logger):

    tb = traceback.extract_tb(e.__traceback__)
    archivo, linea, funcion, texto_err = tb[-1]

    archivo = archivo.replace("-", "_")
    texto_err = texto_err.replace("-", "_")
    if "mensaje" in mi_mensaje and isinstance(mi_mensaje["mensaje"], str):
        mi_mensaje["mensaje"] = mi_mensaje["mensaje"].replace("-", "_")

    logger.error(f"de tiempos {origen}: {mi_mensaje} - {texto_err} - {archivo} - {linea} - {funcion}")


# ------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------
def graba_log_info(mensaje, logger = time_logger):

    logger.info(mensaje)

    for handler in logger.handlers:
        print(f"Handler: {handler}")
        handler.flush()
