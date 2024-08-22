from fastapi import APIRouter, HTTPException, Query
from app.api.schemas.precodigo import PrecodigoRequest 
import json


from fastapi import APIRouter, HTTPException
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
    # is_valid = url.startswith("http")
    
    # if is_valid:
    #     return {"message": f"La URL {url} es válida."}
    # else:
    #     raise HTTPException(status_code=400, detail="URL no válida.")
    try:
        ret_code: int = 0
        ret_txt: str = ""
        datos_str = "" # si llevara información sería en formato json
        
        resultado = valida_url_db(ret_code, ret_txt, url, datos_str)

        print("01", resultado)

        if resultado is None:
            raise HTTPException(status_code=500, detail="Error connecting to database or executing procedure")

        codigo_error = resultado['codigo_error']
        mensaje      = resultado['mensaje']
        # datos      = json.loads(resultado['datos'])
        datos        = resultado['datos']
        print("datos --> ", resultado['datos'])
        
        if codigo_error != 0:
            raise HTTPException(status_code=400, detail=mensaje)

        return ValidaUrlResponse(codigo_error=codigo_error, mensaje=mensaje, datos={})

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None, str(e)
    except Exception as e:
        print(f"Error : {e}")
        return None, str(e)

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
