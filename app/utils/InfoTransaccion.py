
from pydantic import BaseModel

class InfoTransaccion(BaseModel):
    id_App: int
    user: str
    ret_code: int = None
    ret_txt: str = None

    # Datos cuando las funciones de BBDD retornar un valor Ok, Dos listas diferentes
    # En "parametros" retorna la lista de parametros que son de salida o entrada/salida
    parametros: list = None
    # En "resultados" es para procedimientos que retornar un listado de registros "una select"
    resultados: list = []
    

    def set_parametros(self, datos):
        self.parametros = datos

    def set_resultados(self, datos):
        self.resultados = datos

    def registrar_error(self, ret_code: int, ret_txt: str):
        self.ret_code = ret_code
        self.ret_txt = ret_txt

    def limpiar_error(self):
        self.ret_code = None
        self.ret_txt = None

    def to_list(self):
        return [self.id_App, self.user, self.ret_code, self.ret_txt]

    def __str__(self):
        return f"App: {self.id_App}, Usuario: {self.user}, Error: {self.ret_code} - {self.ret_txt}, parametros: {self.parametros}"


'''
Si realmente necesitas que InfoTransaccion siga siendo una clase personalizada y quieres que FastAPI/Pydantic
la acepte, puedes configurar Pydantic para permitir tipos arbitrarios:

from pydantic import BaseModel, Field

class InfoTransaccion:
    def __init__(self, id_App: int, user: str, ret_code=None, ret_txt=None):
        self.id_App = id_App
        self.user = user
        self.ret_code = ret_code
        self.ret_txt = ret_txt

    def to_list(self):
        return [self.id_App, self.user, self.ret_code, self.ret_txt]

    def registrar_error(self, ret_code, ret_txt): 
        self.ret_code = ret_code
        self.ret_txt = ret_txt

    def limpiar_error(self):
        self.ret_code = None
        self.ret_txt = None

    def __str__(self):
        return f"App: {self.id_App}, Usuario: {self.user}, Error: {self.ret_code}, Descripción: {self.ret_txt}"

class MyModel(BaseModel):
    info_transaccion: InfoTransaccion

    class Config:
        arbitrary_types_allowed = True


Otras opciones:
Opción 1: Convertir InfoTransaccion en un modelo Pydantic
Si decides que InfoTransaccion debe ser un modelo de Pydantic, puedes hacerlo de esta manera:

from pydantic import BaseModel

class InfoTransaccion(BaseModel):
    id_App: int
    user: str
    ret_code: int = None
    ret_txt: str = None

    def registrar_error(self, ret_code, ret_txt):
        self.ret_code = ret_code
        self.ret_txt = ret_txt

    def limpiar_error(self):
        self.ret_code = None
        self.ret_txt = None

    def to_list(self):
        return [self.id_App, self.user, self.ret_code, self.ret_txt]


Opción 2: Usar InfoTransaccion dentro de un modelo Pydantic
Si InfoTransaccion es solo un campo dentro de un modelo más grande:

from pydantic import BaseModel

class InfoTransaccionModel(BaseModel):
    id_App: int
    user: str
    ret_code: int = None
    ret_txt: str = None

class SomeOtherModel(BaseModel):
    info_transaccion: InfoTransaccionModel
    # otros campos aquí


¿Cuál Opción Deberías Usar?
Si necesitas validar los datos o quieres aprovechar las capacidades de serialización de Pydantic, es mejor convertir InfoTransaccion en un modelo de Pydantic.
Si InfoTransaccion es más un tipo de dato arbitrario que no necesita la validación de Pydantic, y estás seguro de que no necesitas esa validación, puedes usar la opción de arbitrary_types_allowed.
'''