from fastapi import APIRouter, HTTPException, Body, Request, Depends, File, UploadFile, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os

from app.external_services.equinsa.servicios_equinsa import EquinsaService

# Importaciones propias del proyecto
from app.services.mallorquina import (
    sincroniza, carga_productos_erp
)

from app.config.settings import settings
from app.utils.functions import control_usuario
from app.utils.utilidades import imprime

from app.utils.mis_excepciones import MiException
from app.utils.InfoTransaccion import InfoTransaccion, ParamRequest

router = APIRouter()

# -----------------------------------------------
# Función para manejar excepciones de manera estándar
# -----------------------------------------------
def manejar_excepciones(e: Exception, param: InfoTransaccion, endpoint: str):
    if isinstance(e, MiException):
        return None
    elif isinstance(e, HTTPException):
        param.error_sistema(e=e, debug=f"{endpoint}.HTTP_Exception")
        raise e
    else:
        param.error_sistema(e=e, debug=f"{endpoint}.Exception")
        raise e


# -----------------------------------------------
# Función común para procesar requests
# -----------------------------------------------
async def procesar_request(
    request: Request, body_params: ParamRequest, servicio, endpoint: str
) -> InfoTransaccion:
    tiempo = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        # Validación y construcción de parámetros
        param = InfoTransaccion.from_request(body_params)
        if not control_usuario(param, request):
            return param

        # Ejecución del servicio correspondiente
        resultado = servicio.proceso(param=param)

        # Construcción de respuesta
        param.debug = f"Retornando: {type(resultado)}"
        param.resultados = resultado or []
        return param


    except Exception as e:
        manejar_excepciones(e, param, endpoint)
        return param  # si no es MiException, se retorna el param
    
    finally:
        imprime([tiempo, datetime.now().strftime('%Y-%m-%d %H:%M:%S')], "* FIN TIEMPOS *")


# -----------------------------------------------
# Endpoints optimizados
# -----------------------------------------------
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
class SincronizaRequest(ParamRequest):
    tiendas: Optional[List] = None  # Si es None, asumimos todas

@router.post("/mll_sincroniza", response_model=InfoTransaccion,
             summary="🔄 Sincroniza datos con el sistema dependiente de la parametrización en trabla mll_cfg_*",
             description="""Este servicio sincroniza los datos entre diferentes BBDD como los TPV, la nube de infosoft y el servidor.\n
                                - ✅ **Requiere autenticación**
                                - ✅ **Recibe un `id_App` y un `user`** para identificar al peticionario
                                - ✅ **Retorna `status` y `message` indicando error**
                         """,
             response_description="""📌 En caso de éxito retorna una clase InfoTransaccion y en resultados una lista json con cada BBDD/entidad/tabla tratada, tipo:\n
                                    {
                                        "nombre_bbdd": "Tienda Velázquez",
                                        "entidad": "Tienda - Velázquez",
                                        "tabla_origen": "[Mesas Restaurante]",
                                        "valor_max": null,
                                        "insertados": 0,
                                        "actualizados": 0,
                                        "error": null     ## Si no hay error, se retorna None y si retorna mensaje cuando no hay conexión a la BBDD
                                    }
                                  """
            )
async def mll_sincroniza(request: Request, body_params: SincronizaRequest = Body(...)):
    """ Sincroniza datos entre diferentes BBDD (TPV, nube,..) y servidor. """
    return await procesar_request(request, body_params, sincroniza, "mll_sincroniza")


#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
@router.post("/apk_consultas", response_model=InfoTransaccion,
             summary="🔄 Crealiza consultas sobre un aparcamiento de equinsa",
             description="""........................................\n
                                - ✅ **Requiere autenticación**
                                - ✅ **Recibe un `id_App` y un `user`** para identificar al peticionario
                                - ✅ **Retorna `status` y `message` indicando error**
                         """,
             response_description="""📌 En caso de éxito retorna una clase InfoTransaccion y en resultados una lista con los ficheros generados:\n
                                  """
            )
async def apk_consultas(request: Request,
                        body_params: ParamRequest = Body(...)
):

    tiempo = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        # --------------------------------------------------------------------------------
        # Validaciones y construcción Básica
        # --------------------------------------------------------------------------------
        param = InfoTransaccion.from_request(body_params)

        # control_usuario (param,  request)

        # --------------------------------------------------------------------------------
        # Servicio
        # --------------------------------------------------------------------------------
        equinsa = EquinsaService(carpark_id="1237")

        # Ejecutar una consulta SQL
        sql_query = "SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'"
        sql_query = "SELECT * FROM ope"
        resultado = equinsa.execute_sql_command(sql_query)

        # Imprimir la respuesta
        imprime([type(resultado),resultado], '*   Mi primera select', 2)

        param.debug = f"Retornando un lista: {type(resultado)}"
        param.resultados = resultado or []
        return param

    except Exception as e:
        # manejar_excepciones(e, param, "apk_consultas")
        imprime(["Mensaje de error", e], "=")

    finally:
        imprime([tiempo, datetime.now().strftime('%Y-%m-%d %H:%M:%S')], "* FIN TIEMPOS *")

