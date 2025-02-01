from datetime import datetime, timedelta
import json
import re

from app.utils.functions import graba_log, imprime

from app.models.mll_cfg_tablas import obtener_campos_tabla, crear_tabla_destino
from app.models.mll_cfg_bbdd import obtener_conexion_bbdd_origen
from app.config.db_mallorquina import get_db_connection_mysql, close_connection_mysql, get_db_connection_sqlserver, close_connection_sqlserver
from app.models.mll_cfg import obtener_cfg_general, actualizar_en_ejecucion
from app.services.auxiliares.sendgrid_service import enviar_email

from app.utils.InfoTransaccion import InfoTransaccion
from app.utils.mis_excepciones import MadreException


PAGINACION: int = 100

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def recorre_tiendas(param: InfoTransaccion) -> list:
    funcion = "arqueo_caja.proceso"
    param.debug = "Obtener Conf. Gen"
    resultado = []
    conn_mysql = None # para que no de error en el finally
    cursor_mysql = None # para que no de error en el finally

    try:
        config = obtener_cfg_general(param)

        if not config.get("ID", False):
            param.registrar_error(ret_txt=f'No se han encontrado datos de configuración: config["En_Ejecucion"]', debug=f"{funcion}.config-ID")
            raise MadreException(param = param)
                
        if config["En_Ejecucion"]:
                param.registrar_error(ret_txt="El proceso ya está en ejecución.", debug=f"{funcion}.config.en_ejecucion")
                raise MadreException(param = param)

        param.debug = "actualiza ejec 1"
        actualizar_en_ejecucion(param, 1)

        param.debug = "conn. MySql"
        conn_mysql = get_db_connection_mysql()
        cursor_mysql = conn_mysql.cursor(dictionary=True)

        param.debug = "execute cfg_bbdd"
        # cursor_mysql.execute("SELECT * FROM mll_cfg_bbdd where activo= 'S'")
        cursor_mysql.execute("""SELECT a.*, b.stIdEnt, b.Nombre as nombre_entidad, b.id as id_entidad 
                                  FROM mll_cfg_bbdd a
                                 inner join mll_cfg_entidades b on a.id = b.id_bbdd and b.activo = 'S'
                                 where a.activo= 'S'""")
        lista_bbdd = cursor_mysql.fetchall()

        for bbdd in lista_bbdd:
            imprime(["Procesando TIENDA:", json.loads(bbdd['Conexion'])['database'], bbdd["ID"], bbdd['stIdEnt'], bbdd['nombre_entidad'], bbdd['id_entidad']], "-")
            

            param.debug = "por tablas"
            # Aquí va la lógica específica para cada bbdd
            recorre_tablas(param, bbdd, conn_mysql)
            resultado.append(json.loads(bbdd['Conexion'])['database'])

            param.debug = "execute act. fec_Carga"
            cursor_mysql.execute(
                "UPDATE mll_cfg_bbdd SET Ultima_fecha_Carga = %s WHERE ID = %s",
                (datetime.now(), bbdd["ID"])
            )
        
        conn_mysql.commit()

        param.debug = "Fin"
        return resultado

                  
    except Exception as e:
        param.error_sistema()
        graba_log(param, "recorre_tiendas.Exception", e)
        raise

    finally:
        param.debug = "cierra conn"
        close_connection_mysql(conn_mysql, cursor_mysql)

        param.debug = "Actualiza Ejec 0"
        actualizar_en_ejecucion(param, 0)
        enviar_email(config["Lista_emails"],
                     "Proceso finalizado",
                     "El proceso de sincronización ha terminado."
        )


