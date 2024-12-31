from fastapi import APIRouter, HTTPException, Query
from datetime import datetime

# mias
import app.services.mallorquina.sync_data as sync_data
import app.services.mallorquina.consulta_caja as consulta_caja
import app.services.mallorquina.arqueo_caja as arqueo_caja
import app.services.mallorquina.arqueo_caja_info as arqueo_caja_info
import app.services.mallorquina.tarifas_a_TPV as tarifas_a_TPV

from app.utils.functions import graba_log, imprime
from app.utils.mis_excepciones import MadreException
from app.utils.InfoTransaccion import InfoTransaccion

# Definimos el router
router = APIRouter()


#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
@router.get("/mll_consultas", response_model=InfoTransaccion)
async def mll_consultas(id_App: int = Query(..., description="Identificador de la aplicación"),
                        user: str = Query(..., description="Nombre del usuario que realiza la solicitud"),
                        ret_code: int = Query(..., description="Código de retorno inicial"),
                        ret_txt: str = Query(..., description="Texto descriptivo del estado inicial"),
                        fecha: str = Query(None, description="Fecha de la solicitud en formato 'YYYY-MM-DD', por defecto la actual"),
                       ):
    param.debug = "Inicio"
    resultado = []

    try:
        if not fecha:
            # Si la variable es None o está vacía, asignar la fecha y hora actuales
            fecha = datetime.now().strftime('%Y-%m-%d')

        param.debug = f"infoTrans: {id_App} - {user} - {ret_code} - {ret_txt} - {fecha}"
        param = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, parametros=[fecha])

        param.debug = "Llamando a consulta_caja.recorre_consultas_tiendas"
        resultado = consulta_caja.recorre_consultas_tiendas(param = param)
        if param.ret_code < 0:
            raise MadreException(param.to_dict())

        param.debug = f"Retornando: {type(resultado)}"
        param.resultados = resultado or []

        return param
    
    except MadreException as e:
        raise MadreException(param.to_dict())
                
    except Exception as e:
        param.error_sistema()
        graba_log({"ret_code": -1, "ret_txt": f"{param.debug}"}, "Excepción mll_consultas", e)
        raise HTTPException(status_code=500, detail={"ret_code": param.ret_code,
                                                     "ret_txt": param.ret_txt,
                                                     "error": str(e)
                                                    }
            ) 


#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
@router.get("/mll_sync_todo", response_model=InfoTransaccion)
async def mll_sync_todo(id_App: int = Query(..., description="Identificador de la aplicación"),
                        user: str = Query(..., description="Nombre del usuario que realiza la solicitud"),
                        ret_code: int = Query(..., description="Código de retorno inicial"),
                        ret_txt: str = Query(..., description="Texto descriptivo del estado inicial"),
                       ):

    try:
        param.debug = "Lo estoy ejecutando"
        resultado = []

        param.debug = f"infoTrans: {id_App} - {user} - {ret_code} - {ret_txt}"
        param = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, parametros=[])

        param.debug = "Llamando a sync_data.recorre_tiendas"
        resultado = sync_data.recorre_tiendas(param = param)

        if param.ret_code < 0:
            raise MadreException(param.to_dict())
        
        param.debug = f"Retornando: {type(resultado)}"
        param.resultados = resultado or []

        return param
    
    except MadreException as e:
        raise MadreException(param.to_dict())
                
    except Exception as e:
        param.error_sistema()
        graba_log({"ret_code": -1, "ret_txt": f"{param.debug}"}, "Excepción mll_sync_todo", e)
        raise HTTPException(status_code=500, detail={"ret_code": param.ret_code,
                                                     "ret_txt": param.ret_txt,
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
    param.debug = "Inicio"
    resultado = []

    try:
        param.debug = f"infoTrans: {id_App} - {user} - {ret_code} - {ret_txt} - {fecha}"
        param = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, parametros=[fecha])

        param.debug = "Llamada a arqueo_caja.proceso"
        resultado = arqueo_caja.proceso(param = param)
        if param.ret_code < 0:
            raise MadreException(param.to_dict())
        
        param.debug = f"Retornando: {type(resultado)}"
        param.resultados = resultado or []

        return param
    
    except MadreException as e:
        raise MadreException(param.to_dict())
                
    except Exception as e:
        param.error_sistema()
        graba_log({"ret_code": -1, "ret_txt": f"{param.debug}"}, "Excepción mll_arqueo_caja", e)
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
        print("------ 0 -------")
        resultado = []

        print("------ 1 -------")
        if not fecha: # si no tiene parametro fecha
            fecha = datetime.now().strftime('%Y-%m-%d')

        param = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, parametros=[fecha, tienda], debug="Inicio")
        param.debug = f"infoTrans: {id_App} - {user} - {ret_code} - {ret_txt} - {fecha} - {tienda}"

        print("------ 2 -------")
        param.debug = "Llamada a arqueo_caja_info.informe"
        resultado = arqueo_caja_info.informe(param = param)
        if param.ret_code < 0:
            raise MadreException(param.to_dict())
        
        print("------ 3 -------")
        param.debug = f"Retornando: {type(resultado)}"
        param.resultados = resultado or []

    except HTTPException as e:
        print("------ 4 -------")
        param.error_sistema()
        imprime(param,"$")
        imprime(["Capturado en nivel 1: Código", e.status_code, "Detalle:", e.detail], "$")
        graba_log(param, "mll_inf_arqueo_caja.HTTPException", e)


    except Exception as e:
        print("------ 5 -------")
        param.error_sistema()
        graba_log(param, "mll_inf_arqueo_caja.Exception", e)

    finally:
        print("------ 6 -------")
        return param  

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
    param = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, parametros=[origen_path, output_path])
    resultado = []
    param.debug = "Inicio"
    
    try:
        param.debug = "Llamada a proceso"
        resultado = tarifas_a_TPV.proceso(param = param)

        if param.ret_code < 0:
            raise MadreException(param.to_dict())

        param.debug = f"Retornando: {type(resultado)}"
        param.resultados = resultado or []
    
    except MadreException as e:
        #raise MadreException(param, status_code=500, detail=param.to_dict() | {"error": e, "traceback":e.__traceback__})
        param.error_sistema()
        graba_log(param, "mll_convierte_tarifas.MadreException", e)
                
    except HTTPException as e:
        param.error_sistema()
        graba_log(param, "mll_convierte_tarifas.HTTPException", e)


    except Exception as e:
        param.error_sistema()
        graba_log(param, "mll_convierte_tarifas.Exception", e)

    finally:
        return param
