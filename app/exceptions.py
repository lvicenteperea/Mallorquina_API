from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import json
import traceback
from datetime import datetime

from app.utils.mis_excepciones import MiException
from app.utils.InfoTransaccion import InfoTransaccion
from app.utils.utilidades import graba_log

# ---------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------
async def mi_exception_handler(request: Request, exc: MiException):
    if exc.status_code >= 0: 
        status_code = 200
        mensaje = exc.detail
    elif exc.status_code > -90: # -1, -2.... no son errores graves de cortar el programa
        status_code = 401
        mensaje = exc.detail
    else:                       # -90.... no deberían salir por aquí, pero serían para cortar el programa.
        status_code = 525
        mensaje = "Contacte con su administrador"
    
    return JSONResponse(
        status_code=status_code,
        content={"status_code": exc.status_code, "message": mensaje}
    )

# ---------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------
async def generic_exception_handler(request: Request, exc: Exception):
    loc = "no disponible"

    # ---------------------------------------------------------------------------------------------------------------------------
    param = InfoTransaccion(id_App=1, user="Vamos a ver1", ret_code=-1, ret_txt=str(exc), parametros=[])

    if isinstance(exc, BaseException): # Comprueba si es una excepción
        tb = traceback.extract_tb(exc.__traceback__)
        archivo, linea, funcion, texto_err = tb[-1]
        loc = f'{texto_err.replace("-", "_")} - {archivo.replace("-", "_")} - {linea} - {funcion}'

    graba_log(param, f"generic_exception_handler: {loc}", exc)
    # ---------------------------------------------------------------------------------------------------------------------------

    return JSONResponse(
        status_code=500,
        content={"status_code": 500, 
                 "message": f"Error general. contacte con su administrador ({datetime.now().strftime('%Y%m%d%H%M%S')})"
                }
    )

# ---------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------
async def http_exception_handler(request: Request, exc: HTTPException):
    loc = "no disponible"

    # ---------------------------------------------------------------------------------------------------------------------------
    param = InfoTransaccion(id_App=1, user="Vamos a ver", ret_code=-1, ret_txt="pues el RET_TXT", parametros=[])

    if isinstance(exc, BaseException): # Comprueba si es una excepción
        tb = traceback.extract_tb(exc.__traceback__)
        archivo, linea, funcion, texto_err = tb[-1]
        loc = f'{texto_err.replace("-", "_")} - {archivo.replace("-", "_")} - {linea} - {funcion}'

    graba_log(param, f"{funcion}.http_exception_handler", exc)

    # ---------------------------------------------------------------------------------------------------------------------------

    return JSONResponse(
        status_code=exc.status_code,
        content={"status_code": exc.status_code, 
                 "message": f"Error general. contacte con su administrador ({datetime.now().strftime('%Y%m%d%H%M%S')})"
                }
    )

# ---------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------
async def json_decode_error_handler(request: Request, exc: json.JSONDecodeError):
    return JSONResponse(
        status_code=400,
        content={"status_code": 400, "message": "Error al decodificar JSON"}
    )

# ---------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------
async def type_error_handler(request: Request, exc: TypeError):
    return JSONResponse(
        status_code=422,
        content={"status_code": 422, "message": "Error de tipo en la solicitud"}
    )
