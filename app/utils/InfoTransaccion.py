
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Any

class InfoTransaccion(BaseModel):
    id_App: int = 0
    user: str = 'Sistema_' # Usuario de sistema que se conecta: Fronta, BackOfficce, un servicio específico, webs de terceros...
    ret_code: int = 0
    ret_txt: str = "Ok"
    debug: str = "" # solo por si se necesita saber por donde ha pasado la ejecución

    # Datos cuando las funciones de BBDD retornar un valor Ok, Dos listas diferentes
    # En "parametros" retorna la lista de parametros que son de salida o entrada/salida
    parametros: Optional[List[Any]] = None  # Especificar lista opcional con elementos de cualquier tipo
    # En "resultados" es para procedimientos que retornar un listado de registros "una select"
    resultados: List[Any] = []  # Lista vacía predeterminada para resultados
    

    def set_parametros(self, datos):
        self.parametros = datos

    def set_resultados(self, datos):
        self.resultados = datos

    def registrar_error(self, ret_txt: str, ret_code: int = -1, debug: str = ""):
        self.ret_code = ret_code
        self.ret_txt = ret_txt
        if debug:
            self.debug = debug

    def error_sistema(self, txt_adic: str = '.', debug: str = ""):
        if self.ret_code is None or self.ret_code >= 0:
            self.ret_code = -99
            self.ret_txt = f"Error general. contacte con su administrador ({datetime.now().strftime('%Y%m%d%H%M%S')}){txt_adic}"
        
        self.debug = self.debug if not debug else debug

    def limpiar_error(self):
        self.ret_code = None
        self.ret_txt = None
        self.debug = None

    def to_list(self):
        return [self.id_App, self.user, self.ret_code, self.ret_txt]

    def to_list_proc_bbdd(self):

        lista = [self.id_App, self.user, self.ret_code, self.ret_txt]

        for item in self.parametros:
            lista.append(item)

        return lista


    def to_infotrans_proc_bbdd(self, list: list):
        return InfoTransaccion( id_App      = list[0], 
                                user        = list[1], 
                                ret_code    = list[2], 
                                ret_txt     = list[3] if list[3] else "", 
                                parametros  = list[4:]
                           )

    def to_dict(self):
        return {"id_app": self.id_App, "Usuario": self.user, "ret_code": self.ret_code, "ret_txt": self.ret_txt, "debug": self.debug}
        #return {"id_app": self.id_App, "Usuario": self.user, "ret_code": self.ret_code, "ret_txt": self.ret_txt, "debug": self.debug, "parametros": self.parametros, "resultados": self.resultados}
    
    def __str__(self):
        return f"App: {self.id_App}, Usuario: {self.user}, Error: {self.ret_code} - {self.ret_txt}, debug: {self.debug}, parametros: {self.parametros}"