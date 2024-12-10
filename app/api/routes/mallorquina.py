from fastapi import APIRouter, HTTPException, Query
from datetime import datetime

# mias
from app.api.schemas.mallorquina import MallorquinaResponse
import app.services.mallorquina.sync_data as sync_data
from app.utils.mis_excepciones import MadreException
from app.utils.InfoTransaccion import InfoTransaccion

# Definimos el router
router = APIRouter()

#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
@router.get("/mll_sync_todo", response_model=MallorquinaResponse)
async def mll_sync_todo(id_App: int = Query(..., description="Identificador de la aplicación"),
                        user: str = Query(..., description="Nombre del usuario que realiza la solicitud"),
                        ret_code: int = Query(..., description="Código de retorno inicial"),
                        ret_txt: str = Query(..., description="Texto descriptivo del estado inicial"),
                       ):

    try:
        print("")
        print("Lo estoy ejecutando")
        print("")
        infoTrans = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt)

        param = [infoTrans]

        resultado = sync_data.recorre_tiendas(param = param)

        if resultado.ret_code < 0:
            raise MadreException({"ret_code": resultado.ret_code, "ret_txt": resultado.ret_txt}, 400)

        return MallorquinaResponse(codigo_error=resultado.ret_code, mensaje=resultado.ret_txt, datos="")

    

    except MadreException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
@router.get("/mll_sync_consultas", response_model=InfoTransaccion)
async def mll_sync_consultas(id_App: int = Query(..., description="Identificador de la aplicación"),
                             user: str = Query(..., description="Nombre del usuario que realiza la solicitud"),
                             ret_code: int = Query(..., description="Código de retorno inicial"),
                             ret_txt: str = Query(..., description="Texto descriptivo del estado inicial"),
                             fecha: str = Query(None, description="Fecha de la solicitud en formato 'YYYY-MM-DD', por defecto la actual"),
                            ):

    try:
        print("")
        print("estoy ejecutando sync_consultas")
        print("")

        if not fecha:
            # Si la variable es None o está vacía, asignar la fecha y hora actuales
            fecha = datetime.now().strftime('%Y-%m-%d')

        infoTrans = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, parametros=[fecha])
        resultado = sync_data.recorre_consultas_tiendas(param = infoTrans)

        if resultado.ret_code < 0:
            raise MadreException({"ret_code": resultado.ret_code, "ret_txt": resultado.ret_txt}, 400)

        resultado.resultados = resultado.resultados or []
        return resultado 
    
    except MadreException as e:
        print("Madre --> ")
        raise e
        
    except Exception as e:
        print("Excepción --> ")
        raise HTTPException(status_code=500, detail={"ret_code": -111,
                                                     "ret_txt": "A ver porque ha dado error....",
                                                     "error": str(e)
                                                    }
            )
    

  
'''
#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
@router.get("/mll_arqueo_diario", response_model=InfoTransaccion)
async def mll_arqueo_diario(id_App: int = Query(..., description="Identificador de la aplicación"),
                             user: str = Query(..., description="Nombre del usuario que realiza la solicitud"),
                             ret_code: int = Query(..., description="Código de retorno inicial"),
                             ret_txt: str = Query(..., description="Texto descriptivo del estado inicial"),
                             fecha: str = Query(None, description="Fecha de la solicitud en formato 'YYYY-MM-DD HH:MI:SS', por defecto la actual"),
                            ):

    try:
        print("")
        print("estoy ejecutando mll_arqueo_diario")
        print("")

        if not fecha:
            # Si la variable es None o está vacía, asignar la fecha y hora actuales
            fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        infoTrans = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, parametros=[fecha])
        resultado = sync_data.recorre_consultas_tiendas(param = infoTrans)

        if resultado.ret_code < 0:
            raise MadreException({"ret_code": resultado.ret_code, "ret_txt": resultado.ret_txt}, 400)

        resultado.resultados = resultado.resultados or []
        return resultado 

    except MadreException as e:
        raise e
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"ret_code": -111,
                                                     "ret_txt": "A ver porque ha dado error....",
                                                     "error": str(e)
                                                    }
            )
'''    

  

