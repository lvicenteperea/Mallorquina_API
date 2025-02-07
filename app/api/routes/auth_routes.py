from fastapi import APIRouter, HTTPException, Query, Depends, Header, Request

from app.middleware.auth import AuthMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone

from passlib.context import CryptContext

from app.config.db_mallorquina import get_db_connection_mysql, close_connection_mysql
from app.utils.functions import graba_log, imprime
from app.utils.mis_excepciones import MadreException
from app.utils.InfoTransaccion import InfoTransaccion
from app.api.schemas.user_app import LoginRequest, RegisterRequest

# Definimos el router
router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")



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


#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
@router.post("/create_token")
async def create_token(request: Request,
                       mi_request: TokenRequest, 
                       x_api_key: str = Header(default=None)
                      ):
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


#----------------------------------------------------------------------------------
    # "username": "luis"
    # "password": "mi_contraseña_segura"
#----------------------------------------------------------------------------------
@router.post("/login")
async def login(request: Request,
                login_request: LoginRequest,
                id_App: int = Query(..., description="Identificador de la aplicación"),
                user: str = Query(..., description="Nombre del usuario que realiza la solicitud"),
                ret_code: int = Query(..., description="Código de retorno inicial"),
                ret_txt: str = Query(..., description="Texto descriptivo del estado inicial"),
               ):
    try:
        resultado = []
        param = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, parametros=[])
        param.debug = f"infoTrans: {id_App} - {user} - {ret_code} - {ret_txt}"


        param.debug = "get_db_connection_mysql"
        conn_mysql = get_db_connection_mysql()
        cursor_mysql = conn_mysql.cursor(dictionary=True)

        # Buscar usuario en la base de datos
        cursor_mysql.execute("SELECT id, username, password_hash FROM hxxi_users WHERE username = %s", (login_request.username,))
        user_bbdd = cursor_mysql.fetchone()

        if not user_bbdd:
            raise HTTPException(status_code=401, detail="El Usuario y la Contraseña no son credenciales válidas")

        if "password_hash" not in user_bbdd:
            raise HTTPException(status_code=500, detail="Error en la estructura de datos de usuario")

        if not pwd_context.verify(login_request.password, user_bbdd["password_hash"]):
            raise HTTPException(status_code=401, detail=f"La Contraseña ({login_request.password}) y el Usuario ({login_request.username}) no son credenciales válidas")


        # imprime([user_bbdd, pwd_context.verify(login_request.password, user_bbdd["password_hash"])], "=", 2)


        # Generar Token JWT
        token_data = {
            "user_id": user_bbdd["id"],
            "username": user_bbdd["username"],
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        token = AuthMiddleware.create_token(token_data)

        # 🟢  ✅   ❌
        return {"ret_code":0,
                "ret_txt": "Todo OK",
                "token": token, 
                "user": {"id": user_bbdd["id"], 
                         "username": user_bbdd["username"]},
                "options": [{ "text": '✅ Consulta Cierre', "action": 'openConsultaCierre' },
                            { "text": '✅ Sincroniza BBDD', "action": 'openSincronizaTodo' },
                            { "text": '✅ Carga ERP', "action": 'openCargaProdErp' },
                            { "text": '✅ Arqueo Caja', "action": 'openArqueoCaja' },
                            { "text": '✅ Informe Arqueo Caja', "action": 'openArqueoCajaInf' },
                            { "text": '❌ Convierte Tarifas', "action": 'openConvierteTarifas' },
                            { "text": '❌ Fichas Técnicas', "action": 'openFichasTecnicas' },
                            { "text": '✅ openSincronizaTodo2', "action": 'openSincronizaTodo2' },
        ]
               }
             
    finally:
        close_connection_mysql(conn_mysql, cursor_mysql)



#----------------------------------------------------------------------------------
'''
5. Configuración en React
Desde el frontend en React, puedes autenticar usuarios con este código:

javascript
Copiar
Editar
async function login(username, password) {
    const response = await fetch("http://localhost:8000/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
    });

    if (!response.ok) throw new Error("Error en el login");
    const data = await response.json();
    localStorage.setItem("token", data.token);
}
Y al hacer peticiones protegidas:

javascript
Copiar
Editar
async function getData() {
    const token = localStorage.getItem("token");
    const response = await fetch("http://localhost:8000/protected-route", {
        headers: { Authorization: `Bearer ${token}` },
    });

    if (!response.ok) throw new Error("No autorizado");
    return await response.json();
}

async function registerUser(username, email, password) {
    const queryParams = new URLSearchParams({
        id_App: 1,  // El ID de la aplicación que estás usando
        user: "admin",  // Usuario que realiza el registro
        ret_code: 0,  // Código de retorno
        ret_txt: "Registro de usuario exitoso"  // Mensaje de retorno
    });

    const response = await fetch(`http://localhost:8000/auth/register?${queryParams.toString()}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, email, password }),
    });

    if (!response.ok) throw new Error("Error en el registro");

    return await response.json();
}

'''
#----------------------------------------------------------------------------------
@router.post("/register")
async def register(register_request: RegisterRequest,
                id_App: int = Query(..., description="Identificador de la aplicación"),
                user: str = Query(..., description="Nombre del usuario que realiza la solicitud"),
                ret_code: int = Query(..., description="Código de retorno inicial"),
                ret_txt: str = Query(..., description="Texto descriptivo del estado inicial"),
               ):
    try:
        resultado = []
        param = InfoTransaccion(id_App=id_App, user=user, ret_code=ret_code, ret_txt=ret_txt, parametros=[])
        param.debug = f"infoTrans: {id_App} - {user} - {ret_code} - {ret_txt}"


        param.debug = "get_db_connection_mysql"
        conn_mysql = get_db_connection_mysql()
        cursor_mysql = conn_mysql.cursor(dictionary=True)

        hashed_password = pwd_context.hash(register_request.password)

        cursor_mysql.execute(
            "INSERT INTO hxxi_users (username, email, password_hash) VALUES (%s, %s, %s)",
            (register_request.username, register_request.email, hashed_password),
        )
        conn_mysql.commit()


        return {"message": "Usuario registrado con éxito"}       

    except conn_mysql.connector.Error as err:
                conn_mysql.rollback()
                raise HTTPException(status_code=400, detail="Error al registrar usuario")
    finally:
        close_connection_mysql(conn_mysql, cursor_mysql)        