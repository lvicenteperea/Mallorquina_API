from fastapi import APIRouter, HTTPException, Query
from datetime import datetime

# mias
import app.services.mallorquina.sync_data as sync_data
import app.services.mallorquina.consulta_caja as consulta_caja
import app.services.mallorquina.arqueo_caja as arqueo_caja
import app.services.mallorquina.arqueo_caja_info as arqueo_caja_info
import app.services.mallorquina.tarifas_a_TPV as tarifas_a_TPV
import app.services.mallorquina.fichas_tecnicas as fichas_tecnicas
import app.services.mallorquina.carga_productos_erp as carga_productos_erp




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

    try:
        resultado = []
        if not fecha:
            # Si la variable es None o está vacía, asignar la fecha y hora actuales
            fecha = datetime.now().strftime('%Y-%m-%d')

        param = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, parametros=[fecha])
        param.debug = f"infoTrans: {id_App} - {user} - {ret_code} - {ret_txt} - {fecha}"

        # --------------------------------------------------------------------------------
        resultado = consulta_caja.recorre_consultas_tiendas(param = param)
        # --------------------------------------------------------------------------------

        param.debug = f"Retornando: {type(resultado)}"
        param.resultados = resultado or []

    except MadreException as e:
        graba_log(param, "mll_sync_todo.MadreException", e)
                
    except HTTPException as e:
        param.error_sistema()
        print("HTTPException", param.ret_code, param.ret_txt)
        graba_log(param, "mll_sync_todo.HTTPException", e)


    except Exception as e:
        param.error_sistema()
        print("Exception", param.ret_code, param.ret_txt)
        graba_log(param, "mll_sync_todo.Exception", e)
    
    finally:
        return param


#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
@router.get("/mll_sync_todo", response_model=InfoTransaccion)
async def mll_sync_todo(id_App: int = Query(..., description="Identificador de la aplicación"),
                        user: str = Query(..., description="Nombre del usuario que realiza la solicitud"),
                        ret_code: int = Query(..., description="Código de retorno inicial"),
                        ret_txt: str = Query(..., description="Texto descriptivo del estado inicial"),
                       ):

    try:
        resultado = []
        param = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, parametros=[])
        param.debug = f"infoTrans: {id_App} - {user} - {ret_code} - {ret_txt}"

        # --------------------------------------------------------------------------------
        resultado = sync_data.recorre_tiendas(param = param)
        # --------------------------------------------------------------------------------

        param.debug = f"Retornando: {type(resultado)}"
        param.resultados = resultado or []

    except MadreException as e:
        graba_log(param, "mll_sync_todo.MadreException", e)
                
    except HTTPException as e:
        param.error_sistema()
        print("HTTPException", param.ret_code, param.ret_txt)
        graba_log(param, "mll_sync_todo.HTTPException", e)


    except Exception as e:
        param.error_sistema()
        print("Exception", param.ret_code, param.ret_txt)
        graba_log(param, "mll_sync_todo.Exception", e)
    
    finally:
        return param
    

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
        resultado = []
        param = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, parametros=[fecha])
        param.debug = f"infoTrans: {id_App} - {user} - {ret_code} - {ret_txt} - {fecha}"

        # --------------------------------------------------------------------------------
        resultado = arqueo_caja.proceso(param = param)
        # --------------------------------------------------------------------------------
        
        param.debug = f"Retornando: {type(resultado)}"
        param.resultados = resultado or []
    
    except MadreException as e:
        graba_log(param, "mll_arqueo_caja.MadreException", e)
                
    except HTTPException as e:
        param.error_sistema()
        print("HTTPException", param.ret_code, param.ret_txt)
        graba_log(param, "mll_arqueo_caja.HTTPException", e)


    except Exception as e:
        param.error_sistema()
        print("Exception", param.ret_code, param.ret_txt)
        graba_log(param, "mll_arqueo_caja.Exception", e)

    finally:
        return param

    

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
        resultado = []
        if not fecha: # si no tiene parametro fecha
            fecha = datetime.now().strftime('%Y-%m-%d')

        param = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, parametros=[fecha, tienda], debug="Inicio")
        param.debug = f"infoTrans: {id_App} - {user} - {ret_code} - {ret_txt} - {fecha} - {tienda}"

        # --------------------------------------------------------------------------------
        resultado = arqueo_caja_info.informe(param = param)
        # --------------------------------------------------------------------------------
                
        param.debug = f"Retornando: {type(resultado)}"
        param.resultados = resultado or []
    
    except MadreException as e:
        graba_log(param, "mll_inf_arqueo_caja.MadreException", e)
                
    except HTTPException as e:
        param.error_sistema()
        graba_log(param, "mll_inf_arqueo_caja.HTTPException", e)

    except Exception as e:
        param.error_sistema()
        graba_log(param, "mll_inf_arqueo_caja.Exception", e)

    finally:
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
    
    try:
        resultado = []
        param = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, parametros=[origen_path, output_path])
        param.debug = f"infoTrans: {id_App} - {user} - {ret_code} - {ret_txt} - {origen_path} - {output_path}"

        # --------------------------------------------------------------------------------
        resultado = tarifas_a_TPV.proceso(param = param)
        # --------------------------------------------------------------------------------

        param.debug = f"Retornando: {type(resultado)}"
        param.resultados = resultado or []
    
    except MadreException as e:
        graba_log(param, "mll_convierte_tarifas.MadreException", e)
                
    except HTTPException as e:
        param.error_sistema()
        graba_log(param, "mll_convierte_tarifas.HTTPException", e)


    except Exception as e:
        param.error_sistema()
        graba_log(param, "mll_convierte_tarifas.Exception", e)

    finally:
        return param


