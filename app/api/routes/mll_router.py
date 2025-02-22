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
import app.services.mallorquina.encargos_navidad as encargos_navidad
import app.services.auxiliares.descarga as descarga

from app.config.settings import settings

from app.utils.functions import graba_log, imprime
from app.utils.mis_excepciones import MiException
from app.utils.InfoTransaccion import InfoTransaccion, ParamRequest

# Definimos el router
router = APIRouter()



#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
class SincronizaRequest(ParamRequest):
    tiendas: Optional[List] = 0   # Tienda de la que queremos sacar la información
    
@router.post("/mll_sincroniza", response_model=InfoTransaccion,
             summary="🔄 Sincroniza datos con el sistema",
             description="""Este servicio sincroniza los datos entre la aplicación y el servidor.

                                - ✅ **Requiere autenticación**
                                - ✅ **Recibe un `id_App` y un `user`** para identificar la sincronización
                                - ✅ **Retorna `status` y `message` indicando el éxito o error**
                         """,
             response_description="📌 Respuesta de un objeto tipo InfoTransaccion, y en el atributo 'resultados' habrá una lista de textos"
            )
@router.get("/mll_sincroniza", response_model=InfoTransaccion)
async def mll_sincroniza(request: Request,  # Para acceder a request.state.user
                         body_params: SincronizaRequest = Body(...)
                        ):
    try:
        # --------------------------------------------------------------------------------
        param = InfoTransaccion.from_request(body_params)
        
        tiempo = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # --------------------------------------------------------------------------------
        # Validaciones y construcción Básica
        # --------------------------------------------------------------------------------
        # -------------------------------------------------------------
        

        # --------------------------------------------------------------------------------
        # Control de autenticación de usuario
        # --------------------------------------------------------------------------------
        # Verificar la autenticación
        authenticated_user = request.state.user # AuthMiddleware.get_current_user(credentials)
        if param.user != authenticated_user:
            param.sistem_error(txt_adic="Error de usuario", debug=f"{param.user} - {authenticated_user}")
            raise MiException(param,"Los usuarios no corresponden", -1)

        # --------------------------------------------------------------------------------
        # Servicio
        # --------------------------------------------------------------------------------
        resultado = sincroniza.proceso(param = param)
        # --------------------------------------------------------------------------------

        imprime([tiempo, datetime.now().strftime('%Y-%m-%d %H:%M:%S')], "*  FIN TIEMPOS  ")


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



#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
class FechaRequest(ParamRequest):
    fecha: str    # Dia de cierre que se necesita en formato 'YYYY-MM-DD', por defecto la actual
    tienda: Optional[int] = 0   # Tienda de la que queremos sacar la información
    
@router.post("/mll_consultas_cierre", response_model=InfoTransaccion,
             summary="🔄 Consulta de los datos de cierre una fecha de una tienda",
             description="""Retorna un JSON con los datos.

                                - ✅ **Requiere autenticación**
                                - ✅ **Recibe un `id_App` y un `user`** para identificar la sincronización
                                - ✅ **Retorna `status` y `message` indicando el éxito o error**
                         """,
             response_description="📌 Respuesta de un objeto tipo InfoTransaccion, y en el atributo 'resultados' habrá una lista de textos"
)
async def mll_consultas_cierre( request: Request,  # Para acceder a request.state.user
                                body_params: FechaRequest = Body(...),
                               ):
    try:
        # --------------------------------------------------------------------------------
        # Validaciones y construcción Básica
        # --------------------------------------------------------------------------------
        # Si no se proporciona `fecha`, usar la actual
        if not body_params.fecha:
            body_params.fecha = datetime.now().strftime('%Y-%m-%d')

        if not body_params.tienda:
            body_params.tienda = 0

        # --------------------------------------------------------------------------------
        param = InfoTransaccion.from_request(body_params)

        # --------------------------------------------------------------------------------
        # Control de autenticación de usuario
        # --------------------------------------------------------------------------------
        # Verificar la autenticación
        authenticated_user = request.state.user # AuthMiddleware.get_current_user(credentials)
        if param.user != authenticated_user:
            param.sistem_error(txt_adic="Error de usuario", debug=f"{param.user} - {authenticated_user}")
            raise MiException(param,"Los usuarios no corresponden", -1)
        # else:
        #     print(f"Usuario autenticado: {authenticated_user}")

        # --------------------------------------------------------------------------------
        # Servicio
        # --------------------------------------------------------------------------------
        resultado = consulta_caja.recorre_consultas_tiendas(param=param)

        param.debug = f"Retornando: {type(resultado)}"
        param.resultados = resultado or []

        return param

    except MiException as e:
        graba_log(param, "mll_consultas_cierre.MiException", e)

    except Exception as e:
        param.error_sistema(e=e, debug="mll_consultas_cierre.Exception")



