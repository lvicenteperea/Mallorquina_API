from fastapi import APIRouter, HTTPException, Query
from datetime import datetime

# mias
from app.api.schemas.url import ValidaUrlResponse
from app.api.schemas.precodigo import ValidaPrecodigoRequest
import app.services.db.mysql as db
# from app.services.db.mysql import db_valida_url, db_obtener_contenidos, db_valida_precodigo, db_semillas_campaing
from app.api.schemas.contenido import ListaContenidosResponse
from app.utils.mis_excepciones import MadreException
from app.utils.InfoTransaccion import InfoTransaccion

# PRUEBAS
from app.api.schemas.centro import ListaCentrosResponse


# Definimos el router
router = APIRouter()


#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
@router.get("/valida_url")
def valida_url(id_App: int = Query(..., description="Identificador de la aplicación"),
               user: str = Query(..., description="Nombre del usuario que realiza la solicitud"),
               ret_code: int = Query(..., description="Código de retorno inicial"),
               ret_txt: str = Query(..., description="Texto descriptivo del estado inicial"),
               url: str = Query(..., description="URL a validar"),
               fecha: str = Query(None, description="Fecha de la solicitud en formato 'YYYY-MM-DD HH:MI:SS', por defecto la actual"),
               id_frontal: int = Query(None, description="OUT. Retorna ID del frontal"),
               id_cat: int = Query(None, description="OUT. Retorna ID de la categoría")
               ):
    """ -- DOCUMENTACION --
        Valida una URL específica contra ciertos parámetros y devuelve un resultado.

        Esta función recibe varios parámetros relacionados con la aplicación y el usuario, 
        junto con una URL para validar. Realiza una llamada a la base de datos para ejecutar 
        el procedimiento `db_valida_url` y devuelve el resultado de la validación.
        
        Cuando llega una petición al frontal, el frontal no sabe que contenido debe cargar. Este 
        servicio le indica al frontal es el que debe de cargar (Ya que puede tener varios), es decir, 
        que plantilla y que contenidos pertenecen a ese frontal. 


        Parámetros:
        -----------
        id_App : int
            Identificador de la aplicación.
        user : str
            Nombre del usuario que realiza la solicitud.
        ret_code : int
            Código de retorno inicial.
        ret_txt : str
            Texto descriptivo del estado inicial.
        url : str
            URL a validar.
        fecha : str
            Fecha de la solicitud en formato 'YYYY-MM-DD HH:MI:SS'.
        id_frontal : Optional[int], opcional
            ID del frontal, si aplica.
        id_cat : Optional[int], opcional
            ID de la categoría, si aplica.

        Retorna:
        --------
        ValidaUrlResponse
            - Si ret_code = 0 Ok
                - id_frontal
                - id_cat, si fuera el caso 
            - ret_code < 0 Ko. 
                - ret_txt: Mensaje de error
        Excepciones:
        ------------
        HTTPException
            Se lanza si la validación falla con un código de error negativo.
    """

    if not fecha:
        # Si la variable es None o está vacía, asignar la fecha y hora actuales
        fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    infoTrans = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt)
    
    param = [infoTrans, url, fecha, id_frontal, id_cat]
    
    resultado = db.valida_url(param = param)

    if resultado.ret_code < 0:
        raise HTTPException(status_code=500, detail= {"ret_code": resultado.ret_code,
                                                      "ret_txt": resultado.ret_txt
                                                     }
                           )

    url_validada = ValidaUrlResponse(codigo_error=resultado.ret_code, mensaje=resultado.ret_txt)
    url_validada.asigna_salida(resultado.parametros)
    return url_validada
    