#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
@router.get("/mll_fichas_tecnicas", response_model=InfoTransaccion)
async def mll_fichas_tecnicas(id_App: int = Query(..., description="Identificador de la aplicación"),
                        user: str = Query(..., description="Nombre del usuario que realiza la solicitud"),
                        ret_code: int = Query(..., description="Código de retorno inicial"),
                        ret_txt: str = Query(..., description="Texto descriptivo del estado inicial"),
                        #origen_path: str = Query(..., description="Fichero origen")
                        output_path: str = Query(..., description="Fichero destino")
                       ):
    
    try:
        resultado = []
        param = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, parametros=[output_path])
        param.debug = f"infoTrans: {id_App} - {user} - {ret_code} - {ret_txt} - {output_path}"

        # --------------------------------------------------------------------------------
        resultado = fichas_tecnicas.proceso(param = param)
        # --------------------------------------------------------------------------------

        param.debug = f"Retornando: {type(resultado)}"
        param.resultados = resultado or []
    
    except MadreException as e:
        graba_log(param, "mll_fichas_tecnicas.MadreException", e)
                
    except HTTPException as e:
        param.error_sistema()
        graba_log(param, "mll_fichas_tecnicas.HTTPException", e)


    except Exception as e:
        param.error_sistema()
        graba_log(param, "mll_fichas_tecnicas.Exception", e)

    finally:
        return param

#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
@router.get("/mll_carga_prod_erp", response_model=InfoTransaccion)
async def mll_carga_prod_erp(id_App: int = Query(..., description="Identificador de la aplicación"),
                        user: str = Query(..., description="Nombre del usuario que realiza la solicitud"),
                        ret_code: int = Query(..., description="Código de retorno inicial"),
                        ret_txt: str = Query(..., description="Texto descriptivo del estado inicial"),
                        origen_path: str = Query(..., description="Fichero origen"),
                       ):
    
    try:
        resultado = []
        param = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, parametros=[origen_path])
        param.debug = f"infoTrans: {id_App} - {user} - {ret_code} - {ret_txt} - {origen_path}"

        # --------------------------------------------------------------------------------
        resultado = carga_productos_erp.proceso(param = param)
        # --------------------------------------------------------------------------------

        param.debug = f"Retornando: {type(resultado)}"
        param.resultados = resultado or []
    
    except MadreException as e:
        graba_log(param, "mll_carga_prod_erp.MadreException", e)
                
    except HTTPException as e:
        param.error_sistema()
        graba_log(param, "mll_carga_prod_erp.HTTPException", e)


    except Exception as e:
        param.error_sistema()
        graba_log(param, "mll_fichas_tecnicas.Exception", e)

    finally:
        return param
