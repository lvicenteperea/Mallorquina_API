ANTES DE PASARLO POR CHATGPT


from fastapi.responses import FileResponse
from fastapi import APIRouter, HTTPException, Query, Body, Depends
from fastapi import File, UploadFile, Form
from starlette.requests import Request
from datetime import datetime
# from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel
from typing import List, Optional
import os


# mias
import app.services.mallorquina.sincroniza as sincroniza
import app.services.mallorquina.consulta_caja as consulta_caja
import app.services.mallorquina.arqueo_caja as arqueo_caja
import app.services.mallorquina.arqueo_caja_info as arqueo_caja_info
import app.services.mallorquina.tarifas_ERP_a_TPV as tarifas_ERP_a_TPV  # tarifas_a_TPV as tarifas_a_TPV
import app.services.mallorquina.fichas_tecnicas as fichas_tecnicas
import app.services.mallorquina.carga_productos_erp as carga_productos_erp
# import app.services.mallorquina.encargos_navidad as encargos_navidad
import app.services.auxiliares.descarga as descarga

from app.config.settings import settings

from app.utils.functions import control_usuario
from app.utils.utilidades import graba_log, imprime
from app.utils.mis_excepciones import MiException
from app.utils.InfoTransaccion import InfoTransaccion, ParamRequest

# Definimos el router
router = APIRouter()

#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
class SincronizaRequest(ParamRequest):
    tiendas: Optional[List] = 0   # Tienda de la que queremos sacar la información
    
