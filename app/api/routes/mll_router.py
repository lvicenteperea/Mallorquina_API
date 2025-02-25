from fastapi import APIRouter, HTTPException, Body, Request, Depends, File, UploadFile, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os

# Importaciones propias del proyecto
from app.services.mallorquina import (
    sincroniza, consulta_caja, arqueo_caja, arqueo_caja_info, tarifas_ERP_a_TPV, fichas_tecnicas, carga_productos_erp
)
from app.services.auxiliares import descarga
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
                                        "actualizados": 0
                                    }
                                  """
            )
async def mll_sincroniza(request: Request, body_params: SincronizaRequest = Body(...)):
    """ Sincroniza datos entre diferentes BBDD (TPV, nube,..) y servidor. """
    return await procesar_request(request, body_params, sincroniza, "mll_sincroniza")

#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
class ConsultaCierreRequest(ParamRequest):
    fecha: str = datetime.now().strftime('%Y-%m-%d')
    tienda: Optional[int] = 0  # Por defecto, todas las tiendas

@router.post("/mll_consultas_cierre", response_model=InfoTransaccion)
async def mll_consultas_cierre(request: Request, body_params: ConsultaCierreRequest = Body(...)):
    """ Retorna el cierre de un día determinado (por defecto, hoy). """
    return await procesar_request(request, body_params, consulta_caja, "mll_consultas_cierre")


#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
class ArqueoCajaRequest(ParamRequest):
    # fecha: str  #= datetime.now().strftime('%Y-%m-%d')
    dias: int # = 1

@router.post("/mll_arqueo_caja", response_model=InfoTransaccion)
async def mll_arqueo_caja(request: Request, body_params: ArqueoCajaRequest = Body(...)):
    """ Genera información del arqueo de caja en una fecha determinada. """
    return await procesar_request(request, body_params, arqueo_caja, "mll_arqueo_caja")


#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
class InfArqueoCajaRequest(ParamRequest):
    fecha: str = datetime.now().strftime('%Y-%m-%d')
    tienda: Optional[int] = 0  # Todas las tiendas

@router.post("/mll_inf_arqueo_caja", response_model=InfoTransaccion)
async def mll_inf_arqueo_caja(request: Request, body_params: InfArqueoCajaRequest = Body(...)):
    """ Genera archivos con resultados del arqueo de caja. """
    return await procesar_request(request, body_params, arqueo_caja_info, "mll_inf_arqueo_caja")


#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
@router.post("/mll_carga_prod_erp", response_model=InfoTransaccion)
async def mll_carga_prod_erp(
    request: Request,
    id_App: int = Form(...),
    user: str = Form(...),
    ret_code: int = Form(...),
    ret_txt: str = Form(...),
    file: UploadFile = File(...),
):
    """ Carga un archivo de productos del ERP SQLPYME en la BBDD de La Mallorquina. """
    tiempo = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        fichero = file.filename
        param = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, parametros=[fichero])

        # Guardar archivo
        excel_path = os.path.join(f"{settings.RUTA_DATOS}/erp", fichero)
        with open(excel_path, "wb") as f:
            f.write(await file.read())

        control_usuario(param, request)

        resultado = carga_productos_erp.proceso(param=param)
        param.debug = f"Retornando un lista: {type(resultado)}"
        param.resultados = resultado or []
        return param

    except Exception as e:
        manejar_excepciones(e, param, "mll_carga_prod_erp")

    finally:
        imprime([tiempo, datetime.now().strftime('%Y-%m-%d %H:%M:%S')], "* FIN TIEMPOS *")


#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
class DescargaRequest(ParamRequest):
    tipo: str = "TPV"
    nombres: List[str] = []

@router.post("/mll_descarga", # response_model=InfoTransaccion,
             summary="🔄 Genera las fichas técnicas y listado de alergenos",
             description="""Genera las fichas técnicas de los productos y el listado de alergenos
                                - ✅ **Requiere autenticación**
                                - ✅ **Recibe un `id_App` y un `user`** para identificar al peticionario
                                - ✅ **Retorna `status` y `message` indicando error**
                         """,
             response_description="""📌 En caso de éxito retorna una clase InfoTransaccion y en resultados una lista de textos con un regsitros por fichero generado:
                                    ["Ficheros generados correctamente"]
                                  """
           )
async def mll_descarga(request: Request,
                       body_params: DescargaRequest = Body(...)
                      ):

    tiempo = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        # --------------------------------------------------------------------------------
        # Validaciones y construcción Básica
        # --------------------------------------------------------------------------------
        imprime([type(body_params.nombres), len(body_params.nombres), body_params.nombres], "*")
        param = InfoTransaccion.from_request(body_params)

        control_usuario (param,  request)

        # --------------------------------------------------------------------------------
        # Servicio
        # --------------------------------------------------------------------------------
        return descarga.proceso(param=param)
        # resultado = descarga.proceso(param=param)

        # param.debug = f"Retornando: {type(resultado)}"
        # param.resultados = resultado or []
        # print("3")

        # return param


    except Exception as e:
        manejar_excepciones(e, param, "mll_descarga")

    finally:
        imprime([tiempo, datetime.now().strftime('%Y-%m-%d %H:%M:%S')], "* FIN TIEMPOS *")

#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
class FichasTecnicasRequest(ParamRequest):
    output_path: str = "fichas_tecnicas.html"

@router.post("/mll_fichas_tecnicas", response_model=InfoTransaccion)
async def mll_fichas_tecnicas(request: Request, body_params: FichasTecnicasRequest = Body(...)):
    """ Genera fichas técnicas y listado de alérgenos. """
    return await procesar_request(request, body_params, fichas_tecnicas, "mll_fichas_tecnicas")


#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
@router.post("/mll_convierte_tarifas", response_model=InfoTransaccion)
async def mll_convierte_tarifas(request: Request, body_params: ParamRequest = Body(...)):
    """ Genera tarifas para los TPVs de Infosoft. """
    return await procesar_request(request, body_params, tarifas_ERP_a_TPV, "mll_convierte_tarifas")
