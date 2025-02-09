from fastapi import HTTPException
from fastapi.responses import FileResponse
from app.utils.InfoTransaccion import InfoTransaccion
import os

from app.utils.functions import graba_log, imprime
from app.services.auxiliares.sendgrid_service import enviar_email
from app.utils.InfoTransaccion import InfoTransaccion

DOWNLOAD_PATH = "D:\\Nube\\GitHub\\Mallorquina_API\\app\\ficheros\\datos\\tarifas_a_TPV\\"

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def proceso(param: InfoTransaccion):
    funcion = "descarga.caja.proceso"
    param.debug="Inicio"
    resultado = []
    tipo = param.parametros[0] 
    nombre = param.parametros[1]

    try:
        # Construir la ruta completa del archivo
        file_path = os.path.join(DOWNLOAD_PATH, nombre)
        
        # Verificar si el archivo existe
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"Archivo '{file_path}' no encontrado")
        
        # Crear una respuesta mixta con el archivo y el JSON con la descripción
        resultado = FileResponse(file_path, filename=nombre)
        return resultado
    

    except Exception as e:
        param.error_sistema()
        graba_log(param, f"Excepción descarga.caja.proceso-{param.debug}", e)
        raise