#----------------------------------------------------------------------------------------
# ejecutar_proceso: Sincroniza todas las tablas de una tienda. Recibe un json con los datos del registro de mll_cfg_bbdd:
#   - ID int: Es el ID de la tabla que vamos a tratar
#   - Nombre str: Es el nombre de la tienda
#   - Conexion str: es la conexión de la tienda en formato -->{"host": "ip", "port": "1433", "user": "usuario", "database": "nombre_database", "p a s  s w o  r d": "la_contraseña"}
#   - Ultima_Fecha_Carga str: fecha en la que se sincronizó la última vez
#----------------------------------------------------------------------------------------
def recorre_tablas(param: InfoTransaccion, reg_cfg_bbdd, conn_mysql) -> list:

    try:
        param.debug = "Inicio"
        cursor_mysql = conn_mysql.cursor(dictionary=True)

        param.debug = "execute mll_cfg_tablas_entidades"
        # cursor_mysql.execute("SELECT * FROM mll_cfg_tablas_bbdd where id_bbdd = %s", (reg_cfg_bbdd["ID"],))
        cursor_mysql.execute("""SELECT a.*, b.id_bbdd as ID_BBDD FROM mll_cfg_tablas_entidades a
                               inner join mll_cfg_entidades b on a.id_entidad = b.id
                               where a.id_entidad = %s""",
                             (reg_cfg_bbdd["id_entidad"],)
                            )
        tablas_bbdd = cursor_mysql.fetchall()
        
        for tabla in tablas_bbdd:
            ultima_actualizacion = tabla["Fecha_Ultima_Actualizacion"]
            intervalo = tabla["Cada_Cuanto_Ejecutar"]
            imprime(["ultima_actualizacion:", ultima_actualizacion, intervalo],  "-")
            if (intervalo == 0 or (datetime.now() > ultima_actualizacion + timedelta(days=intervalo))):
                imprime(["Procesando TABLA:", tabla, datetime.now(),  ultima_actualizacion, timedelta(days=intervalo), (intervalo == 0 or (datetime.now() > ultima_actualizacion + timedelta(days=intervalo)))], "-")
               
                param.debug = f"Procesando tabla: {tabla}"
                # Aquí va la lógica específica para cada tabla
                procesar_tabla(param, tabla, conn_mysql)

        return []

    except Exception as e:
        param.error_sistema()
        graba_log(param, "recorre_tablas.Exception", e)
        raise 
            
    finally:
        param.debug = "Cierra Cursor"
        cursor_mysql.close()