@router.post("/mll_sincroniza", response_model=InfoTransaccion,
             summary="🔄 Sincroniza datos con el sistema dependiente de la parametrización en trabla mll_cfg_*",
             description="""Este servicio sincroniza los datos entre diferentes BBDD como los TPV, la nube de infosoft y el servidor.
                                - ✅ **Requiere autenticación**
                                - ✅ **Recibe un `id_App` y un `user`** para identificar al peticionario
                                - ✅ **Retorna `status` y `message` indicando error**
                         """,
             response_description="""📌 En caso de éxito retorna una clase InfoTransaccion y en resultados una lista json con cada BBDD/entidad/tabla tratada, tipo:
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
@router.get("/mll_sincroniza", response_model=InfoTransaccion)
async def mll_sincroniza(request: Request,  # Para acceder a request.state.user
                         body_params: SincronizaRequest = Body(...)
                        ):
    tiempo = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        # --------------------------------------------------------------------------------
        param = InfoTransaccion.from_request(body_params)

        # --------------------------------------------------------------------------------
        # Validaciones y construcción Básica
        # --------------------------------------------------------------------------------
        control_usuario (param,  request)

        # --------------------------------------------------------------------------------
        # Servicio
        # --------------------------------------------------------------------------------
        resultado = sincroniza.proceso(param = param)
        # --------------------------------------------------------------------------------

        param.debug = f"Retornando: {type(resultado)}"
        param.resultados = resultado or []

        return param
   

    except MiException as e:
        print("---------------- MiException ---------------------")
        raise e
    except HTTPException as e:
        param.error_sistema(e=e, debug="mll_sincroniza.HTTP_Exception")
        raise e
    except Exception as e:
        param.error_sistema(e=e, debug="mll_sincroniza.Exception")
        raise e

    finally:
        imprime([tiempo, datetime.now().strftime('%Y-%m-%d %H:%M:%S')], "*  FIN TIEMPOS  ")


#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
class ConsultaCierreRequest(ParamRequest):
    fecha: str    # Dia de cierre que se necesita en formato 'YYYY-MM-DD', por defecto la actual
    tienda: Optional[int] = 0   # Tienda de la que queremos sacar la información
    
@router.post("/mll_consultas_cierre", response_model=InfoTransaccion,
             summary="🔄 Retorna el ciere a un día determinado, por defecto hoy",
             description="""Retorna el ciere a un día determinado, por defecto hoy
                                - ✅ **Requiere autenticación**
                                - ✅ **Recibe un `id_App` y un `user`** para identificar al peticionario
                                - ✅ **Retorna `status` y `message` indicando error**
                         """,
             response_description="""📌 En caso de éxito retorna una clase InfoTransaccion y en resultados una lista json con un regsitros por:
                                     {
                                        "ID_Apertura": 8285,
                                        "Fecha_Hora": "2024-10-05T14:07:20",
                                        "ID_Cobro": 3,
                                        "Medio_Cobro": "TRANSFERENCIA",
                                        "Importe": "0.000",
                                        "Realizado": true,
                                        "ID_Relacion": 39146,
                                        "ID_Puesto": 1,
                                        "Puesto_Facturacion": "SERVIDOR TIENDA",
                                        "Nombre_BBDD": "LMVELAZQUEZ",
                                        "ID_BBDD": 2,
                                        "stIdEnt": "2202232042133764"
                                     }
                                  """
           )
async def mll_consultas_cierre( request: Request,  # Para acceder a request.state.user
                                body_params: ConsultaCierreRequest = Body(...),
                               ):
    tiempo = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        # --------------------------------------------------------------------------------
        # Validaciones y construcción Básica
        # --------------------------------------------------------------------------------
        # Si no se proporciona `fecha`, usar la actual
        if not body_params.fecha:
            body_params.fecha = datetime.now().strftime('%Y-%m-%d')

        if not body_params.tienda:
            body_params.tienda = 0

        param = InfoTransaccion.from_request(body_params)

        control_usuario (param,  request)

        # --------------------------------------------------------------------------------
        # Servicio
        # --------------------------------------------------------------------------------
        resultado = consulta_caja.recorre_consultas_tiendas(param=param)

        param.debug = f"Retornando: {type(resultado)}"
        param.resultados = resultado or []

        return param

    except MiException as e:
        print("---------------- MiException ---------------------")
        raise e
    except HTTPException as e:
        param.error_sistema(e=e, debug="mll_consultas_cierre.HTTP_Exception")
        raise e
    except Exception as e:
        param.error_sistema(e=e, debug="mll_consultas_cierre.Exception")
        raise e

    finally:
        imprime([tiempo, datetime.now().strftime('%Y-%m-%d %H:%M:%S')], "*  FIN TIEMPOS  ")


#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
class ArqueoCajaRequest(ParamRequest):
    fecha: str    # Fecha de la solicitud en formato 'YYYY-MM-DD'

@router.post("/mll_arqueo_caja", response_model=InfoTransaccion,
             summary="🔄 Genera la información del araqueo de caja a un día determinado",
             description="""Genera la información del araqueo de caja a un día determinado, si no se envia fecha toma por defecto la actual
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
async def mll_arqueo_caja(  request: Request,  # Para acceder a request.state.user
                            body_params: ArqueoCajaRequest = Body(...),
                         ):
    tiempo = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        # --------------------------------------------------------------------------------
        # Validaciones y construcción Básica
        # --------------------------------------------------------------------------------
        # Si no se proporciona `fecha`, usar la actual
        if not body_params.fecha:
            body_params.fecha = datetime.now().strftime('%Y-%m-%d')

        param = InfoTransaccion.from_request(body_params)

        control_usuario (param,  request)

        # --------------------------------------------------------------------------------
        # Servicio
        # --------------------------------------------------------------------------------
        resultado = arqueo_caja.proceso(param = param)
        
        param.debug = f"Retornando: {type(resultado)}"
        param.resultados = resultado or []
        param.ret_txt = "OK"

        return param

    except MiException as e:
        print("---------------- MiException ---------------------")
        raise e
    except HTTPException as e:
        param.error_sistema(e=e, debug="mll_consultas_cierre.HTTP_Exception")
        raise e
    except Exception as e:
        param.error_sistema(e=e, debug="mll_consultas_cierre.Exception")
        raise e

    finally:
        imprime([tiempo, datetime.now().strftime('%Y-%m-%d %H:%M:%S')], "*  FIN TIEMPOS  ")


#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
class InfArqueoCajaRequest(ParamRequest):
    fecha: str    # Fecha de la solicitud en formato 'YYYY-MM-DD', por defecto la actual
    tienda: Optional[int] = 0   # BBDD/Tienda (mll_cfg_bbdd) de la que queremos la información, 0 --> Todas

@router.get("/mll_inf_arqueo_caja", response_model=InfoTransaccion,
             summary="🔄 genera dos ficheros con el resultado del arqueo de caja",
             description="""genera dos ficheros con el resultado del arqueo de caja y retorna su ruta
                                - ✅ **Requiere autenticación**
                                - ✅ **Recibe un `id_App` y un `user`** para identificar al peticionario
                                - ✅ **Retorna `status` y `message` indicando error**
                         """,
             response_description="""📌 En caso de éxito retorna una clase InfoTransaccion y en resultados una lista de texto con un regsitros por fichero generado:
                                    [
                                        "Se ha generado el fichero app/xxxxxx/xxxxxx/xxxxxx/resultado_panda.xlsx correctamente.",
                                        "Se ha generado el fichero app/xxxxxx/xxxxxx/xxxxxx/resultado_openpyxl.xlsx correctamente"
                                    ]
                                  """
           )
async def mll_inf_arqueo_caja( request: Request,  # Para acceder a request.state.user
                               body_params: InfArqueoCajaRequest = Body(...),
                             ):

    tiempo = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        # --------------------------------------------------------------------------------
        # Validaciones y construcción Básica
        # --------------------------------------------------------------------------------
        # Si no se proporciona `fecha`, usar la actual
        if not body_params.fecha: # si no tiene parametro fecha
            body_params.fecha = datetime.now().strftime('%Y-%m-%d')

        param = InfoTransaccion.from_request(body_params)

        control_usuario (param,  request)

        # --------------------------------------------------------------------------------
        # Servicio
        # --------------------------------------------------------------------------------
        resultado = arqueo_caja_info.informe(param = param)
                
        param.debug = f"Retornando: {type(resultado)}"
        param.resultados = resultado or []

        return param

    except MiException as e:
        print("---------------- MiException ---------------------")
        raise e
    except HTTPException as e:
        param.error_sistema(e=e, debug="mll_inf_arqueo_caja.HTTP_Exception")
        raise e
    except Exception as e:
        param.error_sistema(e=e, debug="mll_inf_arqueo_caja.Exception")
        raise e

    finally:
        imprime([tiempo, datetime.now().strftime('%Y-%m-%d %H:%M:%S')], "*  FIN TIEMPOS  ")

#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
# class CargaProdERPRequest(ParamRequest):
#     file: UploadFile = None # File(..., description="Archivo subido por el usuario")

# class CargaProdERP(ParamRequest):
#     fichero: str =  None      # Nombre del archivo subido por el usuario

@router.post("/mll_carga_prod_erp", response_model=InfoTransaccion,
             summary="🔄 Carga el fichero de productos del ERP SQLPYME en la BBDD de La Mallorquina",
             description="""Carga el fichero de productos del ERP SQLPYME en la BBDD de La Mallorquina
                                - ✅ **Requiere autenticación**
                                - ✅ **Recibe un `id_App` y un `user`** para identificar al peticionario
                                - ✅ **Retorna `status` y `message` indicando error**
                         """,
             response_description="""📌 En caso de éxito retorna una clase InfoTransaccion y en resultados una lista de texto con un regsitros por fichero generado:
                                    [
                                        Carga exitosa: OK - Registros insertados: 999,Registros modificados: 999,Registros eliminados: 999
                                    ]
                                  """
           )
# async def mll_carga_prod_erp(request: Request,  # Para acceder a request.state.user
#                              body_params: CargaProdERPRequest = Body(...)
#                             ):
async def mll_carga_prod_erp(request: Request,  # Para acceder a request.state.user
                             id_App: int = Form(...),
                             user: str = Form(...),
                             ret_code: int = Form(...),
                             ret_txt: str = Form(...),
                             file: UploadFile = File(...)
                            ):


    tiempo = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        # --------------------------------------------------------------------------------
        # Validaciones y construcción Básica
        # --------------------------------------------------------------------------------
        fichero = file.filename
        param = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, parametros=[fichero])
        param.debug = f"infoTrans: {id_App} - {user} - {ret_code} - {ret_txt} - {fichero}"

        # Guardar el archivo subido en el servidor
        excel = os.path.join(f"{settings.RUTA_DATOS}/erp", f"{fichero}")
        with open(excel, "wb") as f:
            f.write(await file.read())

        control_usuario (param,  request)

        # --------------------------------------------------------------------------------
        # Servicio
        # --------------------------------------------------------------------------------
        resultado = carga_productos_erp.proceso(param = param)

        param.debug = f"Retornando un lista: {type(resultado)}"
        param.resultados = resultado or []

        return param

    except MiException as e:
        print("---------------- MiException ---------------------")
        print(param_aux)
        raise e
    except HTTPException as e:
        print("---------------- HTTPException ---------------------")
        print(param_aux)
        param.error_sistema(e=e, debug="mll_carga_prod_erp.HTTP_Exception")
        raise e
    except Exception as e:
        print("---------------- Exception ---------------------")
        print(param_aux)
        param.error_sistema(e=e, debug="mll_carga_prod_erp.Exception")
        raise e

    finally:
        imprime([tiempo, datetime.now().strftime('%Y-%m-%d %H:%M:%S')], "*  FIN TIEMPOS  ")


