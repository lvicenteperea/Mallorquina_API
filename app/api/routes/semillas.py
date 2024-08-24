from fastapi import APIRouter, HTTPException, Query
from app.api.schemas.precodigo import PrecodigoRequest 
import json
from app.api.schemas.url import ValidaUrlResponse
from app.services.db.mysql import valida_url_db

# Definimos el router
router = APIRouter()

#----------------------------------------------------------------------------------
'''
    Ejemplos de llamada:
        Thunder Client: http://localhost:8000/valida_url?url=https://ejemplo.com
        curl -X GET "http://localhost:8000/valida_url?url=https://ejemplo.com"
'''
@router.get("/valida_url")
#----------------------------------------------------------------------------------
def valida_url(url: str = Query(...)):
    is_valid = url.startswith("http")
    
    if not (is_valid):
        raise HTTPException(status_code=400, detail="URL no válida.")

    ret_code: int = 0
    ret_txt: str = ""
    datos_str = "" # si llevara información sería en formato json
    
    resultado = valida_url_db(ret_code, ret_txt, url, datos_str)
    codigo_error = resultado['ret_code']
    mensaje      = resultado['ret_txt']

    if codigo_error < 0:
        raise HTTPException(status_code=500, detail=mensaje)

    datos = resultado['datos']

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
