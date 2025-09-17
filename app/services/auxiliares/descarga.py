from fastapi.responses import FileResponse
from app.utils.InfoTransaccion import InfoTransaccion
import os
from pathlib import Path
import zipfile
import tempfile

from app.utils.InfoTransaccion import InfoTransaccion
from app.utils.mis_excepciones import MiException
from app.config.settings import settings

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def proceso(param: InfoTransaccion):
    funcion = "descarga.proceso"
    param.debug="Inicio"
    tipo = param.parametros[0] 
    nombres = param.parametros[1]

    try:
        if tipo == "TPV":
            # return descarga_precios_tpv(param, nombres)
            return descarga_fichero(param, settings.RUTA_TPV, nombres)
        elif tipo == "Alérgenos":
            return descarga_alergenos(param)
        elif tipo == "Arqueo":
            return descarga_fichero(param, settings.RUTA_CIERRE_CAJA, nombres)
    
    

    except MiException as e:
        param.error_sistema(e=e, debug=f"{funcion}.MiExcepción")
        raise
    except Exception as e:
        param.error_sistema(e=e, debug=f"{funcion}.Excepción")
        raise


#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def descarga_fichero(param: InfoTransaccion, path: str, nombres: list):
    try:

        if len(nombres) != 1:
            raise MiException(param,f"No viene un nombre de fichero, vienen:  {len(nombres)}-{nombres}", -1)
        else:
            nombre = nombres[0]

        file_path = Path(settings.RUTA_LOCAL) / path / nombre
        
        # Verificar si el archivo existe
        if not file_path.exists():
            raise MiException(param,f"Archivo '{file_path}' no encontrado", -1)
        
        # Crear una respuesta mixta con el archivo y el JSON con la descripción
        resultado = FileResponse(file_path, filename=nombre)
        return resultado

    except MiException as e:
        param.error_sistema(e=e, debug="MiExcepción descarga.descarga_fichero")
        raise
    except Exception as e:
        param.error_sistema(e=e, debug="Excepción descarga.descarga_fichero")
        raise

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def descarga_alergenos(param: InfoTransaccion):
    try:
        nombre = "alergenos_y_fichas.zip"
        # Definir rutas
        base_path = settings.RUTA_ALERGENOS_HTML
        file_to_add = os.path.join(base_path, "fichas_tecnicas.html")
        dir_to_add = os.path.join(base_path, "fichas")

        if (not os.path.exists(file_to_add) or
            not os.path.exists(dir_to_add)):
            raise MiException(param, f"Archivo o directorio de fichas técnicas", -1)

        # Crear archivo ZIP temporal
        temp_dir = tempfile.gettempdir()
        zip_filename = os.path.join(temp_dir, nombre)
        
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Añadir archivo individual
            zipf.write(file_to_add, os.path.basename(file_to_add))
            
            # Añadir directorio completo con su estructura
            for root, _, files in os.walk(dir_to_add):
                for file in files:
                    full_path = os.path.join(root, file)
                    zipf.write(full_path, os.path.relpath(full_path, base_path))



        #----------------------------------------------------

        return FileResponse(zip_filename, filename=nombre)

    except MiException as e:
        param.error_sistema(e=e, debug="MiExcepción descarga.descarga_alergenos")
        raise
    except Exception as e:
        param.error_sistema(e=e, debug="Excepción descarga.descarga_alergenos")
        raise