#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
# @router.get("/mll_carga_prod_erp_2", response_model=InfoTransaccion)
# async def mll_carga_prod_erp2(request: Request,  # Para acceder a request.state.user,
#                              id_App: int = Query(..., description="Identificador de la aplicación"),
#                              user: str = Query(..., description="Nombre del usuario que realiza la solicitud"),
#                              ret_code: int = Query(..., description="Código de retorno inicial"),
#                              ret_txt: str = Query(..., description="Texto descriptivo del estado inicial"),
#                              origen_path: str = Query(..., description="Fichero origen"),
#                             ):
    
#     try:
#         resultado = []
#         param = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, 
#                                 parametros=[origen_path],
#                                 debug = f"infoTrans: {id_App} - {user} - {ret_code} - {ret_txt} - {origen_path}")

#         # --------------------------------------------------------------------------------
#         resultado = carga_productos_erp.proceso(param = param)
#         # --------------------------------------------------------------------------------

#         param.debug = f"Retornando un lista: {type(resultado)}"
#         param.resultados = resultado or []
    
#     except MiException as e:
#         graba_log(param, "mll_carga_prod_erp.MiException", e)
                
#     except HTTPException as e:
#         param.error_sistema(e=e, debug="mll_carga_prod_erp.HTTPException")


#     except Exception as e:
#         param.error_sistema(e=e, debug="mll_fichas_tecnicas.Exception")

