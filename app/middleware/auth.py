from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from fastapi.responses import JSONResponse
from jose import jwt, JWTError
from fastapi import HTTPException
from fastapi.security import HTTPBearer
from app.config.settings import settings



"""
Lo ideal es que se guarde en el sistema:
    SECRET_KEY = os.getenv("SECRET_KEY", "default_dev_secret")

Pero podemos generala nosotros, sobre todo para desarrollo    
    import secrets

    SECRET_KEY = secrets.token_hex(32)  # Genera una clave de 64 caracteres (32 bytes)
    print(SECRET_KEY)
"""
SECRET_KEY = "71400d095eacde5d73d9621e4c6383672279ad437c08666ac0e5244c3928fd89"
ALGORITHM = "HS256"


class AuthMiddleware(BaseHTTPMiddleware):
    # Esquema de autenticación
    security = HTTPBearer()

    #----------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------    
    async def dispatch(self, request: Request, call_next):
        print("01. asdasdfasdfas231542342")
        # Excluir ciertas rutas de autenticación
        if request.url.path in ["/login", "/open-endpoint", "/docs", "/redoc", "/auth/create_token"]:
            return await call_next(request)


        print(f"Headers recibidos: {request.headers}")

        # Obtener token del encabezado Authorization
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse({"detail": "Autenticación requerida1"}, status_code=401)

        token = auth_header.split(" ")[1]

        # Agrega un registro para identificar las solicitudes que fallan debido a la ausencia del encabezado:
        if not auth_header or not auth_header.startswith("Bearer "):
            print(f"Fallo de autenticación en {request.url.path}: encabezado Authorization ausente o incorrecto")
            return JSONResponse({"detail": "Autenticación requerida2"}, status_code=401)

        request.state.user = self.get_current_user(token)


        return await call_next(request)


    #----------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------    
    @staticmethod
    def get_current_user(token): #credentials):
        try:
            if settings.AUTH_ENABLED:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]) #credentials.credentials
                # print(payload.get("user"), payload)
                return payload.get("user")
            else:
                return "usuario_dev"
            
        except JWTError as e:
            raise HTTPException(status_code=401, detail="Token inválido o expirado2")
        
    #----------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------    
    @staticmethod
    def create_token(data: dict) -> str:
        """
        Genera un token JWT con los datos proporcionados.
        
        Args:
            data (dict): Datos a incluir en el token (ejemplo: user, id_App, exp).
            
        Returns:
            str: Token JWT firmado.
        """
        return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)