#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def procesar_tabla(param: InfoTransaccion, tabla, conn_mysql):
    param.debug="Inicio"
    cursor_mysql = None # para que no de error en el finally
    valor_max = None

    try:
        param.debug = "Obtener cursor"
        # Obtener configuración y campos necesarios
        cursor_mysql = conn_mysql.cursor(dictionary=True)
        
        param.debug = "Select cfg_tablas"
        # Obtener nombre de la tabla y si se debe borrar
        cursor_mysql.execute("SELECT * FROM mll_cfg_tablas WHERE ID = %s", (tabla["ID_Tabla"],))

        tabla_config = cursor_mysql.fetchone()
        nombre_tabla = tabla_config["Tabla_Origen"]
        nombre_tabla_destino = tabla_config["Tabla_Destino"]
        # borrar_tabla = tabla_config["Borrar_Tabla"]
        cursor_mysql.close()

        param.debug = "obtener campos"
        # Obtener campos de la tabla
        campos = obtener_campos_tabla(conn_mysql, tabla["ID_entidad"],tabla["ID_Tabla"])

        param.debug = "crea_tabla_dest"
        # Crear tabla si no existe
        crear_tabla_destino(param, conn_mysql, nombre_tabla_destino, campos)

        param.debug = "obt. Origen"
        # Buscamos la conexión que necesitamos para esta bbdd origen
        bbdd_config = obtener_conexion_bbdd_origen(conn_mysql, tabla["ID_BBDD"])
        salto = 0
        proximo_valor = tabla["ult_valor"]


        while True:
            registros,lista_pk,lista_max_valor = Obtener_datos_origen(param, bbdd_config, nombre_tabla, campos, tabla_config["campos_PK"], proximo_valor, salto)
            imprime(registros, f"*Registros: {len(registros)}", 2)
            if len(registros) == 0:
                break

            salto += PAGINACION

            # Identificar el campo PK basado en mll_cfg_campos
            pk_campos = [campo for campo in campos if campo.get("PK", 0) >= 1]
            if not pk_campos:
                param.registrar_error(ret_txt=f"No se encontró ningún campo PK en {nombre_tabla}.", debug=f"Campos: {campos}")
                raise MadreException(param = param)

            # Usamos el primer campo PK encontrado
            pk_campo = pk_campos[0]["Nombre_Destino"]
            campos_update = [campo for campo in campos if campo["Nombre_Destino"] != pk_campo]

            # Generar consultas INSERT y UPDATE de forma dinamica
            # if "I" in tabla_config["insert_update"]:
            insert_query = comando_insert(campos, nombre_tabla_destino)
            # if "U" in tabla_config["insert_update"]:
            update_query = comando_update(campos_update, pk_campo, nombre_tabla_destino)

            # Preparar los cursores para MySQL
            cursor_mysql = conn_mysql.cursor()
            for registro in registros:
                # Obtener el valor del campo PK desde el registro
                pk_index = [campo["Nombre"] for campo in campos].index(pk_campos[0]["Nombre"])
                pk_value = registro[pk_index]

                proximo_valor = ", ".join(str(registro[i]) for i in lista_max_valor)
                if "U" in tabla_config["insert_update"]:
                    select = f"""SELECT COUNT(*) 
                                FROM {nombre_tabla_destino} 
                                WHERE {pk_campo} = %s
                                    AND Origen_BBDD = {tabla["ID_BBDD"]}"""

                    # Comprobar si el registro ya existe en la tabla destino
                    cursor_mysql.execute(select, (pk_value,))
                    existe = cursor_mysql.fetchone()[0] > 0  # Si existe, devuelve True
                else:
                    # Solo actualizo último valor recogido cuando es una tabla de insert, porque se entiende que inserta desde el registro que se ha quedado
                    existe = False # no se comprueba que exista, ya que no se hacaen updates
                    valor_max = proximo_valor

                if existe:
                    # Realizar un UPDATE
                    campos_update_filtrado = [campo for campo in campos_update if not (campo['Nombre'].startswith('{') and campo['Nombre'].endswith('}'))]
                    valores_update = [registro[[campo["Nombre"] for campo in campos].index(campo["Nombre"])]
                                                for campo in campos_update_filtrado] + [pk_value, tabla["ID_BBDD"]]
                    # imprime(["update:......", pk_value, update_query, valores_update], "=")
                    cursor_mysql.execute(update_query, valores_update)
                else:
                    # Realizar un INSERT
                    registro_destino = list(registro) + [tabla["ID_BBDD"]]  # Campos + Origen
                    # imprime(["INSERT:......",insert_query, registro_destino], "=")
                    cursor_mysql.execute(insert_query, registro_destino)
                
        
                param.debug = "Execute fec_ult_act"
                cursor_mysql.execute("""UPDATE mll_cfg_tablas_entidades
                                        SET Fecha_Ultima_Actualizacion = %s, 
                                            ult_valor = COALESCE(%s, ult_valor)
                                        WHERE ID = %s""",
                                    (datetime.now(), valor_max, tabla["ID"])
                                    )
            conn_mysql.commit()

        return valor_max

    except Exception as e:
        param.error_sistema()
        graba_log(param, "procesar_tabla.Exception", e)
        raise 

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def Obtener_datos_origen(param: InfoTransaccion, bbdd_config, nombre_tabla, campos, campos_PK, ult_valor, salto) -> list: # el primer dato son los registros y el segundo la lista de PKs de la tabla
    param.debug="Inicio"
    conn_sqlserver = None # para que no de error en el finally
    cursor_sqlserver = None # para que no de error en el finally
    registros = []
    lista_pk = []

    try:
        param.debug = "conn origen"
        # conextamos con esta bbdd origen
        conn_sqlserver = get_db_connection_sqlserver(bbdd_config)

        # Leer datos desde SQL Server
        param.debug = "crear cursor"
        cursor_sqlserver = conn_sqlserver.cursor()
        if not ult_valor:
            param.debug = f"No hay ult_valor para la tabla {nombre_tabla}, con los campos {campos_PK}"
            raise ValueError("No se ha proporcionado un valor para ult_valor.")

        # Contruimos la SELECT que va a recoger los datos de ORIGEN
        param.debug = "Construir Select"
        select_query, lista_pk, lista_max_valor = construir_consulta(param, campos, nombre_tabla, campos_PK, ult_valor, salto)

        imprime(["Select: ", select_query], "=")

        # Ejecución del cursor
        param.debug = "Ejecutar select"
        cursor_sqlserver.execute(select_query)
        registros = cursor_sqlserver.fetchall()

        return [registros, lista_pk, lista_max_valor]

    except Exception as e:
        param.error_sistema()
        graba_log(param, "Obtener_datos_origen.Exception", e)
        raise 

    finally:
        param.debug = f"cierra conexión sqlserver: {param.debug}"
        close_connection_sqlserver(conn_sqlserver, cursor_sqlserver)

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def construir_consulta(param: InfoTransaccion, campos, nombre_tabla, campos_PK, ult_valor, salto) -> list: # el primer elemento la query y el segundo la lista de PKs
    try:
        # Construcción de la lista de campos para la SELECT
        campos_select = [campo['Nombre'] for campo in campos if not campo['Nombre'].startswith('{')]
        
        lista_pk_valores = [item.strip('" ') for item in ult_valor.split(", ")]
        lista_pk_campos, lista_pk_formato, lista_pk_para_order = separar_campos_pk(campos_PK)
        condiciones_where = generar_where(param, lista_pk_campos, lista_pk_valores, lista_pk_formato, lista_pk_para_order)
        lista_max_valor = []

        # Construcción del WHERE
        condiciones_order = []
        lista_pk = list()
        for campo in campos:
            if campo.get('PK') != 0: # Sabemos su es un indice
                lista_max_valor.append(campo.get('PK') - 1) # Este lo vamos a utiliar para luego guardar el max_valor cargado

                if campo.get('PK') in lista_pk_para_order: # solo estos se deben utilizar para el order y el where
                    lista_pk.append(campo.get('PK') ) #carga_lista_pk(lista_pk, formato, campo.get('PK')-1)         
                    condiciones_order.append(f"{campo['Nombre']}")

        # Generar la consulta SQL
        query = f"SELECT {', '.join(campos_select)} FROM {nombre_tabla} {condiciones_where}"
        if condiciones_order:
            query += f" ORDER BY {' , '.join(condiciones_order)}"
            query = f"""{query} 
                    OFFSET {salto} ROWS            -- Salta 0 filas
                    FETCH NEXT {PAGINACION} ROWS ONLY; -- Toma las siguientes 100"""
        
        return [query, lista_pk, lista_max_valor]

    except Exception as e:
        param.error_sistema()
        graba_log(param, "Obtener_datos_origen.Exception", e)
        raise 


