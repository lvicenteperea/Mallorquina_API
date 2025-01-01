from app.utils.InfoTransaccion import InfoTransaccion
import logging
import logging.config
import traceback

# ------------------------------------------------------------------------------------------------
# Expande una lista que tenga dentro un elemento InfoTransaccion
# ------------------------------------------------------------------------------------------------
def expande_lista(lista:list):
        new_list = []

        for item in lista:
            if isinstance(item, InfoTransaccion):
                # Si el elemento es una instancia de InfoTransaccion, lo expandimos
                new_list.extend(item.to_list())
            else:
                # Si no, simplemente lo añadimos a la nueva lista
                new_list.append(item)

        return new_list



# ------------------------------------------------------------------------------------------------
# Convierte una fila pyodbc en un diccionario
# ------------------------------------------------------------------------------------------------
def row_to_dict(row, cursor):
    # print("Obtener los nombres de las columnas")
    columns = [column[0] for column in cursor.description]
    # print("columnas ", columns)

    # Combinar los nombres de las columnas con los valores del row
    datos = dict(zip(columns, row))
    # print("datos ", datos)
    return datos
    


# ------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------
# esto sería con fichero de inicialización
try:
    print("inicializa logging")
    logging.config.fileConfig('app/logging.ini')
except Exception as e:
    print(f"Error configuring logging: {e}")

# Obtén los loggers
# logger = logging.getLogger('app_logger')
app_logger = logging.getLogger('app_logger')
time_logger = logging.getLogger('time_logger')


# ------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------
def graba_log(mi_mensaje:dict, origen, e, logger = app_logger):
    try:
        loc = "no disponible"

        if isinstance(e, BaseException): # Comprueba si es una excepción
            tb = traceback.extract_tb(e.__traceback__)
            archivo, linea, funcion, texto_err = tb[-1]
            loc = f'{texto_err.replace("-", "_")} - {archivo.replace("-", "_")} - {linea} - {funcion}'

        # Intentar obtener un código de error
        if hasattr(e, 'errno'):  # Excepciones del sistema
            err_num = e.errno
        elif hasattr(e, 'args') and len(e.args) > 0:  # Excepciones genéricas con args
            err_num = e.args[0]
        else:
            err_num = 0

        logger.error(f"MI ERROR: {origen}: {mi_mensaje} - ERROR: {err_num} - {str(e)} - LOCALIZACION: {loc})")

    except Exception as e:
        imprime(["Error en graba_log:", e], relleno="*")
        return

# ------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------
def graba_log_info(mensaje, logger = time_logger):

    logger.info(mensaje)

    for handler in logger.handlers:
        print(f"Handler: {handler}")
        handler.flush()

#------------------------------------------------------------------------------------------------
"""
Esta función es una ayuda para el desarrollo para hacer print de información
    Función que imprime textos con líneas de relleno al inicio y al final.

    Parámetros:
    - textos: lista de textos a imprimir.
    - relleno: carácter que se repetirá en la línea de relleno.
    - modo: 1 (por defecto) imprime todos los textos en la misma línea;
            otro valor imprime cada texto en una línea distinta.
"""
#------------------------------------------------------------------------------------------------
def imprime(textos: list, relleno: str = "", modo: int = 1):

    # Determinar el ancho de las líneas de relleno
    if relleno and relleno.strip() != "":
        ancho = max(len(str(texto)) for texto in textos) + 10  # Añade un extra para que se vea mejor
        linea_relleno = relleno * ancho
 
         # Imprimir la línea de relleno al inicio
        print(linea_relleno)

    # Imprimir los textos
    if modo == 1:
        # print(" ".join(textos))  # Todos los textos en la misma línea
        resultado = "<" + "> - <".join(str(elemento) for elemento in textos) + ">"
        print(resultado)
    else:
        for texto in textos:  # Cada texto en una línea separada
            print(texto)

    if relleno:
        # Imprimir la línea de relleno al final
        print(linea_relleno)
