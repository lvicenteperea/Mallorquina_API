from fastapi import APIRouter, HTTPException, Query, Depends, Header, Request

from app.middleware.auth import AuthMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone

from app.utils.functions import graba_log, imprime
from app.utils.mis_excepciones import MadreException
from app.utils.InfoTransaccion import InfoTransaccion

# Definimos el router
router = APIRouter()


#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
@router.get("/endpoint_sin_auth")
async def endpoint_sin_auth():
    return {"message": "Esta es una ruta pública."}


#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
# Modelo para el cuerpo de la solicitud
class TokenRequest(BaseModel):
    user: str
    id_App: int
    username: str = None
    password: str = None


@router.post("/create_token")
async def create_token(request: Request,
                       mi_request: TokenRequest, 
                       x_api_key: str = Header(default=None)):
    try:
        # Validar credenciales. SECURIZAMOS por usuario y contraseña
        if mi_request.username != "admin" or mi_request.password != "password123":
            raise HTTPException(status_code=401, detail="Credenciales inválidas")

        # . SECURIZAMOS poruna calve secreta tipo api_key
        if x_api_key != "mi_clave_secreta":
            raise HTTPException(status_code=403, detail="Clave de API inválida")

        client_ip = request.client.host
        print(f"Solicitud de token desde IP: {client_ip} para usuario: {mi_request.username}")

        token = AuthMiddleware.create_token({
            "user": mi_request.user,
            "id_App": mi_request.id_App,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)  # Expira en 1 hora --> datetime.now(timezone.utc) + timedelta(minutes=15) serían 15 minutos
        })
        return {"token": token}
    except Exception as e:
        print(f"Error al generar el token: {e}")
        raise HTTPException(status_code=500, detail="Error interno al generar el token")
