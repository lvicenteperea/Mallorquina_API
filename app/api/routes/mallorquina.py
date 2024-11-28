from fastapi import APIRouter, HTTPException, Query
from datetime import datetime

# mias
from app.api.schemas.mallorquina import MallorquinaResponse
import app.services.mallorquina.sync_data as carga
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
        infoTrans = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt)

        param = [infoTrans]

        resultado = carga.recorre_BBDD(param = param)

        if resultado.ret_code < 0:
            raise MadreException({"ret_code": resultado.ret_code, "ret_txt": resultado.ret_txt}, 400)

        return MallorquinaResponse(codigo_error=resultado.ret_code, mensaje=resultado.ret_txt, datos="")
    

    except MadreException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