#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def separar_campos_pk(cadena):
    """
        cfg_tables.campos_pk debe tener un formato de 3 partes encerradas entre parentesis:
        - La primera parte son los nombres de los campos entre comillas (")
        - La segunda es como transformar cada uno de esos campos para hacer el where, 
            teniendo en cuenta que {V1} es el nombre del campo (de la zona anterior) y {V2} va a ser el valor del campo
        - La tercera será los campos que realmente van a formar parte del where
            
        ejemplo de la cadena mostrada en tres lineas para identificarlo mejor:
            ("stIdEnt"; "Fecha"; "[Serie Puesto Facturacion]"; "[Factura Num]"; "[Id Relacion]") 
            ("{v1} >= '{v2}'"; "{v1} >= CONVERT(DATETIME, '{v2}', 121) "; "{v1} >= '{v2}'"; "{v1} >= {v2}"; "{v1} >= {v2}") 
            (1)   --> tener en cuenta que los elementos empiezan en el 0 y el separador es el punto y coma

        
    """
    # Separar las dos partes
    partes = cadena.split(") (")
    if len(partes) != 3:
        raise ValueError("La cadena debe contener dos partes separadas por ') ('.")
    
    # Limpiar paréntesis iniciales y finales
    parte1 = partes[0].strip("()")
    parte2 = partes[1].strip("()")
    parte3 = partes[2].strip("()")
    
    # Convertir cada parte en listas separando por comas
    lista_campos = [item.strip().strip('"') for item in parte1.split(";")]
    lista_formatos = [item.strip().strip('"') for item in parte2.split(";")]
    lista_orden_str = [item.strip().strip('"') for item in parte3.split(";")] # deben ser números pero crea la lista de str
    imprime(lista_orden_str, "*Orden")
    lista_orden = []
    for cadena in lista_orden_str:
        try:
            lista_orden.append(int(cadena))
        except ValueError:
            print(f"No se puede convertir '{cadena}' a número.")

    if len(lista_campos) != len(lista_formatos):
        raise ValueError(f"Las dos listas han de tener el mismo número de elementos y tienen {len(lista_campos)} y {len(lista_formatos)} elementos")
    
    return lista_campos, lista_formatos, lista_orden


