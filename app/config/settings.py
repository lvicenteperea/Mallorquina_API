# con la nueva versión de pedantic, la variables deben ser anotadas:
from pydantic_settings import BaseSettings
# from typing import ClassVar

class Settings(BaseSettings):
    PROJECT_NAME: str = "MALLORQUIA API"

    DEV_PROD: str = "DEV" # Cambia a "PROD" para producción

    # Rutas, estas deben ser del servidor donde se encuentre la web
    WEB_RUTA_LOCAL: str = "http://localhost:3000/" # "C:/GitHub/Mallorquina_API/"
    # WEB_RUTA_LOCAL: str = "https://intranet.pastelerialamallorquina.es/" # "C:/GitHub/Mallorquina_API/"
    WEB_RUTA_IMAGEN: str = "img/" # "app/ficheros/imagen/"
    CORS_ALLOWED_ORIGINS: list[str] = ["http://localhost:3000",
                                       "https://intranet.pastelerialamallorquina.es",
                                      ]

    RUTA_LOCAL: str = "E:/Nube/Github/Mallorquina_API" # "C:/GitHub/Mallorquina_API/" # /opt/MALLORQUINBA_API/
    RUTA_IMAGEN: str = "app/ficheros/imagen/"
    RUTA_BASE: str = "app/ficheros/"
    RUTA_DATOS: str = "app/ficheros/datos/"
    RUTA_TPV: str = "app/ficheros/datos/tarifas_a_TPV/"
    RUTA_WEB: str = "app/ficheros/web/"
    RUTA_ALERGENOS:str = "app/ficheros/datos/alergenos/"
    RUTA_ALERGENOS_HTML: str = "app/ficheros/datos/alergenos/reports/"
    RUTA_CIERRE_CAJA: str = "app/ficheros/datos/cierre_caja/"

    # ----------------------------------------------------------------------------------------
    # CONEXIONES
    # ----------------------------------------------------------------------------------------
    # Coenxión SSH ---------------------------------------------------------------------------
    SSH_HOST: str = '194.164.166.153'  # Cambia por la IP del servidor
    SSH_PORT: int = 15122  # Cambia por el puerto SSH del servidor
    SSH_USER: str = 'lvicente'  # Cambia por el usuario SSH del servidor
    SSH_PWD: str = 'xxxxxxx'  # Cambia por la contraseña SSH del servidor
    # SSH_key_path: str = 'mifichero.ppk' # Cambia por ssh_password si usas contraseña
    # ssh_pkey_password="si la tuviera" # Cambia por ssh_password si usas contraseña
    # Conexión BBDD ----------------------------------------------------------------------------
    SSH_CONEX: bool = False  # Cambia a False si no usas conexión SSH
    MYSQL_DB_HOST_MLL: str = "127.0.0.1"
    MYSQL_DB_PORT_MLL: int = 3306  # es el puerto de MySQL o IONOS
    # MYSQL_DB_PORT_MLL: int = 13306   # es el puerto de MariaDB
    MYSQL_DB_USER_MLL: str = 'root'  # Añadimos anotación de tipo
    MYSQL_DB_PWD_MLL: str = 'No.Admin'  # Añadimos anotación de tipo
    MYSQL_DB_DATABASE_MLL: str = 'mallorquina'  # Añadimos anotación de tipo
    MYSQL_DB_CHARSET: str = "utf8mb4"

    # ----------------------------------------------------------------------------------------    
    MONGODB_URL: str = ""

    ENCRYPTION_KEY: str = "ZOoYUEQNjONU2fwUv-afUuUA--Z4RZlvRL4evOY_ZJk="
    AUTH_ENABLED: bool = False  # Cambiar a False para desactivar la autenticación

    LOG_LEVEL: str = "info"

    class Config:
        env_file = ".env"

settings = Settings()