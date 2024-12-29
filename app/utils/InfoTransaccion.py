
from pydantic import BaseModel

class InfoTransaccion(BaseModel):
    id_App: int
    user: str
    ret_code: int = 0
    ret_txt: str = "Ok"

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

    def error_sistema(self):
        self.ret_code = -99
        self.ret_txt = "Error general. contacte con su administrador"

    def limpiar_error(self):
        self.ret_code = None
        self.ret_txt = None

    def to_list(self):
        return [self.id_App, self.user, self.ret_code, self.ret_txt]

    def to_dict(self):
        return {"id_app": self.id_App, "Usuario": self.user, "ret_code": self.ret_code, "ret_txt": self.ret_txt, "parametros": self.parametros, "resultados": self.resultados}
    
    def __str__(self):
        return f"App: {self.id_App}, Usuario: {self.user}, Error: {self.ret_code} - {self.ret_txt}, parametros: {self.parametros}"