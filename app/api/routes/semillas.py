from fastapi import APIRouter, HTTPException, Query
from datetime import datetime

# mias
from app.api.schemas.url import ValidaUrlResponse
from app.services.db.mysql import valida_url_db, obtener_contenidos_db, obtener_lista_centros
from app.api.schemas.contenido import ListaContenidosResponse
from app.utils.mis_excepciones import MadreException


# PRUEBAS
from app.api.schemas.precodigo import PrecodigoRequest 
from app.api.schemas.centro import ListaCentrosResponse


# Definimos el router
router = APIRouter()

#----------------------------------------------------------------------------------
'''
    Ejemplos de llamada:
        Thunder Client: http://localhost:8000/valida_url?url=https://ejemplo.com
        curl -X GET "http://localhost:8000/valida_url?url=https://ejemplo.com"
    la llamada a BBDD es:
        Call  w_exp_valida_url( @v_idApp	, @v_user	, @v_retNum	, @v_retTxt	, @v_url	, @v_fecha	, @v_id_frontal	, @v_id_cat	);
        
'''
@router.get("/valida_url")
#----------------------------------------------------------------------------------
def valida_url(id_App: int = Query(...),
               user: str = Query(...),
               ret_code: int = Query(...), 
               ret_txt: str = Query(...), 
               url: str = Query(...), 
               fecha: str = Query(...),         # 'YYYY-MM-DD HH:MI:SS
               id_frontal: int = Query(None), 
               id_cat: int = Query(None)  
               ):

    param = [id_App, user, ret_code, ret_txt, url, fecha, id_frontal, id_cat]
    
    resultado = valida_url_db(param = param)

    codigo_error = resultado[2]
    mensaje      = resultado[3]
    id_frontal   = resultado[6]
    datos        = {"id_App":  resultado[0],
                    "user":  resultado[1],
                    "ret_code":  codigo_error,
                    "ret_txt":  mensaje,
                    "url":  resultado[4],
                    "fecha":  resultado[5],         # 'YYYY-MM-DD HH:MI:SS
                    "id_frontal":  id_frontal, 
                    "id_cat":  resultado[7]
                    }
    


    if codigo_error < 0:
        raise HTTPException(status_code=500, detail= {"ret_code": codigo_error,
                                                      "ret_txt": mensaje,
                                                      "datos": datos
                                                     }
                           )

    return ValidaUrlResponse(codigo_error=codigo_error, mensaje=mensaje, datos=datos)
    

#----------------------------------------------------------------------------------
@router.get("/cnt_contenidos", response_model=ListaContenidosResponse)
#----------------------------------------------------------------------------------
async def cnt_contenidos(id_App: int = Query(...),
                         user: str = Query(...),
                         ret_code: int = Query(...), 
                         ret_txt: str = Query(...), 
                         id_idioma: int = Query(0), 
                         id_dispositivo: int = Query(0), 
                         fecha: str = Query(None),         # 'YYYY-MM-DD HH:MI:SS
                         id_cnt: int = Query(...), 
                         vacios: str = Query('S')  
               ):
    try:
        if not fecha:
            # Si la variable es None o está vacía, asignar la fecha y hora actuales
            fecha_hora_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        else:
            # Si la variable ya tiene un valor, mantenerlo
            fecha_hora_actual = fecha

        param = [id_App, user, ret_code, ret_txt, id_idioma, id_dispositivo, fecha_hora_actual, id_cnt, vacios]
                 
        resultado = obtener_contenidos_db(param)

        if resultado['ret_code'] != 0:
            raise MadreException({"ret_code": resultado['ret_code'],"ret_txt": resultado['ret_txt']}, 400)

        return ListaContenidosResponse(codigo_error=resultado['ret_code'], mensaje=resultado['ret_txt'], lista=resultado['datos'])
    

    except MadreException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))










































#----------------------------------------------------------------------------------
'''
    Ejemplos de llamada:
        Thunder Client: http://localhost:8000/valida_url?url=https://ejemplo.com
        curl -X GET "http://localhost:8000/valida_url?url=https://ejemplo.com"
'''
@router.get("/valida_url_prueba")
#----------------------------------------------------------------------------------
def valida_url(url: str = Query(...)):
    is_valid = url.startswith("http")
    
    if not (is_valid):
        # raise HTTPException(status_code=400, detail="URL no válida.")
        return ValidaUrlResponse(codigo_error=-1, mensaje="URL no válida.", datos={})

    datos_str = "" # si llevara información sería en formato json
    
    # resultado = valida_url_db(ret_code, ret_txt, url, datos_str)
    resultado = valida_url_db(url=url, datos_str=datos_str)
    codigo_error = resultado['ret_code']
    mensaje      = resultado['ret_txt']
    datos        = resultado['datos']

    if codigo_error < 0:
        raise HTTPException(status_code=500, detail= {"ret_code": codigo_error,
                                                      "ret_txt": mensaje,
                                                      "datos": datos
                                                     }
                           )

    return ValidaUrlResponse(codigo_error=codigo_error, mensaje=mensaje, datos=datos)
    


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
