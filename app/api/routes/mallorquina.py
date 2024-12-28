from fastapi import APIRouter, HTTPException, Query
from datetime import datetime

from app import mi_libreria as mi
# mias
import app.services.mallorquina.sync_data as sync_data
import app.services.mallorquina.consulta_caja as consulta_caja
import app.services.mallorquina.arqueo_caja as arqueo_caja
import app.services.mallorquina.arqueo_caja_info as arqueo_caja_info
import app.services.mallorquina.tarifas_a_TPV as tarifas_a_TPV

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
        donde = f"infoTrans: {id_App} - {user} - {ret_code} - {ret_txt} - {fecha}"
        param = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, parametros=[fecha])

        donde = "Llamada a arqueo_caja.proceso"
        resultado = arqueo_caja.proceso(param = param)
        
        donde = f"Retornando: {type(resultado)}"
        param.resultados = resultado or []

        return param
    
    except MadreException as e:
        graba_log({"ret_code": -1, "ret_txt": f"{donde}"}, "MadreException mll_arqueo_caja", e)
        raise HTTPException(status_code=500, detail={"ret_code": param.ret_code,
                                                "ret_txt": param.ret_txt,
                                                "error": str(e)
                                            }
                           ) 
    except Exception as e:
        graba_log({"ret_code": -1, "ret_txt": f"{donde}"}, "Exception mll_arqueo_caja", e)
        raise HTTPException(status_code=500, detail={"ret_code": param.ret_code,
                                                     "ret_txt": param.ret_txt,
                                                     "error": str(e)
                                                    }
            )
    

#----------------------------------------------------------------------------------
'''
SELECT * FROM mallorquina.mll_rec_ventas_diarias;
SELECT * FROM mallorquina.mll_rec_ventas_medio_pago;

SELECT 
    vd.id_tienda,
    t.nombre Tienda,
    vd.id_tpv,
    tpv.descripcion Nombre_TPV,
    vd.fecha,
    vd.cierre_tpv_id,
    vd.cierre_tpv_desc,
    vmp.id_medios_pago,
    mp.nombre Nombre_MdP,
    SUM(vmp.ventas) AS total_ventas,
    SUM(vmp.operaciones) AS total_operaciones
FROM mll_rec_ventas_diarias vd
     JOIN  mll_rec_ventas_medio_pago vmp ON vd.id = vmp.id_ventas_diarias
LEFT JOIN mll_cfg_bbdd t         ON vd.id_tienda = t.id
LEFT JOIN tpv_puestos_facturacion tpv        ON vd.id_tpv = tpv.id_puesto and vd.id_tienda = tpv.Origen_BBDD
LEFT JOIN mll_mae_medios_pago mp ON vmp.id_medios_pago = mp.id
GROUP BY 
    vd.id_tienda,
    t.nombre,
    vd.id_tpv,
    tpv.descripcion,
    vd.fecha,
    vd.cierre_tpv_id,
    vd.cierre_tpv_desc,
    vmp.id_medios_pago,
    mp.nombre;
'''
#----------------------------------------------------------------------------------
@router.get("/mll_inf_arqueo_caja", response_model=InfoTransaccion)
async def mll_inf_arqueo_caja(id_App: int = Query(..., description="Identificador de la aplicación"),
                              user: str = Query(..., description="Nombre del usuario que realiza la solicitud"),
                              ret_code: int = Query(..., description="Código de retorno inicial"),
                              ret_txt: str = Query(..., description="Texto descriptivo del estado inicial"),
                              fecha: str = Query(None, description="Fecha de la solicitud en formato 'YYYY-MM-DD', por defecto la actual"),
                              tienda: int = Query(0, description="BBDD/Tienda (mll_cfg_bbdd) de la que queremos la información, 0 --> Todas"),
                             ):

    try:
        donde = f"infoTrans: {id_App} - {user} - {ret_code} - {ret_txt} - {fecha} - {tienda}"
        if not fecha: # si no tiene parametro fecha
            fecha = datetime.now().strftime('%Y-%m-%d')

        param = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, parametros=[fecha, tienda])

        donde = "Llamada a arqueo_caja_info.informe"
        resultado = arqueo_caja_info.informe(param = param)
        
        donde = f"Retornando: {type(resultado)}"
        param.resultados = resultado or []

        return param
    
    except MadreException as e:
        graba_log({"ret_code": -1, "ret_txt": f"{donde}"}, "MadreException mll_inf_arqueo_caja", e)
        raise HTTPException(status_code=400, detail={"ret_code": param.ret_code,
                                                "ret_txt": param.ret_txt,
                                                "error": str(e)
                                            }
                           ) 
    except Exception as e:
        graba_log({"ret_code": -1, "ret_txt": f"{donde}"}, "Exception mll_inf_arqueo_caja", e)
        raise HTTPException(status_code=500, detail={"ret_code": param.ret_code,
                                                     "ret_txt": param.ret_txt,
                                                     "error": str(e)
                                                    }
            )
    

#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
@router.get("/mll_convierte_tarifas", response_model=InfoTransaccion)
async def mll_convierte_tarifas(id_App: int = Query(..., description="Identificador de la aplicación"),
                        user: str = Query(..., description="Nombre del usuario que realiza la solicitud"),
                        ret_code: int = Query(..., description="Código de retorno inicial"),
                        ret_txt: str = Query(..., description="Texto descriptivo del estado inicial"),
                        origen_path: str = Query(..., description="Fichero origen"),
                        output_path: str = Query(..., description="Fichero destino")
                       ):

    donde = "Inicio"
    resultado = []
    donde = f"infoTrans: {id_App} - {user} - {ret_code} - {ret_txt} - {origen_path} - {output_path}"
    param = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, parametros=[origen_path, output_path])
    
    try:
        donde = "Llamada a proceso"
        resultado = tarifas_a_TPV.proceso(param = param)
        if param.ret_code < 0:
            raise MadreException(param.to_dict())

        donde = f"Retornando: {type(resultado)}"
        param.resultados = resultado or []
    
        return param
    
    except MadreException as e:
        raise MadreException(param.to_dict())
                
    except Exception as e:
        graba_log({"ret_code": -1, "ret_txt": f"{donde}"}, "Excepción mll_convierte_tarifas", e)
        raise HTTPException(status_code=500, detail={"ret_code": param.ret_code,
                                                     "ret_txt": param.ret_txt,
                                                     "error": str(e)
                                                    }
            )
      