from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from fastapi.responses import JSONResponse
from jose import jwt, JWTError
from fastapi import HTTPException


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
    async def dispatch(self, request: Request, call_next):
        # Excluir ciertas rutas de autenticación
        if request.url.path in ["/login", "/open-endpoint", "/docs", "/redoc", "/create_token"]:
            return await call_next(request)

        # Obtener token del encabezado Authorization
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse({"detail": "Autenticación requerida1"}, status_code=401)

        token = auth_header.split(" ")[1]

        # Agrega un registro para identificar las solicitudes que fallan debido a la ausencia del encabezado:
        if not auth_header or not auth_header.startswith("Bearer "):
            print(f"Fallo de autenticación en {request.url.path}: encabezado Authorization ausente o incorrecto")
            return JSONResponse({"detail": "Autenticación requerida2"}, status_code=401)

        try:
            # Verificar el token
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            request.state.user = payload.get("user")

        except JWTError as e:
            print(f"Error de token en {request.url.path}: {e}")
            return JSONResponse({"detail": "Token inválido o expirado"}, status_code=401)




        return await call_next(request)