#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
@router.get("/valida_precodigo")
def valida_precodigo(id_App: int = Query(..., description="Identificador de la aplicación"),
                     user: str = Query(..., description="Nombre del usuario que realiza la solicitud"),
                     ret_code: int = Query(..., description="Código de retorno inicial"),
                     ret_txt: str = Query(..., description="Texto descriptivo del estado inicial"),

                     precodigo: str = Query(..., description="Es el precodigo a validar"),
                     fecha: str = Query(None, description="Fecha de la solicitud en formato 'YYYY-MM-DD HH:MI:SS', por defecto la actual"),
                     url: str = Query(None, description="Envia URL o id_frontal"),
                     id_frontal: int = Query(None, description="Envia URL o id_frontal"),

                     id_cat: int = Query(None, description="OUT. Retorna ID de la categoría"),
                     id_Campaign: int = Query(None, description="OUT. Retorna ID de la campaña"),
                     id_Canje: int = Query(None, description="OUT. Retorna ID del canje"),
                     id_Participante: int = Query(None, description="OUT. Retorna ID del participante"),
                     id_Precodigo: int = Query(None, description="OUT. Retorna ID del précodigo"),
                    ):
    """ -- DOCUMENTACION --
        Valida un precódigo y retorna los identificadores relacionados.

        Esta función valida un precódigo recibido junto con otros parámetros de entrada, como la URL o el ID del frontal. 
        Además, retorna varios identificadores relacionados si la validación es exitosa.

        Una vez con el frontal cargado, el usaurio introduce un PRECODIGO, Con este precodigo ya podemos retornar la campaña 
        y otros datos si el procodigo ya ha sido canjeado.


        Parámetros:
        -----------
        id_App : int
            Identificador de la aplicación.
        user : str
            Nombre del usuario que realiza la solicitud.
        ret_code : int
            Código de retorno inicial.
        ret_txt : str
            Texto descriptivo del estado inicial.
        precodigo : str
            El precódigo a validar.
        fecha : str, opcional
            Fecha de la solicitud en formato 'YYYY-MM-DD HH:MI:SS'. Si no se proporciona, se asigna la fecha y hora actuales.
        url : str, opcional
            La URL relacionada con la solicitud o el ID del frontal. Al menos uno de estos campos debe ser proporcionado.
        id_frontal : int, opcional
            El ID del frontal relacionado con la solicitud o la URL. Al menos uno de estos campos debe ser proporcionado.
        id_cat : int, opcional
            OUT. Retorna ID de la categoría tras la validación.
        id_Campaign : int, opcional
            OUT. Retorna ID de la campaña tras la validación.
        id_Canje : int, opcional
            OUT. Retorna ID del canje tras la validación.
        id_Participante : int, opcional
            OUT. Retorna ID del participante tras la validación.
        id_Precodigo : int, opcional
            OUT. Retorna ID del precódigo tras la validación.

        Retorno:
        --------
        ValidaPrecodigoRequest
            Un objeto que contiene el código de error, un mensaje descriptivo y los identificadores relacionados.

        Excepciones:
        ------------
        HTTPException
            Se lanza si la validación falla con un código de error negativo.
    """

    if not fecha:
        # Si la variable es None o está vacía, asignar la fecha y hora actuales
        fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if not url and not id_frontal:
        return ValidaPrecodigoRequest(codigo_error=-1, mensaje="Debe llegar url o frontal")
        

    infoTrans = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt)
    
    param = [infoTrans, precodigo, fecha, url, id_frontal, id_cat, id_Campaign, id_Canje, id_Participante, id_Precodigo]
    
    resultado = db.valida_precodigo(param = param)

    if resultado.ret_code < 0:
        raise HTTPException(status_code=500, detail= {"ret_code": resultado.ret_code,
                                                      "ret_txt": resultado.ret_txt
                                                     }
                           )
    
    url_validada = ValidaPrecodigoRequest(codigo_error=resultado.ret_code, mensaje=resultado.ret_txt)
    url_validada.asigna_salida(resultado.parametros)
    return url_validada
    

#----------------------------------------------------------------------------------
# Con el dato de campaña ya se pueden determinar que Semillas le corresponden 
# (que depende de las categorias asociadas a la campaña)
@router.get("/semillas_campaing")
#----------------------------------------------------------------------------------
def semillas_campaing(id_App: int = Query(..., description="Identificador de la aplicación"),
                      user: str = Query(..., description="Nombre del usuario que realiza la solicitud"),
                      ret_code: int = Query(..., description="Código de retorno inicial"),
                      ret_txt: str = Query(..., description="Texto descriptivo del estado inicial"),

                      id_Campaign: int = Query(..., description="ID de la campaña en la que buscar sus semillas"),
                    ):
    
    infoTrans = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt)
    
    param = [infoTrans, id_Campaign]
    
    resultado = db.semillas_campaing(param = param)

    if resultado.ret_code < 0:
        raise HTTPException(status_code=500, detail= {"ret_code": resultado.ret_code,
                                                      "ret_txt": resultado.ret_txt
                                                     }
                           )
    
    url_validada = ValidaPrecodigoRequest(codigo_error=resultado.ret_code, mensaje=resultado.ret_txt)
    url_validada.asigna_salida(resultado.parametros)
    return url_validada
    

