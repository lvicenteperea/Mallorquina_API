from fastapi import FastAPI
from app.api.routes import router as api_router
from app.config.settings import settings

# uvicorn app.main:app --reload

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

app.include_router(api_router)

@app.get("/")
async def read_root():
    return {"message": "Welcome to the API MADRE"}



'''
# -----------------------------------------------------------------------------------------------
# MIDDLEWARES
# -----------------------------------------------------------------------------------------------
app.add_middleware(LoggingMiddleware)
app.add_middleware(ExceptionMiddleware)
app.add_middleware(AuthMiddleware)

@app.get("/")
async def root():
    return {"message": "Hello World"}



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


