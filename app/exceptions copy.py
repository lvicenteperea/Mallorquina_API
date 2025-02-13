from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import json

from app.utils.mis_excepciones import MiException
from app.utils.functions import graba_log, imprime
from app.utils.InfoTransaccion import InfoTransaccion

# -----------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------
def imprime_mi_log(tipo_excepcion, exc):
    print(f"--------------------------------------{tipo_excepcion}-----------------------------------------------")
    print("Argumentos de la excepción:", exc.args if hasattr(exc, 'args') else exc)
    print(f"--------------------------------------------------------------------------------------------------------")
    print(f"Detalle: {exc.detail if hasattr(exc, 'detail') else 'Sin detalle'}")
    print(f"Estado: {exc.status_code if hasattr(exc, 'status_code') else 'Sin estado'}")
    print(f"Encabezados: {exc.headers if hasattr(exc, 'headers') else 'Sin encabezados'}")

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
async def mi_exception_handler(param: InfoTransaccion, mensaje: str = ' Error general contacte con su administrador', codigo: int = -1):
# -----------------------------------------------------------------------------------------------
    # imprime_mi_log("mi_exception_handler2", mensaje)
    # imprime_mi_log("mi_exception_handler3", codigo)

    '''
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
    '''
    
    # graba_log(param.to_dict() | {"codigo":codigo, "Mensaje":mensaje}, "madre_exception", None)

    # return JSONResponse(
    #     status_code = codigo, 
    #     content={"codigo_error (status_code)": param.ret_code, "mensaje": param.ret_txt+mensaje},
    # )
    x =  JSONResponse(
        status_code = 524, 
        content={"codigo_error (status_code)": 523, "mensaje": "mi_mensaje de madre exception"},
    )
    print("")
    print("x para response madre:", x)
    print("")
    return x


# -----------------------------------------------------------------------------------------------
async def http_exception_handler(request: Request, exc: HTTPException):
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
    imprime_mi_log("generic_exception_handler", exc)
    
    import traceback
    # print("🔥 Error fichero:", traceback.format_exc())
    print("🔥 Error capturado:", str(exc))
    # traceback.print_exc() 

    x =  JSONResponse(
        status_code = 525, 
        content={"codigo_error (statsu_code)": 526, "mensaje": "mi_mensaje"},
    )
    print("")
    print("x para response:", x.body)
    print("")
    return x

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