from fastapi import APIRouter, HTTPException, Query
from datetime import datetime

# mias
from app.api.schemas.url import ValidaUrlResponse
from app.services.db.mysql import db_valida_url, db_obtener_contenidos
from app.api.schemas.contenido import ListaContenidosResponse
from app.utils.mis_excepciones import MadreException
from app.utils.InfoTransaccion import InfoTransaccion

# PRUEBAS
from app.api.schemas.precodigo import PrecodigoRequest 
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
               fecha: str = Query(None, description="Fecha de la solicitud en formato 'YYYY-MM-DD HH:MI:SS'"),
               id_frontal: int = Query(None, description="OUT. Retorna ID del frontal"),
               id_cat: int = Query(None, description="OUT. Retorna ID de la categoría")
               ):
    """DOCUMENTACION
        Valida una URL específica contra ciertos parámetros y devuelve un resultado.

        Esta función recibe varios parámetros relacionados con la aplicación y el usuario, 
        junto con una URL para validar. Realiza una llamada a la base de datos para ejecutar 
        el procedimiento `db_valida_url` y devuelve el resultado de la validación.

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
    
    resultado = db_valida_url(param = param)

    if resultado.ret_code < 0:
        raise HTTPException(status_code=500, detail= {"ret_code": resultado.ret_code,
                                                      "ret_txt": resultado.ret_txt
                                                     }
                           )

    return ValidaUrlResponse(codigo_error=resultado.ret_code, mensaje=resultado.ret_txt, datos=resultado.resultados)
    

#----------------------------------------------------------------------------------
@router.get("/cnt_contenidos", response_model=ListaContenidosResponse)
#----------------------------------------------------------------------------------
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
    """ DOCUMENTACION
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
                 
        resultado = db_obtener_contenidos(param = param)

        # if resultado['ret_code'] != 0:
        if resultado.ret_code < 0:
            raise MadreException({"ret_code": resultado.ret_code,"ret_txt": resultado.ret_txt}, 400)

        return ListaContenidosResponse(codigo_error=resultado.ret_code, mensaje=resultado.ret_txt, lista=resultado.resultados)
    

    except MadreException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))







































#----------------------------------------------------------------------------------
'''
    Ejemplos de llamada:
        curl -X POST "http://localhost:8000/valida_precodigo" -H "Content-Type: application/json" -d '{"codigo": "abc123", "usuario_id": 42}'
        Thunder Client: http://localhost:8000/valida_precodigo
            En el Body, formato JSON: 
                {"codigo": "abc123",
                "usuario_id": 42
                }
        
    Se implementa como post porque así adminte datos en el body
'''
@router.post("/valida_precodigo")
#----------------------------------------------------------------------------------
def valida_precodigo(request: PrecodigoRequest):

    # Lógica para validar el precódigo
    if len(request.codigo) < 3:
        raise HTTPException(status_code=400, detail="El código es demasiado corto.")

    return {"message": f"Código {request.codigo} es válido para el usuario {request.usuario_id}."}


#----------------------------------------------------------------------------------
@router.get("/lista_centros", response_model=ListaCentrosResponse)
#----------------------------------------------------------------------------------
async def lista_centros():
    try:
        resultado = obtener_lista_centros()

        if resultado['ret_code'] != 0:
            raise MadreException({"ret_code": resultado['ret_code'],"ret_txt": resultado['ret_txt']}, 400)

        return ListaCentrosResponse(codigo_error=resultado['ret_code'], mensaje=resultado['ret_txt'], lista=resultado['datos'])
    

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
