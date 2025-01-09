from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import json

from app.utils.mis_excepciones import MadreException
from app.utils.functions import graba_log, imprime


'''
# -----------------------------------------------------------------------------------------------
# LOGGING
#import logging
#import logging.config

# # esto sería con basicConfig
# logging.basicConfig(
#     level=logging.DEBUG,  # Configura el nivel de logging
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Formato del log
#     handlers=[
#         logging.FileHandler("app/logs/app.log"),  # Guarda los logs en un archivo
#         logging.StreamHandler()  # También muestra los logs en la consola
#     ]
# )
 

# Configuración manual
# logger.setLevel(logging.DEBUG)

# # Crear un formato de log
# formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# # Crear y configurar el handler para escribir en archivo
# file_handler = logging.handlers.RotatingFileHandler("app/logs/app.log", maxBytes=1000000, backupCount=5)
# file_handler.setFormatter(formatter)
# logger.addHandler(file_handler)
# 
# Crear y configurar el handler para escribir en la consola
# console_handler = logging.StreamHandler()
# console_handler.setFormatter(formatter)
# logger.addHandler(console_handler)
# -----------------------------------------------------------------------------------------------

# # esto sería con fichero de inicialización
# try:
#     logging.config.fileConfig('app/logging.ini')
# except Exception as e:
#     print(f"Error configuring logging: {e}")

# logger = logging.getLogger('app_logger')

# logger.info("Inicio de la ejecución")
'''
# -----------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------
def imprime_mi_log(tipo_excepcion, exc):
    print(f"--------------------------------------{tipo_excepcion}-----------------------------------------------")
    print("Argumentos de la excepción:", exc.args)
    print(f"--------------------------------------------------------------------------------------------------------")
    print(f"Detalle: {exc.detail}")
    print(f"Estado: {exc.status_code}")
    print(f"Encabezados: {exc.headers}")

    #imprime([tipo_excepcion, "Trace:", traceback.extract_tb(exc.detail["traceback"])], "=")
    if hasattr(exc, 'status_code'): 
        imprime([tipo_excepcion, "Estatus:", type(exc.status_code), exc.status_code], "=")
    if hasattr(exc, 'detail'): 
        imprime([tipo_excepcion, "Detail:", type(exc.detail), exc.detail], "=")
    if hasattr(exc, 'param'): 
        imprime([tipo_excepcion, "Param: ", exc.param], "=")

# -----------------------------------------------------------------------------------------------
# EXCEPTION HANDLERS
# -----------------------------------------------------------------------------------------------
async def madre_exception_handler(request: Request, exc: MadreException):
# -----------------------------------------------------------------------------------------------
    imprime_mi_log("madre_exception_handler", exc)

    if isinstance(exc.mi_mensaje, dict):
        mi_mensaje = exc.mi_mensaje
    else:
        mi_mensaje = {"ret_code": -1,
                      "ret_txt": exc.mi_mensaje,
                     }

    graba_log(mi_mensaje, "madre_exception", exc)

    return JSONResponse(
        status_code = 500 if mi_mensaje['ret_code'] == -99 else 400, # exc.status_code
        content={"codigo_error (status_code)": exc.status_code, "mensaje": mi_mensaje},
    )

# -----------------------------------------------------------------------------------------------
async def http_exception_handler(request: Request, exc: HTTPException):
    '''
    if hasattr(exc, 'detail') and exc.detail is not None and isinstance(exc.detail, dict):
        mi_mensaje = {"ret_code": exc.detail['ret_code'],
                      "ret_txt": str(exc.detail.get('ret_txt', exc.detail.get("excepcion", "Sin texto asociado"))),
                     }
    else:
        mi_mensaje = {"ret_code": -1,
                      "ret_txt": exc.detail,
                     }

    graba_log(mi_mensaje, 
                "HTTPException", 
                exc # str(exc.detail.get("excepcion", exc.detail.get('ret_txt',"Sin texto asociado")))
                )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"codigo_error": exc.status_code, "mensaje": mi_mensaje},
    )
    '''
# -----------------------------------------------------------------------------------------------
    if hasattr(exc, "status_code"):
        status_code = getattr(exc, "status_code", 500)
    else:
        status_code = 500  # Estatus predeterminado para errores genéricos

    if hasattr(exc, "detail"):
        detalle = getattr(exc, "detail", "Detalle no disponible")
    else:
        detalle = "Detalle no ha llegado"

    print(status_code, detalle)

    return {
        "status_code": status_code,
        "message": detalle
    }

# -----------------------------------------------------------------------------------------------
async def generic_exception_handler(request: Request, exc: Exception):
    '''
    imprime_mi_log("generic_exception_handler", exc)

        if hasattr(exc, 'detail') and exc.detail is not None and isinstance(exc.detail, dict):
            mi_mensaje = {"ret_code": exc.detail['ret_code'],
                        "ret_txt": str(exc.detail.get('ret_txt', exc.detail.get("excepcion", "Sin texto asociado"))),
                        }
            graba_log(mi_mensaje, "GenericException", exc.detail.get("excepcion", "Sin texto asociado"))
        else:
            mi_mensaje = {"ret_code": -1,
                        "ret_txt": str(exc),
                        #   "ret_txt": exc.detail,
                        }
            graba_log(mi_mensaje, "GenericException", exc)

        return JSONResponse(
            status_code=500,
            content={"codigo_error": -1, "mensaje": str(exc)},
        )
    '''    
# -----------------------------------------------------------------------------------------------
    if hasattr(exc, "status_code"):
        status_code = getattr(exc, "status_code", 500)
    else:
        status_code = 500  # Estatus predeterminado para errores genéricos

    if hasattr(exc, "detail"):
        detalle = getattr(exc, "detail", "Detalle no disponible")
    else:
        detalle = "Detalle no ha llegado"

    return {
        "status_code": status_code,
        "message": detalle
    }


# -----------------------------------------------------------------------------------------------
async def type_error_handler(request: Request, exc: TypeError):
# -----------------------------------------------------------------------------------------------
    graba_log({"Detalle:": exc,"method:": request.method, "url:": request.url}, "TypeErrorException", exc)

    return {
        "message": exc,
        "status_code": 500
    }
# -----------------------------------------------------------------------------------------------
async def json_decode_error_handler(request: Request, exc: json.JSONDecodeError):
# -----------------------------------------------------------------------------------------------
    imprime_mi_log("json_decode_error_handler", exc)


    # Ya probaremos si esto es así
    if isinstance(exc.detail, dict):
        mi_mensaje = {"ret_code": exc.detail['ret_code'],
                      "ret_txt": exc.detail.get('ret_txt', str(exc.detail["excepcion"])),
                     }
    else:
        mi_mensaje = {"ret_code": -1,
                      "ret_txt": exc.detail,
                     }

    mi_mensaje["ret_txt"] = mi_mensaje["ret_txt"].join(f"JSONDecodeError: {exc.msg} (line: {exc.lineno}, col: {exc.colno})")
    graba_log(mi_mensaje, "JSONDecodeErrorException", exc.detail["excepcion"])


    return JSONResponse(
        status_code=400,
        content={"codigo_error": -1, "mensaje": "Error decoding JSON"},
    )