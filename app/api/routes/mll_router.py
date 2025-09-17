from fastapi import APIRouter, HTTPException, Body, Request, Depends, File, UploadFile, Form, Query
from typing import List, Optional
from datetime import datetime
import os
from fastapi.responses import JSONResponse

router = APIRouter()


# Importaciones propias del proyecto
from app.services.mallorquina import (
    sincroniza, consulta_cierre, arqueo_caja, arqueo_caja_info, tarifas_ERP_a_TPV
   ,genera_fichas_tecnicas, recupera_ficha_tecnica, alergenos, carga_productos_erp
)
from app.services.auxiliares import descarga

from app.config.settings import settings
from app.utils.functions import control_usuario

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
        print([tiempo, datetime.now().strftime('%Y-%m-%d %H:%M:%S')], "* FIN TIEMPOS *")


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
class ArqueoCajaRequest(ParamRequest):
    # fecha: str  #= datetime.now().strftime('%Y-%m-%d')
    dias: int # = 1

@router.post("/mll_arqueo_caja", response_model=InfoTransaccion,
             summary="🔄 Genera la información del araqueo de caja a un día determinado en las tablas mll_rec_ventas_diarias y mll_rec_ventas_medio_pago",
             description="""Genera la información del araqueo de caja para todas las entidades que su Tiendas/BBDD que tengan cierre_caja='S'
                            También la forma de cobro debe estar activa en el TPV (activo_arqueo=1)
                            La fecha que trata es ultimo_cierre de cfg_entidades
                                - ✅ **Requiere autenticación**
                                - ✅ **Recibe un `id_App` y un `user`** para identificar al peticionario
                                - ✅ **Retorna `status` y `message` indicando error**
                         """,
             response_description="""📌 En caso de éxito retorna una clase InfoTransaccion y en resultados una lista de texto con un regsitros por:
                                    [
                                        "para el 01/02/2025 y tienda 2: se han creado 4 regsitros de venta, con un total de 99999.99€ para 999 operaciones. En Medios de pago se han creado 999 registros",
                                        "para el 01/02/2025 y tienda 7: se han creado 4 regsitros de venta, con un total de 99999.99€ para 999 operaciones. En Medios de pago se han creado 999 registros"
                                    ]
                                  """
           )
async def mll_arqueo_caja(request: Request, body_params: ArqueoCajaRequest = Body(...)):
    """ Genera información del arqueo de caja en una fecha determinada. """
    return await procesar_request(request, body_params, arqueo_caja, "mll_arqueo_caja")


#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
class InfArqueoCajaRequest(ParamRequest):
    fecha: str = datetime.now().strftime('%Y-%m-%d')
    entidad: Optional[int] = 0  # Todas las entidades

@router.post("/mll_inf_arqueo_caja", response_model=InfoTransaccion,
             summary="🔄 Busca los datos para una tienda determinada en las tablas mll_rec_ventas_diarias y mll_rec_ventas_medio_pago",
             description="""Este servicio sincroniza los datos entre diferentes BBDD como los TPV, la nube de infosoft y el servidor.\n
                                - ✅ **Requiere autenticación**
                                - ✅ **Recibe un `id_App` y un `user`** para identificar al peticionario
                                - ✅ **Retorna `status` y `message` indicando error**
                         """,
             response_description="""📌 En caso de éxito retorna una clase InfoTransaccion y en resultados una lista con los ficheros generados:\n
                                    [ "Se ha generado el fichero app/xxxxx/xxxxx/resultado_panda.xlsx correctamente.",
                                      "Se ha generado el fichero app/xxxxx/xxxxx/resultado_openpyxl.xlsx correctamente"
                                      ]
                                  """
            )
async def mll_inf_arqueo_caja(request: Request, body_params: InfArqueoCajaRequest = Body(...)):
    """ Genera archivos con resultados del arqueo de caja. """
    return await procesar_request(request, body_params, arqueo_caja_info, "mll_inf_arqueo_caja")


#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
class ConsultaCierreRequest(ParamRequest):
    fecha: str = datetime.now().strftime('%Y-%m-%d')
    entidad: Optional[int] = 0  # Por defecto, todas las entidades

@router.post("/mll_consultas_cierre", response_model=InfoTransaccion)
async def mll_consultas_cierre(request: Request, body_params: ConsultaCierreRequest = Body(...)):
    """ Retorna el cierre de un día determinado (por defecto, hoy). """
    return await procesar_request(request, body_params, consulta_cierre, "mll_consultas_cierre")


