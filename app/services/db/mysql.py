from fastapi import HTTPException
import mysql.connector
from mysql.connector import Error
import json

from app.utils.InfoTransaccion import InfoTransaccion
from app.utils.functions import expande_lista
from app.config.settings import settings

#----------------------------------------------------------------------------------------
def get_db_connection():
#----------------------------------------------------------------------------------------
    try:
        connection = mysql.connector.connect(
            host=settings.MYSQL_DB_URL,
            user=settings.MYSQL_DB_USER,
            password=settings.MYSQL_DB_PWD,
            database=settings.MYSQL_DB_DATABASE
        )
        return connection
    
    except Error as e:
        raise HTTPException(status_code=400, detail= {"ret_code": -1,
                                                      "ret_txt": str(e),
                                                     }
                           )

#----------------------------------------------------------------------------------------
def get_db_close_connection(conn, cursor):
#----------------------------------------------------------------------------------------
    if conn.is_connected():
        if isinstance(cursor, mysql.connector.cursor_cext.CMySQLCursor):
            cursor.close()
        conn.close()


'''#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def call_proc_bbdd_param(procedimiento:str, param) -> InfoTransaccion:
    """
        Este método ejecuta un procedimiento almacenado en la base de datos con los parámetros 
        proporcionados, y devuelve una instancia de `InfoTransaccion` que contiene 
            - Variables de salida

        Parámetros:
        -----------
        procedimiento : str
            El nombre del procedimiento almacenado que se va a ejecutar.
        param : lista
            Lista de paramostros que debe coincidir con los del procedimiento de BBDD
            Si hay un elemneto de la lista de tipo `InfoTransaccion` los expande en la lista.

        Retorna:
        --------
        InfoTransaccion
            Una instancia de `InfoTransaccion` que contiene:
            - `id_App`: Identificador de la aplicación devuelto por el procedimiento.
            - `user`: El usuario asociado a la solicitud devuelto por el procedimiento.
            - `ret_code`: Código de retorno del procedimiento (0 indica éxito, valores negativos indican error).
            - `ret_txt`: Texto de retorno con un mensaje o descripción devuelto por el procedimiento.

        Excepciones:
        ------------
        HTTPException
            Se lanza si ocurre un error durante la ejecución del procedimiento almacenado.

        Ejemplo de Uso:
        ---------------
        ```
        info_trans = call_proc_bbdd_param("mi_procedimiento", mi_param)
        if info_trans.ret_code == 0:
            print("Procedimiento ejecutado con éxito")
        else:
            print("Error:", info_trans.ret_txt)
        ```

        Notas:
        ------
        - El método expande los parámetros proporcionados usando `expande_lista` para adaptarlos a la llamada al 
        procedimiento almacenado.
        - El método maneja la conexión a la base de datos y garantiza su cierre incluso si ocurre una excepción.
    """
    connection = get_db_connection()

    try:
        # Crear una nueva lista para almacenar los elementos expandidos, ya que param debe trar un tipo InfoTransaccion
        param_expanded = expande_lista(param)

        cursor = connection.cursor()
        response = cursor.callproc(procedimiento, param_expanded)
        print("A ver que saca call_proc_bbdd_param", response)
        return InfoTransaccion(id_App=response[0], user=response[1], ret_code=response[2], ret_txt=response[3])

    except Exception as e:
        print("pasa por aquí")
        raise HTTPException(status_code=400, detail={"ret_code": -3,
                                                     "excepcion": e
                                                    }
                           )

    finally:
        get_db_close_connection(connection, cursor)
'''
#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def call_proc_bbdd(procedimiento:str, param) -> InfoTransaccion:
    """
        Este método ejecuta un procedimiento almacenado en la base de datos, toma los parámetros 
        necesarios, y devuelve una instancia de `InfoTransaccion` que contiene 
            - Variables de salida
            - Recorset retornado por el procedimiento en formato JSON

        Parámetros:
        -----------
        procedimiento : str
            El nombre del procedimiento almacenado que se va a ejecutar.
        param : lista
            Lista de paramostros que debe coincidir con los del procedimiento de BBDD
            Si hay un elemneto de la lista de tipo `InfoTransaccion` los expande en la lista.

        Retorna:
        --------
        InfoTransaccion
            Una instancia de `InfoTransaccion` que contiene:
            - `id_App`: Identificador de la aplicación.
            - `user`: El usuario que hace la solicitud.
            - `ret_code`: Código de retorno del procedimiento (0 indica éxito, valores negativos indican error).
            - `ret_txt`: Texto de retorno con un mensaje o descripción.
            - `resultados`: Si la ejecución es exitosa, contiene los resultados del procedimiento en formato JSON.

        Excepciones:
        ------------
        HTTPException
            Se lanza si ocurre un error durante la ejecución del procedimiento o durante el procesamiento de los resultados.

        Ejemplo de Uso:
        ---------------
        ```
        info_trans = call_proc_bbdd_records("mi_procedimiento", mi_param)
        if info_trans.ret_code == 0:
            print("Procedimiento ejecutado con éxito")
            print("Resultados:", info_trans.resultados)
        else:
            print("Error:", info_trans.ret_txt)
        ```

        Notas:
        ------
        - El método expande los parámetros proporcionados usando `expande_lista` para adaptarlos a la llamada al 
        procedimiento almacenado.
        - Después de la ejecución, se procesan los resultados y se convierten a JSON antes de devolverlos.
        - El método maneja la conexión a la base de datos y garantiza su cierre incluso si ocurre una excepción.
    """
    connection = get_db_connection()
    
    try:

        # Crear una nueva lista para almacenar los elementos expandidos, ya que param debe trar un tipo InfoTransaccion
        param_expanded = expande_lista(param)

        cursor = connection.cursor()
        response = cursor.callproc(procedimiento, param_expanded)

        infoTrans = InfoTransaccion(id_App=response[0], 
                                    user=response[1], 
                                    ret_code=response[2], 
                                    ret_txt=response[3])

        if infoTrans.ret_code < 0:
            return infoTrans
    
        # Asignamos la lista de parametros que son del salida
        infoTrans.set_parametros(response[4:])

        # para convertirlo a JSON el posible record set retornado
        rows = []
        for result in cursor.stored_results():
            columns = [col[0] for col in result.description]  # Obtener nombres de las columnas
            rows = [
                    {col: (val if val is not None else "") for col, val in zip(columns, row)}
                    for row in result.fetchall()
                   ]  # Convertir cada fila en un diccionario, reemplazando None con ""

        # Convertir la lista de diccionarios a JSON
        json_rows = json.dumps(rows)
        infoTrans.set_resultados(json.loads(json_rows))

        return infoTrans

    except Exception as e:
        raise HTTPException(status_code=400, detail={"ret_code": -3,
                                                     "ret_txt": str(e),
                                                     "excepcion": e
                                                    }
                           )
    finally:
        get_db_close_connection(connection, cursor)




