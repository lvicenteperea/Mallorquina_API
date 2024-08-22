from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        authorization: str = request.headers.get("Authorization")
        if authorization:
            token = authorization.split(" ")[1]
            if token == "your_token":  # Lógica para validar el token
                return await call_next(request)
        raise HTTPException(status_code=401, detail="Unauthorized")