#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
@router.get("/cnt_contenidos", response_model=ListaContenidosResponse)
async def cnt_contenidos(id_App: int = Query(..., description="Identificador de la aplicación"),
                         user: str = Query(..., description="Nombre del usuario que realiza la solicitud"),
                         ret_code: int = Query(..., description="Código de retorno inicial"),
                         ret_txt: str = Query(..., description="Texto descriptivo del estado inicial"),
                         id_idioma: int = Query(0, description="Identificador del idioma (opcional, por defecto 0)"),
                         id_dispositivo: int = Query(0, description="Identificador del dispositivo (opcional, por defecto 0)"),
                         fecha: str = Query(None, description="Fecha de la solicitud en formato 'YYYY-MM-DD HH:MI:SS' (opcional)"),
                         id_cnt: int = Query(..., description="Identificador del contenido a obtener"),
                         vacios: str = Query('N', description="Indica si se deben incluir contenidos vacíos (S --> sacar vacios también, cualquier otro valor no los saca)")
                         ):
    """ -- DOCUMENTACION --
        Obtiene una lista de contenidos basados en los parámetros proporcionados.

        Este endpoint permite obtener una lista de contenidos según los parámetros especificados, 
        como el idioma, el dispositivo, la fecha, y el identificador del contenido. La función llama 
        a un procedimiento almacenado en la base de datos para recuperar los contenidos solicitados.

        Parámetros:
        -----------
        id_App : int
            Identificador de la aplicación.
        user : str
            Nombre del usuario que realiza la solicitud.
        ret_code : int
            Código de retorno inicial.
        ret_txt : str
            Texto descriptivo del estado inicial.
        id_idioma : int, opcional
            Identificador del idioma (opcional, por defecto 0: Todos los coge para el primer idioma que exista o si hay un contenido que valga para todos los idiomas).
        id_dispositivo : int, opcional
            Identificador del dispositivo (opcional, por defecto 0: Para el primer dispositivo que encuentre contenido o el que valga para todos).
        fecha : str, opcional
            Fecha de la solicitud en formato 'YYYY-MM-DD HH:MI:SS' (opcional).
            Si no se proporciona, se utiliza la fecha y hora actuales.
        id_cnt : int
            Identificador del contenido a obtener.
        vacios : str
            Indica si se deben incluir contenidos vacíos (S --> sacar vacios también, cualquier otro valor no los saca).

        Retorna:
        --------
        ListaContenidosResponse
            - Si ret_code = 0 Ok
                - lista con el json de los contenidos
            - ret_code < 0 Ko. 
                - ret_txt: Mensaje de error

        Excepciones:
        ------------
        MadreException
            Se lanza si ocurre un error de aplicación específico con un código de error negativo.
        HTTPException
            Se lanza si ocurre cualquier otro tipo de error no controlado durante la ejecución.

        Ejemplo de Uso:
        ---------------
        ```
        response = cnt_contenidos(id_App=1, user="usuario", ret_code=0, ret_txt="Inicio", id_idioma=1, id_dispositivo=2, fecha="2024-08-21 12:00:00", id_cnt=123, vacios="N")
        print(response.lista)
        ```

        Notas:
        ------
        - Si no se proporciona la fecha, se utilizará la fecha y hora actuales.
        - La función maneja excepciones específicas y genéricas, devolviendo los códigos de error adecuados.
    """
    try:
        if not fecha:
            # Si la variable es None o está vacía, asignar la fecha y hora actuales
            fecha_hora_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        else:
            # Si la variable ya tiene un valor, mantenerlo
            fecha_hora_actual = fecha
        
        infoTrans = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt)

        param = [infoTrans, id_idioma, id_dispositivo, fecha_hora_actual, id_cnt, vacios]
        
        resultado = db.obtener_contenidos(param = param)

        # if resultado['ret_code'] != 0:
        if resultado.ret_code < 0:
            raise MadreException({"ret_code": resultado.ret_code, "ret_txt": resultado.ret_txt}, 400)

        return ListaContenidosResponse(codigo_error=resultado.ret_code, mensaje=resultado.ret_txt, lista=resultado.resultados)
    

    except MadreException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