#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
@router.post("/mll_carga_prod_erp", response_model=InfoTransaccion,
             summary="🔄 Carga el fichero de productos excel del ERP SQLPYME en la BBDD de La Mallorquina",
             description="""Carga el fichero de productos excel del ERP SQLPYME en la BBDD de La Mallorquina.\n
                                - ✅ **Requiere autenticación**
                                - ✅ **Recibe un `id_App` y un `user`** para identificar al peticionario
                                - ✅ **Retorna `status` y `message` indicando error**
                         """,
             response_description="""📌 En caso de éxito retorna una clase InfoTransaccion y en resultados una lista con los ficheros generados:\n
                                  """
            )
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
        print([tiempo, datetime.now().strftime('%Y-%m-%d %H:%M:%S')], "* FIN TIEMPOS *")


#------------------------------------------------------------------------------------------------------
# ALERGENMOS, FICHAS TÉCNICAS
#------------------------------------------------------------------------------------------------------
class FichaTecnicaRequest(ParamRequest):
    id_producto: int

class FichasTecnicasRequest(ParamRequest):
    output_path: str = "alergenos.html"
    punto_venta: Optional[int] = 0  # Por defecto, todos los punto_venta
    generar_ficheros: str = "N"

@router.post("/mll_recupera_ficha_tecnica", response_model=InfoTransaccion)
async def mll_recupera_ficha_tecnica(request: Request, body_params: FichaTecnicaRequest = Body(...)):
    """ Retorna el HTML de una ficha técnica concreta. """
    return await procesar_request(request, body_params, recupera_ficha_tecnica, "mll_recupera_ficha_tecnica")

@router.post("/mll_genera_fichas_tecnicas", response_model=InfoTransaccion)
async def mll_genera_fichas_tecnicas(request: Request, body_params: FichasTecnicasRequest = Body(...)):
    """ Genera fichas técnicas y listado de alérgenos. """
    return await procesar_request(request, body_params, genera_fichas_tecnicas, "mll_genera_fichas_tecnicas")

@router.post("/mll_alergenos", response_model=InfoTransaccion)
async def mll_alergenos(request: Request, body_params: FichasTecnicasRequest = Body(...)):
    """ Retorna un html con los agergenos del punto de venta. """
    return await procesar_request(request, body_params, alergenos, "mll_alergenos")



#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
class ConvierteTarifasRequest(ParamRequest):
    codigos: List[int] = []
    
@router.post("/mll_convierte_tarifas", response_model=InfoTransaccion)
async def mll_convierte_tarifas(request: Request, body_params: ConvierteTarifasRequest = Body(...)):
    """ Genera tarifas para los TPVs de Infosoft. """
    return await procesar_request(request, body_params, tarifas_ERP_a_TPV, "mll_convierte_tarifas")

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
        print([type(body_params.nombres), len(body_params.nombres), body_params.nombres], "*")
        param = InfoTransaccion.from_request(body_params)

        control_usuario (param,  request)

        # --------------------------------------------------------------------------------
        # Servicio
        # --------------------------------------------------------------------------------
        return descarga.proceso(param=param)

    except Exception as e:
        manejar_excepciones(e, param, "mll_descarga")

    finally:
        print([tiempo, datetime.now().strftime('%Y-%m-%d %H:%M:%S')], "* FIN TIEMPOS *")


#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
# Ruta a los logs (ajusta según tu entorno con una variable de entorno o config)
LOGS_DIR = os.getenv('LOGS_DIR', './logs')

@router.get("/leer_log")
def leer_log(
    archivo: str = Query(..., description="Nombre del archivo de log"),
    desde: int = Query(1, ge=1, description="Línea inicial (opcional, por defecto 1)"),
    hasta: int = Query(None, description="Línea final (opcional, por defecto hasta el final)"),
):
    # Seguridad: Solo permitimos ciertos logs
    archivos_permitidos = {"app.log", "time.log"}
    if archivo not in archivos_permitidos:
        raise HTTPException(status_code=400, detail="Archivo de log no permitido")

    log_path = os.path.join(LOGS_DIR, archivo)
    if not os.path.isfile(log_path):
        raise HTTPException(status_code=404, detail="Archivo de log no encontrado")

    with open(log_path, encoding="utf-8") as f:
        lineas = f.readlines()

    total_lineas = len(lineas)
    desde = max(1, desde)
    hasta = hasta or total_lineas

    if desde > hasta or desde > total_lineas:
        return JSONResponse(content={"lineas": [], "total": total_lineas})

    # Cortamos y mostramos en orden descendente
    lineas_seleccionadas = lineas[desde-1:hasta][::-1]
    return {
        "lineas": [l.rstrip('\n\r') for l in lineas_seleccionadas],
        "total": total_lineas,
        "desde": desde,
        "hasta": hasta
    }
