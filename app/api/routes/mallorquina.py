from fastapi import APIRouter, HTTPException, Query, Depends

from fastapi.security import HTTPAuthorizationCredentials
from app.middleware.auth import AuthMiddleware
from datetime import datetime


# mias
import app.services.mallorquina.sync_data as sync_data
import app.services.mallorquina.consulta_caja as consulta_caja
import app.services.mallorquina.arqueo_caja as arqueo_caja
import app.services.mallorquina.arqueo_caja_info as arqueo_caja_info
import app.services.mallorquina.tarifas_a_TPV as tarifas_a_TPV
import app.services.mallorquina.fichas_tecnicas as fichas_tecnicas
import app.services.mallorquina.carga_productos_erp as carga_productos_erp
import app.services.mallorquina.encargos_navidad as encargos_navidad
import app.services.emails.grabar_token as grabar_token


from app.utils.functions import graba_log, imprime
from app.utils.mis_excepciones import MadreException
from app.utils.InfoTransaccion import InfoTransaccion

# Definimos el router
router = APIRouter()


#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
@router.get("/mll_consultas", response_model=InfoTransaccion)
async def mll_consultas(id_App: int = Query(..., description="Identificador de la aplicación"),
                        user: str = Query(..., description="Nombre del usuario que realiza la solicitud"),
                        ret_code: int = Query(..., description="Código de retorno inicial"),
                        ret_txt: str = Query(..., description="Texto descriptivo del estado inicial"),
                        fecha: str = Query(None, description="Fecha de la solicitud en formato 'YYYY-MM-DD', por defecto la actual"),
                        credentials: HTTPAuthorizationCredentials = Depends(AuthMiddleware.security)
                       ):
    try:
        # Verificar la autenticación
        authenticated_user = AuthMiddleware.get_current_user(credentials)
        print(f"Usuario autenticado: {authenticated_user}")

        # Si no se proporciona `fecha`, usar la actual
        if not fecha:
            fecha = datetime.now().strftime('%Y-%m-%d')

        param = InfoTransaccion(
            id_App=id_App,
            user=user,
            ret_code=ret_code,
            ret_txt=ret_txt,
            parametros=[fecha]
        )
        param.debug = f"infoTrans: {id_App} - {user} - {ret_code} - {ret_txt} - {fecha}"

        # --------------------------------------------------------------------------------
        resultado = consulta_caja.recorre_consultas_tiendas(param=param)
        # --------------------------------------------------------------------------------

        param.debug = f"Retornando: {type(resultado)}"
        param.resultados = resultado or []


    except MadreException as e:
        graba_log(param, "mll_consultas.MadreException", e)

    except Exception as e:
        param.error_sistema()
        graba_log(param, "mll_consultas.Exception", e)

    finally:
        return param



#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
@router.get("/mll_sync_todo", response_model=InfoTransaccion)
async def mll_sync_todo(id_App: int = Query(..., description="Identificador de la aplicación"),
                        user: str = Query(..., description="Nombre del usuario que realiza la solicitud"),
                        ret_code: int = Query(..., description="Código de retorno inicial"),
                        ret_txt: str = Query(..., description="Texto descriptivo del estado inicial"),
                       ):

    try:
        resultado = []
        param = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, parametros=[])
        param.debug = f"infoTrans: {id_App} - {user} - {ret_code} - {ret_txt}"
        # --------------------------------------------------------------------------------
        resultado = sync_data.recorre_tiendas(param = param)
        # --------------------------------------------------------------------------------

        param.debug = f"Retornando: {type(resultado)}"
        param.resultados = resultado or []

    except MadreException as e:
        graba_log(param, "mll_sync_todo.MadreException", e)
                
    except HTTPException as e:
        param.error_sistema()
        graba_log(param, "mll_sync_todo.HTTPException", e)


    except Exception as e:
        param.error_sistema()
        graba_log(param, "mll_sync_todo.Exception", e)
    
    finally:
        return param
    

#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
@router.get("/mll_arqueo_caja", response_model=InfoTransaccion)
async def mll_arqueo_caja(  id_App: int = Query(..., description="Identificador de la aplicación"),
                            user: str = Query(..., description="Nombre del usuario que realiza la solicitud"),
                            ret_code: int = Query(..., description="Código de retorno inicial"),
                            ret_txt: str = Query(..., description="Texto descriptivo del estado inicial"),
                            fecha: str = Query(None, description="Fecha de la solicitud en formato 'YYYY-MM-DD', por defecto la actual"),
                         ):
    try:
        resultado = []
        param = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, parametros=[fecha])
        param.debug = f"infoTrans: {id_App} - {user} - {ret_code} - {ret_txt} - {fecha}"

        # --------------------------------------------------------------------------------
        resultado = arqueo_caja.proceso(param = param)
        # --------------------------------------------------------------------------------
        
        param.debug = f"Retornando: {type(resultado)}"
        param.resultados = resultado or []
    
    except MadreException as e:
        graba_log(param, "mll_arqueo_caja.MadreException", e)
                
    except HTTPException as e:
        param.error_sistema()
        graba_log(param, "mll_arqueo_caja.HTTPException", e)


    except Exception as e:
        param.error_sistema()
        graba_log(param, "mll_arqueo_caja.Exception", e)

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

        # --------------------------------------------------------------------------------
        resultado = arqueo_caja_info.informe(param = param)
        # --------------------------------------------------------------------------------
                
        param.debug = f"Retornando: {type(resultado)}"
        param.resultados = resultado or []
    
    except MadreException as e:
        graba_log(param, "mll_inf_arqueo_caja.MadreException", e)
                
    except HTTPException as e:
        param.error_sistema()
        graba_log(param, "mll_inf_arqueo_caja.HTTPException", e)

    except Exception as e:
        param.error_sistema()
        graba_log(param, "mll_inf_arqueo_caja.Exception", e)

    finally:
        return param
 

