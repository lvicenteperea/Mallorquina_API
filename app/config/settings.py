# con la nueva versión de pedantic, la variables deben ser anotadas:
from pydantic_settings import BaseSettings
# from typing import ClassVar

class Settings(BaseSettings):
    PROJECT_NAME: str = "MADRE"

    MYSQL_DB_URL: str = "127.0.0.1"
    MYSQL_DB_USER: str = 'test'  # Añadimos anotación de tipo
    MYSQL_DB_PWD: str = 'Test.01'  # Añadimos anotación de tipo
    MYSQL_DB_HOST: str = 'localhost'  # Añadimos anotación de tipo
    MYSQL_DB_DATABASE: str = 'test'  # Añadimos anotación de tipo

    MYSQL_DB_URL_MLL: str = "127.0.0.1"
    MYSQL_DB_USER_MLL: str = 'root'  # Añadimos anotación de tipo
    MYSQL_DB_PWD_MLL: str = 'admin'  # Añadimos anotación de tipo
    MYSQL_DB_HOST_MLL: str = 'localhost'  # Añadimos anotación de tipo
    MYSQL_DB_DATABASE_MLL: str = 'mallorquina'  # Añadimos anotación de tipo

    MONGODB_URL: str = ""

    LOG_LEVEL: str = "info"

    class Config:
        env_file = ".env"

settings = Settings()
