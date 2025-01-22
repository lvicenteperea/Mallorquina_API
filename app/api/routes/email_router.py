from fastapi import APIRouter, Query, Body
from starlette.requests import Request
from typing import List, Optional, Dict

# mias
import app.services.emails.grabar_token as grabar_token
import app.services.emails.grabar_email as grabar_email

from app.utils.functions import graba_log, imprime
from app.utils.mis_excepciones import MadreException
from app.utils.InfoTransaccion import InfoTransaccion

# Definimos el router
router = APIRouter()


#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
@router.get("/eml_grabar_token", response_model=InfoTransaccion)
async def eml_grabar_token( request: Request,  # Para acceder a request.state.user
                            id_App: int = Query(..., description=""),
                            user: str = Query(..., description="Nombre del usuario que realiza la solicitud"),
                            ret_code: int = Query(..., description="Código de retorno inicial"),
                            ret_txt: str = Query(..., description="Texto descriptivo del estado inicial"),
                            tokenable: str = Query(..., description="Para su campo"),
                            nombre: str= Query(..., description="Nombre o descripción del token o de su uso"),
                            token: str = Query(..., description="Token que se le quiere asignar"),
                            abilities = Query(..., description="para que servicio o servicios array de cadenas: ['serv1','serv2','serv3',...]"),
                          ):
    
    try:
        # --------------------------------------------------------------------------------
        # Validaciones y construcción Básica
        # --------------------------------------------------------------------------------


        param = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, 
                                parametros=[tokenable, nombre, token, abilities],
                                debug = f"infoTrans: {id_App} - {user} - {ret_code} - {ret_txt} - {tokenable} - {nombre} - {token} - {abilities}")

        # --------------------------------------------------------------------------------
        # Control de autenticación de usuario
        # --------------------------------------------------------------------------------
        # Verificar la autenticación
        authenticated_user = request.state.user # AuthMiddleware.get_current_user(credentials)
        if user != authenticated_user:
            param.error_sistema(txt_adic="Error de usuario", debug=f"{user} - {authenticated_user}")
            raise MadreException(param,"Los usuarios no corresponden", -1)

        # --------------------------------------------------------------------------------
        # Servicio
        # --------------------------------------------------------------------------------
        param_resultado = grabar_token.proceso(param = param) # ya retorna un infoTransaccion
        # --------------------------------------------------------------------------------

        param.debug = f"Esto debería ser <infoTransaccion>: {type(param_resultado)}"
    

    except MadreException as e:
        graba_log(param, "eml_grabar_token.MadreException", e)
                
    except Exception as e:
        param.error_sistema()
        graba_log(param, "eml_grabar_token.Exception", e)

    finally:
        return param_resultado


#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
@router.post("/eml_grabar_email", response_model=InfoTransaccion)
async def eml_grabar_email( request: Request,  # Para acceder a request.state.user
                            id_App: int = Query(..., description="Identificador de la aplicación"),
                            user: str = Query(..., description="Nombre del usuario que realiza la solicitud"),
                            ret_code: int = Query(..., description="Código de retorno inicial"),
                            ret_txt: str = Query(..., description="Texto descriptivo del estado inicial"),
                            id_servidor: Optional[int] = Query(None, description="Servidor desde el que se va a lanzar"),
                            id_participante: Optional[int] = Query(None, description="Id del participante al que se le envía el correo"),
                            para: List[str] = Body(..., description="Lista de correos a los que se envía"),
                            para_nombre: Optional[str] = Query(None, description="En caso de ser solo uno, el nombre del destinatario"),
                            de: str = Query(..., description="Email del remitente"),
                            de_nombre: Optional[str] = Query(None, description="Nombre del remitente"),
                            cc: Optional[List[str]] = Body(None, description="Lista de correos a los que se envía copia"),
                            bcc: Optional[List[str]] = Body(None, description="Lista de correos a los que se envía copia oculta"),
                            prioridad: int = Query(1, description="Prioridad: 1, 2, 3..."),
                            reply_to: Optional[str] = Query(None, description="Correo de respuesta"),
                            clave_externa: str = Query(..., description="Clave externa para identificar el envío"),
                            asunto: str = Query(..., description="Puede ser un html, puede llevar variables tipo {nombre}"),
                            cuerpo: str = Query(..., description="Html del cuerpo del mensaje, puede llevar variables tipo {nombre}"),
                            lenguaje: str = Query("es", description="es, en,..."),
                            parametros: Optional[Dict[str, str]] = Body(None, description="Diccionario de variables para sustituir en el cuerpo y asunto"),
                            fecha_envio: Optional[str] = Query(None, description="Fecha en formato 'YYYY-MM-DD HH:MM:SS'"),
                            identificador_externo: Optional[str] = Query(None, description="Identificador del envío en el proveedor de servicios")
):
    
    try:
        # --------------------------------------------------------------------------------
        # Validaciones y construcción Básica
        # --------------------------------------------------------------------------------


        param = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, 
                                parametros=[id_servidor, id_participante, para, para_nombre, de, de_nombre, cc, bcc, prioridad, reply_to, clave_externa, 
                                            asunto, cuerpo, lenguaje, parametros, fecha_envio, identificador_externo],
                                debug = f"infoTrans: {id_App} - {user} - {ret_code} - {ret_txt} - {para} - {de} - {asunto} - {parametros}")

        # --------------------------------------------------------------------------------
        # Control de autenticación de usuario
        # --------------------------------------------------------------------------------
        # Verificar la autenticación
        authenticated_user = request.state.user # AuthMiddleware.get_current_user(credentials)
        if user != authenticated_user:
            param.error_sistema(txt_adic="Error de usuario", debug=f"{user} - {authenticated_user}")
            raise MadreException(param,"Los usuarios no corresponden", -1)

        # --------------------------------------------------------------------------------
        # Servicio
        # --------------------------------------------------------------------------------
        param_resultado = grabar_email.proceso(param = param) # ya retorna un infoTransaccion
        # --------------------------------------------------------------------------------

        param.debug = f"Esto debería ser <infoTransaccion>: {type(param_resultado)}"
        imprime([param], "*")
    

    except MadreException as e:
        graba_log(param, "eml_grabar_email.MadreException", e)
                
    except Exception as e:
        param.error_sistema()
        graba_log(param, "eml_grabar_email.Exception", e)

    finally:
        return param_resultado
