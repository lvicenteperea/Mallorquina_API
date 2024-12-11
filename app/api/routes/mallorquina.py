from fastapi import APIRouter, HTTPException, Query
from datetime import datetime


import pyodbc

# mias
from app.api.schemas.mallorquina import MallorquinaResponse
import app.services.mallorquina.sync_data as sync_data
import app.services.mallorquina.consulta_caja as consulta_caja
import app.services.mallorquina.arqueo_caja as arqueo_caja

from app.utils.mis_excepciones import MadreException
from app.utils.InfoTransaccion import InfoTransaccion

# Definimos el router
router = APIRouter()

#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
@router.get("/mll_sync_todo", response_model=InfoTransaccion)
async def mll_sync_todo(id_App: int = Query(..., description="Identificador de la aplicación"),
                        user: str = Query(..., description="Nombre del usuario que realiza la solicitud"),
                        ret_code: int = Query(..., description="Código de retorno inicial"),
                        ret_txt: str = Query(..., description="Texto descriptivo del estado inicial"),
                       ):

    try:
        print("")
        print("Lo estoy ejecutando")
        print("")
        infoTrans = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, parametros=[])

        resultado = sync_data.recorre_tiendas(param = infoTrans)

        if resultado.ret_code < 0:
            raise MadreException({"ret_code": resultado.ret_code, "ret_txt": resultado.ret_txt}, 400)

        resultado.resultados = resultado.resultados or []
        return resultado 
    
    except MadreException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail={"ret_code": -1,
                                                "ret_txt": "A ver porque ha dado error....",
                                                "error": str(e)
                                            }
                           )
    


#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
@router.get("/mll_consultas", response_model=InfoTransaccion)
async def mll_consultas(id_App: int = Query(..., description="Identificador de la aplicación"),
                        user: str = Query(..., description="Nombre del usuario que realiza la solicitud"),
                        ret_code: int = Query(..., description="Código de retorno inicial"),
                        ret_txt: str = Query(..., description="Texto descriptivo del estado inicial"),
                        fecha: str = Query(None, description="Fecha de la solicitud en formato 'YYYY-MM-DD', por defecto la actual"),
                       ):

    try:
        print("")
        print("estoy ejecutando mll_consultas")
        print("")

        if not fecha:
            # Si la variable es None o está vacía, asignar la fecha y hora actuales
            fecha = datetime.now().strftime('%Y-%m-%d')

        infoTrans = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, parametros=[fecha])
        resultado = consulta_caja.recorre_consultas_tiendas(param = infoTrans)

        if resultado.ret_code < 0:
            raise MadreException({"ret_code": resultado.ret_code, "ret_txt": resultado.ret_txt}, 400)

        resultado.resultados = resultado.resultados or []
        return resultado 
    
    except MadreException as e:
        print("Madre --> ")
        raise e
        
    except Exception as e:
        print("Excepción --> ")
        raise HTTPException(status_code=500, detail={"ret_code": -1,
                                                     "ret_txt": "A ver porque ha dado error....",
                                                     "error": str(e)
                                                    }
            )
    

  

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
        print("")
        print("estoy ejecutando mll_arqueo_caja")
        print("")

        if not fecha:
            # Si la variable es None o está vacía, asignar la fecha y hora actuales
            fecha = datetime.now().strftime('%Y-%m-%d')

        infoTrans = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, parametros=[fecha])
        resultado = arqueo_caja.proceso(param = infoTrans)

        print('--------------------')
        if isinstance(resultado, pyodbc.Row):
            print('el principal')
            resultado = dict(resultado)  # Convertir a diccionario
        elif isinstance(resultado, list) and isinstance(resultado[0], pyodbc.Row):
            print('es una lista y tiene uan instancia')
            resultado = [dict(row) for row in resultado]  # Convertir cada fila a diccionario
        if resultado.ret_code < 0:
            print('resultado.ret_code', resultado.ret_code)

        print(f"Resultado: {type(resultado)}")
        print(f"Resultado.resultados: {type(resultado.resultados)}")
        if resultado.resultados:
            for idx, item in enumerate(resultado.resultados):
                print(f"Item {idx}: {type(item)} - {item}")

        print('--------------------')



        resultado.resultados = resultado.resultados or []
        return resultado 
    
    except MadreException as e:
        print("Madre --> ")
        raise e
        
    except Exception as e:
        print("Excepción --> ")
        raise HTTPException(status_code=500, detail={"ret_code": -1,
                                                     "ret_txt": "A ver porque ha dado error....",
                                                     "error": str(e)
                                                    }
            )
    

  