@router.get("/cnt_categorias", response_model=ListaContenidosResponse)
async def cnt_categorias(id_App: int = Query(..., description="Identificador de la aplicación"),
                         user: str = Query(..., description="Nombre del usuario que realiza la solicitud"),
                         ret_code: int = Query(..., description="Código de retorno inicial"),
                         ret_txt: str = Query(..., description="Texto descriptivo del estado inicial"),
                         id_idioma: int = Query(0, description="Identificador del idioma (opcional, por defecto 0)"),
                         id_dispositivo: int = Query(0, description="Identificador del dispositivo (opcional, por defecto 0)"),
                         fecha: str = Query(None, description="Fecha de la solicitud en formato 'YYYY-MM-DD HH:MI:SS' (opcional)"),
                         id_campaing: int = Query(..., description="Campaña de la que de la que se van a sacar las categorias y experiencias"),
                         vacios: str = Query('N', description="Indica si se deben incluir contenidos vacíos (S --> sacar vacios también, cualquier otro valor no los saca)")
                         ):
    """ -- DOCUMENTACION --
        Obtiene una lista de contenidos basados en los parámetros proporcionados.

        Este endpoint permite obtener una lista de los contenidos relacionadas con las categorías que pertenecen
        a una campaña.

        Parámetros:
        -----------
        id_App : int
            Identificador de la aplicación.
        user : str
            Nombre del usuario que realiza la solicitud.
        ret_code : int
            Código de retorno inicial.
        ret_txt : str
            Texto descriptivo del estado inicial.
        id_idioma : int, opcional
            Identificador del idioma (opcional, por defecto 0: Todos los coge para el primer idioma que exista o si hay un contenido que valga para todos los idiomas).
        id_dispositivo : int, opcional
            Identificador del dispositivo (opcional, por defecto 0: Para el primer dispositivo que encuentre contenido o el que valga para todos).
        fecha : str, opcional
            Fecha de la solicitud en formato 'YYYY-MM-DD HH:MI:SS' (opcional).
            Si no se proporciona, se utiliza la fecha y hora actuales.
        id_campaing : int
            Campaña de la que de la que se van a sacar las categorias y experiencias
        vacios : str
            Indica si se deben incluir contenidos vacíos (S --> sacar vacios también, cualquier otro valor no los saca).

        Retorna:
        --------
        ListaContenidosResponse
            - Si ret_code = 0 Ok
                - lista con el json de los contenidos
            - ret_code < 0 Ko. 
                - ret_txt: Mensaje de error

        Excepciones:
        ------------
        MadreException
            Se lanza si ocurre un error de aplicación específico con un código de error negativo.
        HTTPException
            Se lanza si ocurre cualquier otro tipo de error no controlado durante la ejecución.

        Ejemplo de Uso:
        ---------------
        ```
        response = cnt_contenidos(id_App=1, user="usuario", ret_code=0, ret_txt="Inicio", id_idioma=1, id_dispositivo=2, fecha="2024-08-21 12:00:00", id_campaing=123, vacios="N")
        print(response.lista)
        ```

        Notas:
        ------
        - Si no se proporciona la fecha, se utilizará la fecha y hora actuales.
        - La función maneja excepciones específicas y genéricas, devolviendo los códigos de error adecuados.
    """
    try:
        if not fecha:
            # Si la variable es None o está vacía, asignar la fecha y hora actuales
            fecha_hora_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        else:
            # Si la variable ya tiene un valor, mantenerlo
            fecha_hora_actual = fecha

        infoTrans = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt)

        param = [infoTrans, id_idioma, id_dispositivo, fecha_hora_actual, id_campaing, vacios]

        resultado = db.obtener_cnt_categorias(param = param)

        # if resultado['ret_code'] != 0:
        if resultado.ret_code < 0:
            raise MadreException({"ret_code": resultado.ret_code, "ret_txt": resultado.ret_txt}, 400)

        return ListaContenidosResponse(codigo_error=resultado.ret_code, mensaje=resultado.ret_txt, lista=resultado.resultados)
    

    except MadreException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
