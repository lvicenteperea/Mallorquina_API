from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import json
import logging

from app.utils.mis_excepciones import MadreException

# -----------------------------------------------------------------------------------------------
# LOGGING

# # esto sería con fichero de inicialización
# try:
#     logging.config.fileConfig('app/logging.ini')
# except Exception as e:
#     print(f"Error configuring logging: {e}")
# 
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

logger = logging.getLogger('app_logger')
 
# esto sería con basicConfig
logging.basicConfig(
    level=logging.DEBUG,  # Configura el nivel de logging
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Formato del log
    handlers=[
        logging.FileHandler("app/logs/app.log"),  # Guarda los logs en un archivo
        logging.StreamHandler()  # También muestra los logs en la consola
    ]
)
 
logger.info("Inicio de la ejecución")


# -----------------------------------------------------------------------------------------------
# EXCEPTION HANDLERS
# -----------------------------------------------------------------------------------------------
async def madre_exception_handler(request: Request, exc: MadreException):
# -----------------------------------------------------------------------------------------------
    print("madre_exception_handler")
    logger.error(f"MadreException: (status: {exc.status_code} {exc.mi_mensaje})")
    
    if isinstance(exc.mi_mensaje, dict):
        mi_mensaje = exc.mi_mensaje
    else:
        mi_mensaje = {"ret_code": -1,
                      "ret_txt": exc.mi_mensaje,
                     }

    return JSONResponse(
        status_code=exc.status_code,
        content={"codigo_error": exc.status_code, "mensaje": mi_mensaje},
    )

# -----------------------------------------------------------------------------------------------
async def http_exception_handler(request: Request, exc: HTTPException):
# -----------------------------------------------------------------------------------------------
    print("http_exception_handler")
    if isinstance(exc.detail, dict):
        mi_mensaje = exc.detail
    else:
        mi_mensaje = {"ret_code": -1,
                      "ret_txt": exc.detail,
                     }

    logger.error(f"HTTPException: {exc.detail} (status: {mi_mensaje})")

    return JSONResponse(
        status_code=exc.status_code,
        content={"codigo_error": exc.status_code, "mensaje": mi_mensaje},
    )

# -----------------------------------------------------------------------------------------------
async def json_decode_error_handler(request: Request, exc: json.JSONDecodeError):
# -----------------------------------------------------------------------------------------------
    print("json_decode_error_handler")
    logger.error(f"JSONDecodeError: {exc.msg} (line: {exc.lineno}, col: {exc.colno})")
    return JSONResponse(
        status_code=400,
        content={"codigo_error": -1, "mensaje": "Error decoding JSON", "datos": {}},
    )

# -----------------------------------------------------------------------------------------------
async def generic_exception_handler(request: Request, exc: Exception):
# -----------------------------------------------------------------------------------------------
    print("generic_exception_handler")
    logger.error(f"Unhandled Exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"codigo_error": -1, "mensaje": str(exc), "datos": {}},
    )


# -----------------------------------------------------------------------------------------------
async def type_error_handler(request: Request, exc: TypeError):
# -----------------------------------------------------------------------------------------------
    print("type_error_handler")
    return JSONResponse(
        status_code=400,
        content={"codigo_error": -1, "mensaje": "Type error in processing JSON data", "datos": {}},
    )