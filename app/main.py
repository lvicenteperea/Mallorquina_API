# Lo siguiente:
#     utilizar los middleware


# uvicorn app.main:app --reload
from fastapi import FastAPI, HTTPException
import json

from app.exceptions import http_exception_handler, json_decode_error_handler, generic_exception_handler, madre_exception_handler, type_error_handler
from app.api.routes import router as api_router
from app.config.settings import settings
from app.utils.mis_excepciones import MadreException
from app.middleware.log_tiempos_respuesta import log_tiempos_respuesta

'''
from fastapi.middleware.cors import CORSMiddleware

from app.middleware.logging import LoggingMiddleware
from app.middleware.exception import ExceptionMiddleware
from app.middleware.auth import AuthMiddleware
'''



# -----------------------------------------------------------------------------------------------
# FASTAPI
# -----------------------------------------------------------------------------------------------
app = FastAPI(title=settings.PROJECT_NAME)




# -----------------------------------------------------------------------------------------------
# MIDDLEWARES
# -----------------------------------------------------------------------------------------------
# Importar y registrar el middleware
app.middleware("http")(log_tiempos_respuesta)


# -----------------------------------------------------------------------------------------------
# RUTAS
# -----------------------------------------------------------------------------------------------
app.include_router(api_router)

@app.get("/")
async def read_root():
    return {"message": "Welcome to the API MADRE"}


# -----------------------------------------------------------------------------------------------
# EXCEPTION HANDLERS
# -----------------------------------------------------------------------------------------------
app.add_exception_handler(MadreException, madre_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(json.JSONDecodeError, json_decode_error_handler)
app.add_exception_handler(Exception, generic_exception_handler)
app.add_exception_handler(TypeError, type_error_handler)


'''
# -----------------------------------------------------------------------------------------------
# MIDDLEWARES
# -----------------------------------------------------------------------------------------------
app.add_middleware(LoggingMiddleware)
app.add_middleware(ExceptionMiddleware)
app.add_middleware(AuthMiddleware)



# -----------------------------------------------------------------------------------------------
# CORS
# -----------------------------------------------------------------------------------------------
# Configuración de CORS
origins = [
    "http://localhost",            # Tu frontend local
    "http://localhost:3000",       # Otro puerto local, por ejemplo, para React
    "https://yourdomain.com",      # Tu dominio principal
    "https://*.yourdomain.com"     # Todos los subdominios
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,           # Permitir estos dominios
    allow_credentials=True,          # Permitir cookies/credenciales
    allow_methods=["*"],             # Permitir todos los métodos (GET, POST, etc.)
    allow_headers=["*"],             # Permitir todas las cabeceras
)
'''

'''
Este bloque de código se usa para iniciar la aplicación FastAPI utilizando uvicorn 
como servidor cuando ejecutas directamente el script Python. 
Es un método estándar para lanzar aplicaciones web con FastAPI y asegurar que el servidor 
web esté escuchando en el puerto y dirección IP correctos, con la configuración de logging adecuada.
'''
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level=settings.LOG_LEVEL)