@router.get("/cnt_exp_por_cat", response_model=ListaContenidosResponse)
async def cnt_exp_por_cat(id_App: int = Query(..., description="Identificador de la aplicación"),
                         user: str = Query(..., description="Nombre del usuario que realiza la solicitud"),
                         ret_code: int = Query(..., description="Código de retorno inicial"),
                         ret_txt: str = Query(..., description="Texto descriptivo del estado inicial"),
                         id_idioma: int = Query(0, description="Identificador del idioma (opcional, por defecto 0)"),
                         id_dispositivo: int = Query(0, description="Identificador del dispositivo (opcional, por defecto 0)"),
                         fecha: str = Query(None, description="Fecha de la solicitud en formato 'YYYY-MM-DD HH:MI:SS' (opcional)"),
                         id_campaing: int = Query(..., description="Campaña de la que de la que se van a sacar las categorias y experiencias"),
                         vacios: str = Query('N', description="Indica si se deben incluir contenidos vacíos (S --> sacar vacios también, cualquier otro valor no los saca)")
                         ):
    """ -- DOCUMENTACION --
        Obtiene una lista de contenidos basados en los parámetros proporcionados.

        Este endpoint permite obtener una lista delos contenidos relacionadas con las semillas o expedientes que pertenecen
        a las categorías de una campaña.

        Parámetros:
        -----------
        id_App : int
            Identificador de la aplicación.
        user : str
            Nombre del usuario que realiza la solicitud.
        ret_code : int
            Código de retorno inicial.
        ret_txt : str
            Texto descriptivo del estado inicial.
        id_idioma : int, opcional
            Identificador del idioma (opcional, por defecto 0: Todos los coge para el primer idioma que exista o si hay un contenido que valga para todos los idiomas).
        id_dispositivo : int, opcional
            Identificador del dispositivo (opcional, por defecto 0: Para el primer dispositivo que encuentre contenido o el que valga para todos).
        fecha : str, opcional
            Fecha de la solicitud en formato 'YYYY-MM-DD HH:MI:SS' (opcional).
            Si no se proporciona, se utiliza la fecha y hora actuales.
        id_campaing : int
            Campaña de la que de la que se van a sacar las categorias y experiencias
        vacios : str
            Indica si se deben incluir contenidos vacíos (S --> sacar vacios también, cualquier otro valor no los saca).

        Retorna:
        --------
        ListaContenidosResponse
            - Si ret_code = 0 Ok
                - lista con el json de los contenidos
            - ret_code < 0 Ko. 
                - ret_txt: Mensaje de error

        Excepciones:
        ------------
        MadreException
            Se lanza si ocurre un error de aplicación específico con un código de error negativo.
        HTTPException
            Se lanza si ocurre cualquier otro tipo de error no controlado durante la ejecución.

        Ejemplo de Uso:
        ---------------
        ```
        response = cnt_contenidos(id_App=1, user="usuario", ret_code=0, ret_txt="Inicio", id_idioma=1, id_dispositivo=2, fecha="2024-08-21 12:00:00", id_campaing=123, vacios="N")
        print(response.lista)
        ```

        Notas:
        ------
        - Si no se proporciona la fecha, se utilizará la fecha y hora actuales.
        - La función maneja excepciones específicas y genéricas, devolviendo los códigos de error adecuados.
    """
    try:
        if not fecha:
            # Si la variable es None o está vacía, asignar la fecha y hora actuales
            fecha_hora_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        else:
            # Si la variable ya tiene un valor, mantenerlo
            fecha_hora_actual = fecha

        infoTrans = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt)

        param = [infoTrans, id_idioma, id_dispositivo, fecha_hora_actual, id_campaing, vacios]

        resultado = db.obtener_cnt_exp_por_cat(param = param)

        # if resultado['ret_code'] != 0:
        if resultado.ret_code < 0:
            raise MadreException({"ret_code": resultado.ret_code, "ret_txt": resultado.ret_txt}, 400)

        return ListaContenidosResponse(codigo_error=resultado.ret_code, mensaje=resultado.ret_txt, lista=resultado.resultados)
    
    except MadreException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
