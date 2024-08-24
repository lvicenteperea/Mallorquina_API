from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import json
import logging

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
async def http_exception_handler(request: Request, exc: HTTPException):
    
    logger.error(f"HTTPException: {exc.detail} (status: {exc.status_code})")

    return JSONResponse(
        status_code=exc.status_code,
        content={"codigo_error": exc.status_code, "mensaje": exc.detail, "datos": {}},
    )

async def json_decode_error_handler(request: Request, exc: json.JSONDecodeError):
    logger.error(f"JSONDecodeError: {exc.msg} (line: {exc.lineno}, col: {exc.colno})")
    return JSONResponse(
        status_code=400,
        content={"codigo_error": -1, "mensaje": "Error decoding JSON", "datos": {}},
    )

async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"codigo_error": -1, "mensaje": str(exc), "datos": {}},
    )
