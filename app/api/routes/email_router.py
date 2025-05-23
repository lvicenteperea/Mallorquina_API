from fastapi import APIRouter, HTTPException, Query, Body
from starlette.requests import Request
from typing import List, Optional, Dict
# from pydantic import Field # BaseModel, Para definir los campos de la clase EmailRequest
from datetime import datetime

# mias
import app.services.emails.grabar_token as grabar_token
import app.services.emails.grabar_email as grabar_email
import app.services.emails.enviar_emails as enviar_emails

from app.utils.utilidades import graba_log, imprime
from app.utils.functions import control_usuario
from app.utils.mis_excepciones import MiException
from app.utils.InfoTransaccion import InfoTransaccion, ParamRequest
# Definimos el router
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
            param.sistem_error(txt_adic="Error de usuario", debug=f"{user} - {authenticated_user}")
            raise MiException(param,"Los usuarios no corresponden", -1)

        # --------------------------------------------------------------------------------
        # Servicio
        # --------------------------------------------------------------------------------
        param_resultado = grabar_token.proceso(param = param) # ya retorna un infoTransaccion
        # --------------------------------------------------------------------------------

        param.debug = f"Esto debería ser <infoTransaccion>: {type(param_resultado)}"
    
        return param_resultado

    except MiException as e:
        graba_log(param, "eml_grabar_token.MiException", e)
                
    except Exception as e:
        param.error_sistema(e=e, txt_adic="", debug="eml_grabar_token.Exception")

#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
class EmailRequest(ParamRequest):
    id_servidor: Optional[int] # = Field(None, description="Servidor desde el que se va a lanzar")
    id_participante: Optional[int] #  = Field(None, description="Id del participante al que se le envía el correo")
    para: List[str] #  = Field(..., description="Lista de correos a los que se envía")
    para_nombre: Optional[str] #  = Field(None, description="En caso de ser solo uno, el nombre del destinatario")
    de: str # = Field(..., description="Email del remitente")
    de_nombre: Optional[str] # = Field(None, description="Nombre del remitente")
    cc: Optional[List[str]] # = Field(None, description="Lista de correos a los que se envía copia")
    bcc: Optional[List[str]] # = Field(None, description="Lista de correos a los que se envía copia oculta")
    prioridad: int # = Field(1, description="Prioridad: 1, 2, 3...")
    reply_to: Optional[str] # = Field(None, description="Correo de respuesta")
    clave_externa: str # = Field(..., description="Clave externa para identificar el envío")
    asunto: str # = Field(..., description="Puede ser un html, puede llevar variables tipo {nombre}")
    cuerpo: str # = Field(..., description="Html del cuerpo del mensaje, puede llevar variables tipo {nombre}")
    lenguaje: str # = Field("es", description="es, en,...")
    parametros: Optional[Dict[str, str]] # = Field(None, description="Diccionario de variables para sustituir en el cuerpo y asunto")
    fecha_envio: Optional[str] # = Field(None, description="Fecha en formato 'YYYY-MM-DD HH:MM:SS'")
    identificador_externo: Optional[str] # = Field(None, description="Identificador del envío en el proveedor de servicios")
    ficheros: Optional[List[Dict[str, str]]] # formato: [{"nombre_archivo": "informe.pdf", "tipo_mime": "application/pdf", "contenido": base64.b64encode(open("ruta/al/archivo.pdf", "rb").read()).decode()}, ..]

@router.post("/eml_grabar_email", response_model=InfoTransaccion)
async def eml_grabar_email( request: Request,  body_params: EmailRequest = Body(...)):
    """ Grabamos un email en la tabla email_envios. """
    return await procesar_request(request, body_params, grabar_email, "eml_grabar_email")    
        

"""
@router.post("/eml_grabar_email", response_model=InfoTransaccion)
async def eml_grabar_email( request: Request,  # Para acceder a request.state.user
                            body_params: EmailRequest = Body(...)
):
    
    try:
        # --------------------------------------------------------------------------------
        # Validaciones y construcción Básica
        # --------------------------------------------------------------------------------


        # param = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, 
        #                         parametros=[id_servidor, id_participante, para, para_nombre, de, de_nombre, cc, bcc, prioridad, reply_to, clave_externa, 
        #                                     asunto, cuerpo, lenguaje, parametros, fecha_envio, identificador_externo],
        #                         debug = f"infoTrans: {id_App} - {user} - {ret_code} - {ret_txt} - {para} - {de} - {asunto} - {parametros}")
        
        param = InfoTransaccion.from_request(body_params)
        # --------------------------------------------------------------------------------
        # Control de autenticación de usuario
        # --------------------------------------------------------------------------------
        # Verificar la autenticación
        authenticated_user = request.state.user # AuthMiddleware.get_current_user(credentials)
        # if user != authenticated_user:
        #     imprime([user, authenticated_user], "@")
        #     param.sistem_error(txt_adic=f"Error de usuario{user} != {authenticated_user}", debug=f"{user} - {authenticated_user}")
        #     raise MiException(param, "Los usuarios no corresponden", -1)

        # --------------------------------------------------------------------------------
        # Servicio
        # --------------------------------------------------------------------------------
        param = grabar_email.proceso(param = param) # ya retorna un infoTransaccion
        param.debug = f"Retornando: {type(param)}"
        # --------------------------------------------------------------------------------

    
        return param

    except MiException as e:
        # imprime(["MiException"], "@")
        # graba_log(param, "eml_grabar_email.MiException", e)
        print("-----------------------------")
        print("-------------------")
        print(e)
        print("-------------------")
        print("-----------------------------")
        
                
    except Exception as e:
        param.error_sistema(e=e, txt_adic="", debug="eml_grabar_email.Exception")
"""


#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
@router.get("/eml_envia_emails", response_model=InfoTransaccion)
async def eml_envia_emails(id_App: int = Query(..., description="Identificador de la aplicación"),
                         user: str = Query(..., description="Nombre del usuario que realiza la solicitud"),
                         ret_code: int = Query(..., description="Código de retorno inicial"),
                         ret_txt: str = Query(..., description="Texto descriptivo del estado inicial"),
                         servidor: int = Query(..., description="Se van enviar los emails asociados a este servidor"),
                        ):

    try:
        resultado = []
        param = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, parametros=[servidor])
        param.debug = f"infoTrans: {id_App} - {user} - {ret_code} - {ret_txt} - {servidor}"

        # --------------------------------------------------------------------------------
        resultado = enviar_emails.proceso(param = param)
        # --------------------------------------------------------------------------------

        param.debug = f"Retornando: {type(resultado)}"
        param.resultados = resultado or []


        return param
   

    except MiException as e:
        graba_log(param, "eml_envia_emails.MiException", e)
                
    except HTTPException as e:
        param.error_sistema(e=e, txt_adic="", debug="eml_envia_emails.HTTPException")


    except Exception as e:
        param.error_sistema(e=e, txt_adic="", debug="eml_envia_emails.Exception")
