# con la nueva versión de pedantic, la variables deben ser anotadas:
from pydantic_settings import BaseSettings
# from typing import ClassVar

class Settings(BaseSettings):
    PROJECT_NAME: str = "MALLORQUIA API"
    VERSION: str = "06062025"

    DEV_PROD: str = "DEV" # Cambia a "PROD" para producción

    # Rutas, estas deben ser del servidor donde se encuentre la web
    WEB_RUTA_LOCAL: str = "http://localhost:3000/" # "C:/GitHub/Mallorquina_API/"
    # WEB_RUTA_LOCAL: str = "https://intranet.pastelerialamallorquina.es/" # "C:/GitHub/Mallorquina_API/"
    WEB_RUTA_IMAGEN: str = "img/" # "app/ficheros/imagen/"
    CORS_ALLOWED_ORIGINS: list[str] = ["http://localhost:3000",
                                       "https://intranet.pastelerialamallorquina.es",
                                      ]

    RUTA_LOCAL: str = "E:/Nube/GitHub/Mallorquina_API/" # /opt/MALLORQUINBA_API/
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
    SSH_KEY_PATH: str = 'Mllrqn@1984'  # Cambia por la contraseña SSH del servidor
    # SSH_key_path: str = 'mifichero.ppk' # Cambia por ssh_password si usas contraseña
    # Conexión BBDD ----------------------------------------------------------------------------
    SSH_CONEX: bool = True  # Cambia a False si no usas conexión SSH o a True si la usas
    MYSQL_DB_HOST: str = "localhost"  # Cambia por la IP del servidor
    MYSQL_DB_PORT: int = 3306
    MYSQL_DB_USER: str = 'root'  # Añadimos anotación de tipo
    MYSQL_DB_PWD: str = 'La.Mallorquina@1984'  # Añadimos anotación de tipo
    MYSQL_DB_DATABASE: str = 'mallorquina'  # Añadimos anotación de tipo
    MYSQL_DB_CHARSET: str = "utf8mb4"




    # ----------------------------------------------------------------------------------------    

    ENCRYPTION_KEY: str = "ZOoYUEQNjONU2fwUv-afUuUA--Z4RZlvRL4evOY_ZJk="
    AUTH_ENABLED: bool = False  # Cambiar a False para desactivar la autenticación

    LOG_LEVEL: str = "info"

    class Config:
        env_file = ".env"

settings = Settings()