import logging
import logging.config
import traceback

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
def graba_log(mi_mensaje:dict, origen: str, e, logger = app_logger):
    try:
        loc = "no disponible"

        if isinstance(e, BaseException): # Comprueba si es una excepción
            tb = traceback.extract_tb(e.__traceback__)
            archivo, linea, funcion, texto_err = tb[-1]
            loc = f'{texto_err.replace("-", "_")} - {archivo.replace("-", "_")} - {linea} - {funcion}'

        # Intentar obtener un código de error
        if hasattr(e, 'errno'):  # Excepciones del sistema
            err_num = e.errno
        elif hasattr(e, 'args') and len(e.args) > 0:  # Excepciones genéricas con args
            err_num = e.args[0]
        else:
            err_num = 0

        logger.error(f"MI ERROR: {origen}: {mi_mensaje} - ERROR: {err_num} - {str(e)} - LOCALIZACION: {loc})")

    except Exception as e:
        return

# ------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------
def graba_log_info(mensaje, logger = time_logger):

    logger.info(mensaje)

    for handler in logger.handlers:
        print(f"Handler: {handler}")
        handler.flush()