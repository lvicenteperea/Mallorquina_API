import pymysql

from app.config.db_mallorquina import get_db_connection_mysql, close_connection_mysql
from app.utils.mis_excepciones import MiException
from app.utils.InfoTransaccion import InfoTransaccion

#----------------------------------------------------------------------------------------
def obtener_cfg_general(param: InfoTransaccion):
    
    try:
        param.debug ='Inicio'
        conn_mysql = get_db_connection_mysql()

        param.debug ='cursor'
        # cursor_mysql = conn_mysql.cursor(dictionary=True)
        cursor_mysql = conn_mysql.cursor(pymysql.cursors.DictCursor)

        param.debug ='select'
        cursor_mysql.execute("SELECT * FROM mll_cfg LIMIT 1")

        param.debug ='fetch'
        config = cursor_mysql.fetchone()

        if not config.get("ID", False):
            param.registrar_error(ret_txt = f"No se han encontrado datos de configuración", debug="obtener_cfg_general.config-ID")
            raise MiException(param = param)

        return config

    except Exception as e:
        param.error_sistema(e=e, debug="Excepción mll_cfg.obtener_cfg_general")
        raise

    finally:
        close_connection_mysql(conn_mysql, cursor_mysql)

#----------------------------------------------------------------------------------------
def actualizar_en_ejecucion(param: InfoTransaccion, estado: int):

    try:
        conn_mysql = get_db_connection_mysql()

        # cursor_mysql = conn_mysql.cursor(dictionary=True)
        cursor_mysql = conn_mysql.cursor(pymysql.cursors.DictCursor)
        cursor_mysql.execute("UPDATE mll_cfg SET En_Ejecucion = %s", (estado,))
        conn_mysql.commit()

    except Exception as e:
        param.error_sistema(e=e, debug="Excepción mll_cfg.obtener_cfg_general")
        raise

    finally:
        close_connection_mysql(conn_mysql, cursor_mysql)