@router.get("/cnt_exp_centros", response_model=ListaContenidosResponse)
async def cnt_exp_centros(id_App: int = Query(..., description="Identificador de la aplicación"),
                         user: str = Query(..., description="Nombre del usuario que realiza la solicitud"),
                         ret_code: int = Query(..., description="Código de retorno inicial"),
                         ret_txt: str = Query(..., description="Texto descriptivo del estado inicial"),
                         id_idioma: int = Query(0, description="Identificador del idioma (opcional, por defecto 0)"),
                         id_dispositivo: int = Query(0, description="Identificador del dispositivo (opcional, por defecto 0)"),
                         fecha: str = Query(None, description="Fecha de la solicitud en formato 'YYYY-MM-DD HH:MI:SS' (opcional)"),
                         id_semilla: int = Query(..., description="Semilla de la que queremos sacar los centros"),
                         vacios: str = Query('N', description="Indica si se deben incluir contenidos vacíos (S --> sacar vacios también, cualquier otro valor no los saca)")
                         ):
    """ -- DOCUMENTACION --
        Obtiene una lista de contenidos basados en los parámetros proporcionados.

        Este endpoint permite obtener una lista delos contenidos relacionadas con las semillas o expedientes que pertenecen
        a las categorías de una campaña.

        Parámetros:
        -----------
        id_App : int
            Identificador de la aplicación.
        user : str
            Nombre del usuario que realiza la solicitud.
        ret_code : int
            Código de retorno inicial.
        ret_txt : str
            Texto descriptivo del estado inicial.
        id_idioma : int, opcional
            Identificador del idioma (opcional, por defecto 0: Todos los coge para el primer idioma que exista o si hay un contenido que valga para todos los idiomas).
        id_dispositivo : int, opcional
            Identificador del dispositivo (opcional, por defecto 0: Para el primer dispositivo que encuentre contenido o el que valga para todos).
        fecha : str, opcional
            Fecha de la solicitud en formato 'YYYY-MM-DD HH:MI:SS' (opcional).
            Si no se proporciona, se utiliza la fecha y hora actuales.
        id_campaing : int
            Campaña de la que de la que se van a sacar las categorias y experiencias
        vacios : str
            Indica si se deben incluir contenidos vacíos (S --> sacar vacios también, cualquier otro valor no los saca).

        Retorna:
        --------
        ListaContenidosResponse
            - Si ret_code = 0 Ok
                - lista con el json de los contenidos
            - ret_code < 0 Ko. 
                - ret_txt: Mensaje de error

        Excepciones:
        ------------
        MadreException
            Se lanza si ocurre un error de aplicación específico con un código de error negativo.
        HTTPException
            Se lanza si ocurre cualquier otro tipo de error no controlado durante la ejecución.

        Ejemplo de Uso:
        ---------------
        ```
        response = cnt_contenidos(id_App=1, user="usuario", ret_code=0, ret_txt="Inicio", id_idioma=1, id_dispositivo=2, fecha="2024-08-21 12:00:00", id_campaing=123, vacios="N")
        print(response.lista)
        ```

        Notas:
        ------
        - Si no se proporciona la fecha, se utilizará la fecha y hora actuales.
        - La función maneja excepciones específicas y genéricas, devolviendo los códigos de error adecuados.
    """
    try:
        if not fecha:
            # Si la variable es None o está vacía, asignar la fecha y hora actuales
            fecha_hora_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        else:
            # Si la variable ya tiene un valor, mantenerlo
            fecha_hora_actual = fecha

        infoTrans = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt)

        param = [infoTrans, id_idioma, id_dispositivo, fecha_hora_actual, id_semilla, vacios]

        resultado = db.obtener_cnt_exp_centros(param = param)

        # if resultado['ret_code'] != 0:
        if resultado.ret_code < 0:
            raise MadreException({"ret_code": resultado.ret_code, "ret_txt": resultado.ret_txt}, 400)

        return ListaContenidosResponse(codigo_error=resultado.ret_code, mensaje=resultado.ret_txt, lista=resultado.resultados)
    
    except MadreException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))








































#----------------------------------------------------------------------------------
@router.get("/seleccionar_centro")
#----------------------------------------------------------------------------------
def seleccionar_centro():

    return  {"message": "Ahora hay que ver como sacar valores de verdad de seleccionar_centro!!"}

#----------------------------------------------------------------------------------
@router.get("/canjear")
#----------------------------------------------------------------------------------
def canjear():

    return  {"message": "Ahora hay que ver como sacar valores de verdad de canjear!!"}

#----------------------------------------------------------------------------------
@router.get("/volver_a_enviar")
#----------------------------------------------------------------------------------
def volver_a_enviar():

    return  {"message": "Ahora hay que ver como sacar valores de verdad de volver_a_enviar!!"}