#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
@router.get("/mll_convierte_tarifas", response_model=InfoTransaccion)
async def mll_convierte_tarifas(id_App: int = Query(..., description="Identificador de la aplicación"),
                        user: str = Query(..., description="Nombre del usuario que realiza la solicitud"),
                        ret_code: int = Query(..., description="Código de retorno inicial"),
                        ret_txt: str = Query(..., description="Texto descriptivo del estado inicial"),
                        origen_path: str = Query(..., description="Fichero origen"),
                        output_path: str = Query(..., description="Fichero destino")
                       ):
    
    try:
        resultado = []
        param = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, parametros=[origen_path, output_path])
        param.debug = f"infoTrans: {id_App} - {user} - {ret_code} - {ret_txt} - {origen_path} - {output_path}"

        # --------------------------------------------------------------------------------
        resultado = tarifas_a_TPV.proceso(param = param)
        # --------------------------------------------------------------------------------

        param.debug = f"Retornando un lista: {type(resultado)}"
        param.resultados = resultado or []
    
    except MadreException as e:
        graba_log(param, "mll_convierte_tarifas.MadreException", e)
                
    except HTTPException as e:
        param.error_sistema()
        graba_log(param, "mll_convierte_tarifas.HTTPException", e)


    except Exception as e:
        param.error_sistema()
        graba_log(param, "mll_convierte_tarifas.Exception", e)

    finally:
        return param


#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
@router.get("/mll_fichas_tecnicas", response_model=InfoTransaccion)
async def mll_fichas_tecnicas(id_App: int = Query(..., description="Identificador de la aplicación"),
                        user: str = Query(..., description="Nombre del usuario que realiza la solicitud"),
                        ret_code: int = Query(..., description="Código de retorno inicial"),
                        ret_txt: str = Query(..., description="Texto descriptivo del estado inicial"),
                        #origen_path: str = Query(..., description="Fichero origen")
                        output_path: str = Query(..., description="Fichero destino")
                       ):
    
    try:
        resultado = []
        param = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, parametros=[output_path])
        param.debug = f"infoTrans: {id_App} - {user} - {ret_code} - {ret_txt} - {output_path}"

        # --------------------------------------------------------------------------------
        resultado = fichas_tecnicas.proceso(param = param)
        # --------------------------------------------------------------------------------

        param.debug = f"Retornando un lista: {type(resultado)}"
        param.resultados = resultado or []
    
    except MadreException as e:
        graba_log(param, "mll_fichas_tecnicas.MadreException", e)
                
    except HTTPException as e:
        param.error_sistema()
        graba_log(param, "mll_fichas_tecnicas.HTTPException", e)


    except Exception as e:
        param.error_sistema()
        graba_log(param, "mll_fichas_tecnicas.Exception", e)

    finally:
        return param

#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
@router.get("/mll_carga_prod_erp", response_model=InfoTransaccion)
async def mll_carga_prod_erp(id_App: int = Query(..., description="Identificador de la aplicación"),
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
    
    except MadreException as e:
        graba_log(param, "mll_carga_prod_erp.MadreException", e)
                
    except HTTPException as e:
        param.error_sistema()
        graba_log(param, "mll_carga_prod_erp.HTTPException", e)


    except Exception as e:
        param.error_sistema()
        graba_log(param, "mll_fichas_tecnicas.Exception", e)

    finally:
        return param


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
    
    except MadreException as e:
        graba_log(param, "mll_carga_prod_erp.MadreException", e)
                
    except HTTPException as e:
        param.error_sistema()
        graba_log(param, "mll_carga_prod_erp.HTTPException", e)


    except Exception as e:
        param.error_sistema()
        graba_log(param, "mll_fichas_tecnicas.Exception", e)

    finally:
        return param_resultado



#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
@router.get("/eml_grabar_token", response_model=InfoTransaccion)
async def eml_grabar_token(id_App: int = Query(..., description="Identificador de la aplicación"),
                        user: str = Query(..., description="Nombre del usuario que realiza la solicitud"),
                        ret_code: int = Query(..., description="Código de retorno inicial"),
                        ret_txt: str = Query(..., description="Texto descriptivo del estado inicial"),
                        tokenable: str = Query(..., description="Para su campo"),
                        nombre: str= Query(..., description="Nombre o descripción del token o de su uso"),
                        token: str = Query(..., description="Token que se le quiere asignar"),
                        abilities = Query(..., description="para que servicio o servicios array de cadenas: ['serv1','serv2','serv3',...]"),
                       ):
    
    try:
        param = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, 
                                parametros=[tokenable, nombre, token, abilities],
                                debug = f"infoTrans: {id_App} - {user} - {ret_code} - {ret_txt} - {tokenable} - {nombre} - {token} - {abilities}")

        # --------------------------------------------------------------------------------
        param_resultado = grabar_token.proceso(param = param) # ya retorna un infoTransaccion
        # --------------------------------------------------------------------------------

        param.debug = f"Esto debería ser <infoTransaccion>: {type(resultado)}"
    
    except MadreException as e:
        graba_log(param, "mll_carga_prod_erp.MadreException", e)
                
    except HTTPException as e:
        param.error_sistema()
        graba_log(param, "mll_carga_prod_erp.HTTPException", e)


    except Exception as e:
        param.error_sistema()
        graba_log(param, "mll_fichas_tecnicas.Exception", e)

    finally:
        return param_resultado