#     finally:
#         return param



#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
class FichasTecnicasRequest(ParamRequest):
    output_path: str =  None      # Fichero destino"

@router.get("/mll_fichas_tecnicas", response_model=InfoTransaccion,
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
async def mll_fichas_tecnicas(request: Request,  # Para acceder a request.state.user
                              body_params: FichasTecnicasRequest = Body(...)
                             ):
    
    try:
        # --------------------------------------------------------------------------------
        param = InfoTransaccion.from_request(body_params)
        tiempo = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # --------------------------------------------------------------------------------
        # Validaciones y construcción Básica
        # --------------------------------------------------------------------------------
        if not body_params.output_path:
            body_params.output_path = "fichas_tecnicas.html"

        control_usuario (param,  request)

        # --------------------------------------------------------------------------------
        # Servicio
        # --------------------------------------------------------------------------------
        resultado = fichas_tecnicas.proceso(param = param)

        param.debug = f"Retornando un lista: {type(resultado)}"
        param.resultados = resultado or []

        imprime([tiempo, datetime.now().strftime('%Y-%m-%d %H:%M:%S')], "*  FIN TIEMPOS  ")
        return param
    
    except MiException as e:
        graba_log(param, "mll_fichas_tecnicas.MiException", e)
                
    # except HTTPException as e:
    #     param.error_sistema(e=e, debug="mll_fichas_tecnicas.HTTPException")

    except Exception as e:
        param.error_sistema(e=e, debug="mll_fichas_tecnicas.Exception")

#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
@router.post("/mll_convierte_tarifas", response_model=InfoTransaccion,
             summary="🔄 Genera las tarifas para cada uno de los TPVs de Infosoft",
             description="""Genera las tarifas para cada uno de los TPVs de Infosoft. genera un fichero por TPV
                                - ✅ **Requiere autenticación**
                                - ✅ **Recibe un `id_App` y un `user`** para identificar al peticionario
                                - ✅ **Retorna `status` y `message` indicando error**
                         """,
             response_description="""📌 En caso de éxito retorna una clase InfoTransaccion y en resultados una lista de textos con un regsitros por fichero generado:
                                    [
                                        {
                                        "fichero": "Nombre fichero.xlsx",
                                        "texto": "Sol: 999 precios de 999"
                                        },
                                        .....
                                    ]
                                  """
           )
async def mll_convierte_tarifas(request: Request,  # Para acceder a request.state.user
                                body_params: ParamRequest = Body(...)
                               ):
    
    tiempo = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        # --------------------------------------------------------------------------------
        # Validaciones y construcción Básica
        # --------------------------------------------------------------------------------
        param = InfoTransaccion.from_request(body_params)
        

        control_usuario (param,  request)

        # --------------------------------------------------------------------------------
        # Servicio
        # --------------------------------------------------------------------------------
        resultado = tarifas_ERP_a_TPV.proceso(param = param)

        param.debug = f"Retornando un lista: {type(resultado)}"
        param.resultados = resultado or []
    
        return param

    except MiException as e:
        print("---------------- MiException ---------------------")
        raise e
    except HTTPException as e:
        param.error_sistema(e=e, debug="mll_convierte_tarifas.HTTP_Exception")
        raise e
    except Exception as e:
        param.error_sistema(e=e, debug="mll_convierte_tarifas.Exception")
        raise e

    finally:
        imprime([tiempo, datetime.now().strftime('%Y-%m-%d %H:%M:%S')], "*  FIN TIEMPOS  ")



#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
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
        # print("1")
        # resultado = descarga.proceso(param=param)
        # print("2")

        # param.debug = f"Retornando: {type(resultado)}"
        # param.resultados = resultado or []
        # print("3")

        # return param

    except MiException as e:
        print("---------------- MiException ---------------------")
        raise e
    except HTTPException as e:
        param.error_sistema(e=e, debug="mll_descarga.HTTP_Exception")
        raise e
    except Exception as e:
        param.error_sistema(e=e, debug="mll_descarga.Exception")
        raise e

    finally:
        imprime([tiempo, datetime.now().strftime('%Y-%m-%d %H:%M:%S')], "*  FIN TIEMPOS  ")

# #----------------------------------------------------------------------------------
# #----------------------------------------------------------------------------------
# @router.get("/mll_encargos_navidad", response_model=InfoTransaccion)
# async def mll_encargos_navidad(id_App: int = Query(..., description="Identificador de la aplicación"),
#                         user: str = Query(..., description="Nombre del usuario que realiza la solicitud"),
#                         ret_code: int = Query(..., description="Código de retorno inicial"),
#                         ret_txt: str = Query(..., description="Texto descriptivo del estado inicial"),
#                        ):
    
#     try:
#         param = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, 
#                                 debug = f"infoTrans: {id_App} - {user} - {ret_code} - {ret_txt}")

#         # --------------------------------------------------------------------------------
#         param_resultado = encargos_navidad.proceso(param = param)
#         # --------------------------------------------------------------------------------

#         param.debug = f"Esto debería ser <infoTransaccion>: {type(param_resultado)}"
    
#     except MiException as e:
#         graba_log(param, "mll_carga_prod_erp.MiException", e)
                
#     except HTTPException as e:
#         param.error_sistema(e=e, debug="mll_carga_prod_erp.HTTPException")


#     except Exception as e:
#         param.error_sistema(e=e, debug="mll_fichas_tecnicas.Exception")

#     finally:
#         return param_resultado