#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
@router.get("/mll_arqueo_caja", response_model=InfoTransaccion)
async def mll_arqueo_caja(  request: Request,  # Para acceder a request.state.user
                            id_App: int = Query(..., description="Identificador de la aplicación"),
                            user: str = Query(..., description="Nombre del usuario que realiza la solicitud"),
                            ret_code: int = Query(..., description="Código de retorno inicial"),
                            ret_txt: str = Query(..., description="Texto descriptivo del estado inicial"),
                            fecha: str = Query(None, description="Fecha de la solicitud en formato 'YYYY-MM-DD'"),
                         ):
    try:
        resultado = []
        param = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, parametros=[fecha])
        param.debug = f"infoTrans: {id_App} - {user} - {ret_code} - {ret_txt} - {fecha}"

        # --------------------------------------------------------------------------------
        # Control de autenticación de usuario
        # --------------------------------------------------------------------------------
        # Verificar la autenticación
        authenticated_user = request.state.user # AuthMiddleware.get_current_user(credentials)
        if user != authenticated_user:
            param.sistem_error(txt_adic="Error de usuario", debug=f"{user} - {authenticated_user}")
            raise MiException(param,"Los usuarios no corresponden", -1)

        # --------------------------------------------------------------------------------
        resultado = arqueo_caja.proceso(param = param)
        # --------------------------------------------------------------------------------
        
        param.debug = f"Retornando: {type(resultado)}"
        param.resultados = resultado or []
        param.ret_txt = "OK"
    
    except MiException as e:
        graba_log(param, "mll_arqueo_caja.MiException", e)
                
    except HTTPException as e:
        param.error_sistema(e=e, debug="mll_arqueo_caja.HTTPException")


    except Exception as e:
        param.error_sistema(e=e, debug="mll_arqueo_caja.Exception")

    finally:
        return param

    

#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
@router.get("/mll_inf_arqueo_caja", response_model=InfoTransaccion)
async def mll_inf_arqueo_caja(id_App: int = Query(..., description="Identificador de la aplicación"),
                              user: str = Query(..., description="Nombre del usuario que realiza la solicitud"),
                              ret_code: int = Query(..., description="Código de retorno inicial"),
                              ret_txt: str = Query(..., description="Texto descriptivo del estado inicial"),
                              fecha: str = Query(None, description="Fecha de la solicitud en formato 'YYYY-MM-DD', por defecto la actual"),
                              tienda: int = Query(0, description="BBDD/Tienda (mll_cfg_bbdd) de la que queremos la información, 0 --> Todas"),
                             ):

    try:
        resultado = []
        if not fecha: # si no tiene parametro fecha
            fecha = datetime.now().strftime('%Y-%m-%d')

        param = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, parametros=[fecha, tienda], debug="Inicio")
        param.debug = f"infoTrans: {id_App} - {user} - {ret_code} - {ret_txt} - {fecha} - {tienda}"

        imprime("Llegamos", "*")


        # --------------------------------------------------------------------------------
        resultado = arqueo_caja_info.informe(param = param)
        # --------------------------------------------------------------------------------
                
        param.debug = f"Retornando: {type(resultado)}"
        param.resultados = resultado or []
    
    except MiException as e:
        graba_log(param, "mll_inf_arqueo_caja.MiException", e)
                
    except HTTPException as e:
        param.error_sistema(e=e, debug="mll_inf_arqueo_caja.HTTPException")

    except Exception as e:
        param.error_sistema(e=e, debug="mll_inf_arqueo_caja.Exception")

    finally:
        return param
 