#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def db_valida_url(param: list) -> InfoTransaccion:
    return call_proc_bbdd('w_exp_valida_url', param)


'''----------------------------------------------------------------------------------------
w_exp_valida_precodigo( IN v_idApp 				BIGINT  
                      , IN v_user 				VARCHAR(45)         -- Usuario que lanza el procedimiento
                      , INOUT v_retNum 			INT            -- 0 --> OK; <0 --> error;  >0 --> Ok, con algún significado; 2 --> El precodigo ya ha sido canjeado
                      , INOUT v_retTxt 			VARCHAR(4000)  -- Texto en caso de error (v_retNum < 0)
                      , IN	  v_precodigo		VARCHAR(30)
                      , IN  v_fecha 			VARCHAR(19)     -- '%Y-%m-%d %H:%i:%s'
                      , IN  v_url				VARCHAR(400) 	-- LLeva URL o ....
                      , INOUT v_idFrontal		BIGINT			-- ... lleva IdFrontal
                      , OUT v_idCatalogo		BIGINT
                      , OUT v_idCampaign		BIGINT
                      , OUT v_idCanje			BIGINT
                      , OUT v_idParticipante	BIGINT
                      , OUT v_idPrecodigo		BIGINT
                      )
----------------------------------------------------------------------------------------'''
def db_valida_precodigo(param: list) -> InfoTransaccion:
    return call_proc_bbdd('w_exp_valida_precodigo', param)


#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def db_obtener_contenidos(param: list) -> InfoTransaccion:
    return call_proc_bbdd('w_cnt_contenidos', param)


