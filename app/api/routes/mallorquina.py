from fastapi import APIRouter, HTTPException, Query
from datetime import datetime

import pyodbc

from app import mi_libreria as mi
# mias
import app.services.mallorquina.sync_data as sync_data
import app.services.mallorquina.consulta_caja as consulta_caja
import app.services.mallorquina.arqueo_caja as arqueo_caja
import app.services.mallorquina.convierte_excel as convierte_excel

from app.utils.functions import graba_log
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
        donde = "Lo estoy ejecutando"
        resultado = []

        donde = f"infoTrans: {id_App} - {user} - {ret_code} - {ret_txt}"
        infoTrans = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, parametros=[])

        donde = "Llamando a sync_data.recorre_tiendas"
        resultado = sync_data.recorre_tiendas(param = infoTrans)

        if resultado.ret_code < 0:
            raise MadreException({"ret_code": resultado.ret_code, "ret_txt": resultado.ret_txt}, 400)

        donde = f"Resultado: {type(resultado.resultados)}"
        resultado.resultados = resultado.resultados or []
        return resultado 
    
    except MadreException as e:
        graba_log({"ret_code": -1, "ret_txt": f"{donde}"}, "MadreException mll_sync_todo", e)
        raise HTTPException(status_code=500, detail={"ret_code": resultado.ret_code,
                                                     "ret_txt": resultado.ret_txt,
                                                     "error": str(e)
                                                    }
                           ) 
    except Exception as e:
        graba_log({"ret_code": -1, "ret_txt": f"{donde}"}, "Exception mll_sync_todo", e)
        raise HTTPException(status_code=500, detail={"ret_code": resultado.ret_code,
                                                     "ret_txt": resultado.ret_txt,
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
        donde = "estoy ejecutando mll_consultas"
        resultado = []

        if not fecha:
            # Si la variable es None o está vacía, asignar la fecha y hora actuales
            fecha = datetime.now().strftime('%Y-%m-%d')

        donde = f"infoTrans: {id_App} - {user} - {ret_code} - {ret_txt} - {fecha}"
        infoTrans = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, parametros=[fecha])

        donde = "Llamando a consulta_caja.recorre_consultas_tiendas"
        resultado = consulta_caja.recorre_consultas_tiendas(param = infoTrans)

        donde = f"Retorno: {resultado.ret_code}"
        if resultado.ret_code < 0:
            raise MadreException({"ret_code": resultado.ret_code, "ret_txt": resultado.ret_txt}, 400)

        donde = f"Resultado: {type(resultado.resultados)}"
        resultado.resultados = resultado.resultados or []
        return resultado 
    
    except MadreException as e:
        graba_log({"ret_code": -1, "ret_txt": f"{donde}"}, "MadreException mll_consultas", e)
        raise HTTPException(status_code=500, detail={"ret_code": resultado.ret_code,
                                                "ret_txt": resultado.ret_txt,
                                                "error": str(e)
                                            }
                           )
    except Exception as e:
        graba_log({"ret_code": -1, "ret_txt": f"{donde}"}, "Exception mll_consultas", e)
        raise HTTPException(status_code=500, detail={"ret_code": resultado.ret_code,
                                                     "ret_txt": resultado.ret_txt,
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
        donde = "estoy ejecutando mll_arqueo_caja"

        if not fecha:
            # Si la variable es None o está vacía, asignar la fecha y hora actuales
            fecha = datetime.now().strftime('%Y-%m-%d')

        donde = f"infoTrans: {id_App} - {user} - {ret_code} - {ret_txt} - {fecha}"
        resultado = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, parametros=[fecha])

        donde = "Llamada a arqueo_caja.proceso"
        resultado = arqueo_caja.proceso(param = resultado)
        
        donde = f"Retorno: {resultado.ret_code}"
        if isinstance(resultado, pyodbc.Row):
            donde = 'el principal'
            resultado = dict(resultado)  # Convertir a diccionario
        elif isinstance(resultado, list) and isinstance(resultado[0], pyodbc.Row):
            donde = 'es una lista y tiene uan instancia'
            resultado = [dict(row) for row in resultado]  # Convertir cada fila a diccionario
        if resultado.ret_code < 0:
            donde = f"resultado.ret_code: {resultado.ret_code}"

        donde = f"Resultado: {type(resultado.resultados)}"
        if resultado.resultados:
            print('--------------------')
            for idx, item in enumerate(resultado.resultados):
                print(f"Item {idx}: {type(item)} - {item}")
            print('--------------------')


        donde = f"Retornando: {type(resultado.resultados)}"
        resultado.resultados = resultado.resultados or []
        return resultado 
    
    except MadreException as e:
        graba_log({"ret_code": -1, "ret_txt": f"{donde}"}, "MadreException mll_arqueo_caja", e)
        raise HTTPException(status_code=500, detail={"ret_code": resultado.ret_code,
                                                "ret_txt": resultado.ret_txt,
                                                "error": str(e)
                                            }
                           ) 
    except Exception as e:
        graba_log({"ret_code": -1, "ret_txt": f"{donde}"}, "Exception mll_arqueo_caja", e)
        raise HTTPException(status_code=500, detail={"ret_code": resultado.ret_code,
                                                     "ret_txt": resultado.ret_txt,
                                                     "error": str(e)
                                                    }
            )
    

#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
@router.get("/mll_convierte_excel", response_model=InfoTransaccion)
async def mll_convierte_excel(id_App: int = Query(..., description="Identificador de la aplicación"),
                        user: str = Query(..., description="Nombre del usuario que realiza la solicitud"),
                        ret_code: int = Query(..., description="Código de retorno inicial"),
                        ret_txt: str = Query(..., description="Texto descriptivo del estado inicial"),
                        origen_path: str = Query(..., description="Fichero origen"),
                        output_path: str = Query(..., description="Fichero destino")
                       ):

    try:
        donde = "Inicio"
        resultado = []
        print("")
        print("estoy ejecutando mll_convierte_excel")
        print("")

        donde = f"infoTrans: {id_App} - {user} - {ret_code} - {ret_txt} - {origen_path} - {output_path}"
        infoTrans = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, parametros=[origen_path, output_path])

        donde = "Llamada a convierte_excel"
        resultado = convierte_excel.proceso(param = infoTrans)

        donde = f"Retorno: {resultado.ret_code}"
        if resultado.ret_code < 0:
            raise MadreException({"ret_code": resultado.ret_code, "ret_txt": resultado.ret_txt}, 400)

        resultado.resultados = resultado.resultados or []
        return resultado 
    
    except MadreException as e:
        graba_log({"ret_code": -1, "ret_txt": f"{donde}"}, "MadreException mll_convierte_excel", e)
        raise HTTPException(status_code=500, detail={"ret_code": resultado.ret_code,
                                                     "ret_txt": resultado.ret_txt,
                                                     "error": str(e)
                                                    }
                           )
        
    except Exception as e:
        graba_log({"ret_code": -1, "ret_txt": f"{donde}"}, "Excepción mll_convierte_excel", e)
        raise HTTPException(status_code=500, detail={"ret_code": resultado.ret_code,
                                                     "ret_txt": resultado.ret_txt,
                                                     "error": str(e)
                                                    }
            )
      