#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
@router.get("/mll_convierte_tarifas", response_model=InfoTransaccion)
async def mll_convierte_tarifas(id_App: int = Query(..., description="Identificador de la aplicación"),
                        user: str = Query(..., description="Nombre del usuario que realiza la solicitud"),
                        ret_code: int = Query(..., description="Código de retorno inicial"),
                        ret_txt: str = Query(..., description="Texto descriptivo del estado inicial"),
                       ):
    
    try:
        resultado = []
        param = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, parametros=[])  # origen_path]) #, output_path])
        param.debug = f"infoTrans: {id_App} - {user} - {ret_code} - {ret_txt}" # - {origen_path}" # - {output_path}"
        
        # --------------------------------------------------------------------------------
        # resultado = tarifas_a_TPV.proceso(param = param)
        resultado = tarifas_ERP_a_TPV.proceso(param = param)
        # --------------------------------------------------------------------------------

        param.debug = f"Retornando un lista: {type(resultado)}"
        param.resultados = resultado or []
    
    except MiException as e:
        graba_log(param, "mll_convierte_tarifas.MiException", e)
                
    except HTTPException as e:
        param.error_sistema(e=e, debug="mll_convierte_tarifas.HTTPException")


    except Exception as e:
        param.error_sistema(e=e, debug="mll_convierte_tarifas.Exception")

    finally:
        return param


#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
@router.get("/mll_fichas_tecnicas", response_model=InfoTransaccion)
async def mll_fichas_tecnicas(request: Request,  # Para acceder a request.state.user
                              id_App: int = Query(..., description="Identificador de la aplicación"),
                              user: str = Query(..., description="Nombre del usuario que realiza la solicitud"),
                              ret_code: int = Query(..., description="Código de retorno inicial"),
                              ret_txt: str = Query(..., description="Texto descriptivo del estado inicial"),
                              output_path: str = Query(..., description="Fichero destino")
                             ):
    
    try:
        resultado = []
        if not output_path:
            output_path = "fichas_tecnicas.html"
            
        param = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, parametros=[output_path])
        param.debug = f"infoTrans: {id_App} - {user} - {ret_code} - {ret_txt} - {output_path}"

        # --------------------------------------------------------------------------------
        # Control de autenticación de usuario
        # --------------------------------------------------------------------------------
        # Verificar la autenticación
        authenticated_user = request.state.user # AuthMiddleware.get_current_user(credentials)
        if user != authenticated_user:
            param.sistem_error(txt_adic="Error de usuario", debug=f"{user} - {authenticated_user}")
            raise MiException(param,"Los usuarios no corresponden", -1)
        # else:
        #     print(f"Usuario autenticado: {authenticated_user}")


        # --------------------------------------------------------------------------------
        resultado = fichas_tecnicas.proceso(param = param)
        # --------------------------------------------------------------------------------

        param.debug = f"Retornando un lista: {type(resultado)}"
        param.resultados = resultado or []

        return param
    
    except MiException as e:
        graba_log(param, "mll_fichas_tecnicas.MiException", e)
                
    except HTTPException as e:
        param.error_sistema(e=e, debug="mll_fichas_tecnicas.HTTPException")


    except Exception as e:
        param.error_sistema(e=e, debug="mll_fichas_tecnicas.Exception")


#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
@router.post("/mll_carga_prod_erp", response_model=InfoTransaccion)
async def mll_carga_prod_erp(id_App: int = Form(..., description="Identificador de la aplicación"),
                             user: str = Form(..., description="Nombre del usuario que realiza la solicitud"),
                             ret_code: int = Form(..., description="Código de retorno inicial"),
                             ret_txt: str = Form(..., description="Texto descriptivo del estado inicial"),
                             file: UploadFile = File(..., description="Archivo subido por el usuario")
                            ):
    
    try:
        resultado = []
        fichero = file.filename
        param = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, 
                                parametros=[fichero],
                                debug = f"infoTrans: {id_App} - {user} - {ret_code} - {ret_txt} - {fichero}")


        # Guardar el archivo subido en el servidor
        # origen_path  = f"./uploads/{file.filename}"
        excel = os.path.join(f"{settings.RUTA_DATOS}/erp", f"{fichero}")
        with open(excel, "wb") as f:
            f.write(await file.read())

        # --------------------------------------------------------------------------------
        resultado = carga_productos_erp.proceso(param = param)
        # --------------------------------------------------------------------------------

        param.debug = f"Retornando un lista: {type(resultado)}"
        param.resultados = resultado or []
    
    except MiException as e:
        graba_log(param, "mll_carga_prod_erp.MiException", e)
                
    except HTTPException as e:
        param.error_sistema(e=e, debug="mll_carga_prod_erp.HTTPException")


    except Exception as e:
        param.error_sistema(e=e, debug="mll_fichas_tecnicas.Exception")

    finally:
        return param

