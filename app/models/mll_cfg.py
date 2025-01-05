from app.config.db_mallorquina import get_db_connection_mysql, close_connection_mysql
from app.utils.mis_excepciones import MadreException
from app.utils.InfoTransaccion import InfoTransaccion
from app.utils.functions import graba_log

#----------------------------------------------------------------------------------------
def obtener_cfg_general(param: InfoTransaccion):
    
    try:
        param.debug ='Inicio'
        conn = get_db_connection_mysql()

        param.debug ='cursor'
        cursor = conn.cursor(dictionary=True)

        param.debug ='select'
        cursor.execute("SELECT * FROM mll_cfg LIMIT 1")

        param.debug ='fetch'
        config = cursor.fetchone()

        if not config.get("ID", False):
            param.registrar_error(ret_txt = f"No se han encontrado datos de configuración: {config['En_Ejecucion']}", debug="obtener_cfg_general.config-ID")
            raise MadreException(param = param)

        return config

    except Exception as e:
        param.error_sistema()
        # {"ret_code": param.ret_code, "ret_txt": param.ret_txt}
        graba_log(param.to_dict(), f"Excepción mll_cfg.obtener_cfg_general", e)
        raise

    finally:
        close_connection_mysql(conn, cursor)


#----------------------------------------------------------------------------------------
# def obtener_configuracion_general():
#         # param = InfoTransaccion(id_App=0, user="Sistema", ret_code=0, ret_txt="Ok")
#         # obtener_cfg_general(param):

#         conn = get_db_connection_mysql()

#         cursor = conn.cursor(dictionary=True)
#         cursor.execute("SELECT * FROM mll_cfg LIMIT 1")
#         config = cursor.fetchone()

#         close_connection_mysql(conn, cursor)
#         return config

#----------------------------------------------------------------------------------------
def actualizar_en_ejecucion(estado):
    conn = get_db_connection_mysql()

    cursor = conn.cursor()
    cursor.execute("UPDATE mll_cfg SET En_Ejecucion = %s", (estado,))
    conn.commit()

    close_connection_mysql(conn, cursor)
