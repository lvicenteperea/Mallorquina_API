from pydantic import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "MADRE"

    '''
        Usuarios de Localhost en PC terraza
        DB_CONFIG = {
                    'user': 'root',
                    'password': 'admin',
                    'host': 'localhost',
                    'database': 'test',
                }

        DB_CONFIG = {
                    'user': 'luis',
                    'password': 'luis.01',
                    'host': 'localhost',
                    'database': 'test',
                }
    '''
    MYSQL_DB_URL: str = "127.0.0.1"
    MYSQL_DB_USER =  'test'
    MYSQL_DB_PWD = 'Test.01'
    MYSQL_DB_HOST = 'localhost'
    MYSQL_DB_DATABASE = 'test'

    MONGODB_URL: str = ""

    LOG_LEVEL: str = "info"

    class Config:
        env_file = ".env"

settings = Settings()