#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
@router.get("/mll_carga_prod_erp_2", response_model=InfoTransaccion)
async def mll_carga_prod_erp2(request: Request,  # Para acceder a request.state.user,
                             id_App: int = Query(..., description="Identificador de la aplicación"),
                             user: str = Query(..., description="Nombre del usuario que realiza la solicitud"),
                             ret_code: int = Query(..., description="Código de retorno inicial"),
                             ret_txt: str = Query(..., description="Texto descriptivo del estado inicial"),
                             origen_path: str = Query(..., description="Fichero origen"),
                            ):
    
    try:
        resultado = []
        param = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, 
                                parametros=[origen_path],
                                debug = f"infoTrans: {id_App} - {user} - {ret_code} - {ret_txt} - {origen_path}")

        # --------------------------------------------------------------------------------
        resultado = carga_productos_erp.proceso(param = param)
        # --------------------------------------------------------------------------------

        param.debug = f"Retornando un lista: {type(resultado)}"
        param.resultados = resultado or []
    
    except MiException as e:
        graba_log(param, "mll_carga_prod_erp.MiException", e)
                
    except HTTPException as e:
        param.error_sistema(e=e, debug="mll_carga_prod_erp.HTTPException")


    except Exception as e:
        param.error_sistema(e=e, debug="mll_fichas_tecnicas.Exception")

    finally:
        return param


#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
class DescargaRequest(ParamRequest):
    tipo: str = "TPV"
    nombres: List[str] = []

@router.post("/mll_descarga")
async def mll_descarga(request: Request,
                       body_params: DescargaRequest = Body(...)):
    try:

        # --------------------------------------------------------------------------------
        # Validaciones y construcción Básica
        # --------------------------------------------------------------------------------

        # --------------------------------------------------------------------------------
        imprime([type(body_params.nombres), len(body_params.nombres), body_params.nombres], "*")
        
        param = InfoTransaccion.from_request(body_params)

        imprime([param], "*")

        # --------------------------------------------------------------------------------
        # Control de autenticación de usuario
        # --------------------------------------------------------------------------------
        # Verificar la autenticación
        # authenticated_user = request.state.user # AuthMiddleware.get_current_user(credentials)
        # if user != authenticated_user:
        #     param.sistem_error(txt_adic="Error de usuario", debug=f"{user} - {authenticated_user}")
        #     raise MiException(param,"Los usuarios no corresponden", -1)
        # else:
        #     print(f"Usuario autenticado: {authenticated_user}")

        # --------------------------------------------------------------------------------
        # Servicio
        # --------------------------------------------------------------------------------
        return descarga.proceso(param=param)
         

    except MiException as e:
        graba_log(param, "mll_descarga.MiException", e)
        raise

    except HTTPException as e:
        param.error_sistema(e=e, debug="mll_sync_todo.HTTPException")
        raise


    except Exception as e:
        param.error_sistema(e=e, debug="mll_descarga.Exception")
        raise

 

#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
@router.get("/mll_encargos_navidad", response_model=InfoTransaccion)
async def mll_encargos_navidad(id_App: int = Query(..., description="Identificador de la aplicación"),
                        user: str = Query(..., description="Nombre del usuario que realiza la solicitud"),
                        ret_code: int = Query(..., description="Código de retorno inicial"),
                        ret_txt: str = Query(..., description="Texto descriptivo del estado inicial"),
                       ):
    
    try:
        param = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, 
                                debug = f"infoTrans: {id_App} - {user} - {ret_code} - {ret_txt}")

        # --------------------------------------------------------------------------------
        param_resultado = encargos_navidad.proceso(param = param)
        # --------------------------------------------------------------------------------

        param.debug = f"Esto debería ser <infoTransaccion>: {type(param_resultado)}"
    
    except MiException as e:
        graba_log(param, "mll_carga_prod_erp.MiException", e)
                
    except HTTPException as e:
        param.error_sistema(e=e, debug="mll_carga_prod_erp.HTTPException")


    except Exception as e:
        param.error_sistema(e=e, debug="mll_fichas_tecnicas.Exception")

    finally:
        return param_resultado