#----------------------------------------------------------------------------------------
# generamos el where de origen con los datos de las tres lista de elementos que tengo:
#   - Campos de la tabla original que son PK
#   - Ultimos valores utilizados, debemos empezar a trabajar desde ahí
#   - Posible conversión de datos, a fechas,....
#----------------------------------------------------------------------------------------
def generar_where(param: InfoTransaccion, lista_pk_campos, lista_pk_valores, lista_pk_formato, lista_pk_para_where):
    try:    
        # Verificar que todas las listas tengan la misma longitud
        if not (len(lista_pk_campos) == len(lista_pk_valores) == len(lista_pk_formato)):
            param.debug = f"Campos({len(lista_pk_campos)}): {lista_pk_campos}  --  Valores ({len(lista_pk_valores)}): {lista_pk_valores}  --  Formato ({len(lista_pk_formato)}): {lista_pk_formato}"
            raise ValueError("Las listas deben tener la misma longitud.")
        
        # Construir la cláusula WHERE
        where_clause = []
        for i, (col, val, template) in enumerate(zip(lista_pk_campos, lista_pk_valores, lista_pk_formato)):
            if i in lista_pk_para_where:
                if not template:  # Si lista_pk_formato no tiene valor, usar el formato básico
                    if isinstance(val, str):  # Si el valor es una cadena, mantener las comillas
                        where_clause.append(f"{col} >= \"{val}\"")
                    else:  # Si no es una cadena, usar el valor tal cual
                        where_clause.append(f"{col} >= {val}")
                else:  # Si lista_pk_formato tiene valor, usar el formato proporcionado
                    formatted_value = template.replace("{v1}", str(col)).replace("{v2}", str(val))
                    where_clause.append(formatted_value)
        
        # Unir las condiciones con AND
        return f"WHERE {' AND '.join(where_clause)}"

    except Exception as e:
        param.error_sistema()
        graba_log(param, "generar_where.Exception", e)
        raise 
#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def carga_lista_pk(lista, valor, posicion, relleno=None):
    # Rellenar la lista si la posición está fuera de rango
    while len(lista) <= posicion:
        lista.append(relleno)
    
    # Insertar el valor en la posición indicada
    lista[posicion] = valor

    return lista


#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def comando_insert(campos, nombre_tabla_destino):
    columnas_mysql = [campo["Nombre_Destino"] for campo in campos if not campo["Nombre"].startswith("{")] + ["Origen_BBDD"]

    return f"""
            INSERT INTO {nombre_tabla_destino} ({', '.join(columnas_mysql)})
            VALUES ({', '.join(['%s'] * len(columnas_mysql))})
            """

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def comando_update(campos_update, pk_campo, nombre_tabla_destino):
    """
    re.match(r"^{.+}$", campo["Nombre"]):
        - Verifica si campo["Nombre"] comienza con { y termina con }.
    
    re.search(r"{(.+?)}", campo["Nombre"]).group(1):
        - Extrae el contenido entre las llaves {} en campo["Nombre"].
    
    Condición en la comprensión de lista:
        - Si campo["Nombre"] cumple con la condición de llaves, genera Nombre_Destino = contenido_dentro_de_las_llaves.
        - Si no cumple, genera Nombre_Destino = %s.
    
    ', '.join([...]):
        - Combina todas las asignaciones generadas en una sola cadena separada por comas.
    """
    update_query = f"""
        UPDATE {nombre_tabla_destino}
        SET {', '.join([
            f'{campo["Nombre_Destino"]} = {re.search(r"{(.+?)}", campo["Nombre"]).group(1)}' if re.match(r"^{.+}$", campo["Nombre"]) 
            else f'{campo["Nombre_Destino"]} = %s' 
            for campo in campos_update
        ])}
        WHERE {pk_campo} = %s AND Origen_BBDD = %s
    """

    return update_query

