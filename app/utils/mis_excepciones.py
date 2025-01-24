from app.utils.functions import imprime
from app.utils.InfoTransaccion import InfoTransaccion

class MadreException(Exception):
    param: dict = InfoTransaccion(debug="Tenemos un excepción MadreException")
    status_code: int = 0
    detail: str = ""

    def __init__(self, param: InfoTransaccion, detail: str = "", status_code: int = 0):
        if not param:
            self.param = InfoTransaccion(ret_code= status_code if status_code!=0 else -99, ret_txt=detail)
        else:
            self.param = param

        if not self.param.ret_code:
            self.param.ret_code = -1

        if not self.param.ret_txt:
            self.param.ret_txt = detail if detail else "Error no controlado"

        elif isinstance(detail, str) and detail:
            self.detail = detail
        else:
            self.detail = self.param.ret_txt

        if status_code == 0:
            if self.param.ret_code == -99:
                self.status_code = 500
            else:
                self.status_code = 400
        else:
            self.status_code = status_code

        imprime(["Madre / Excptn: ", self.param, self.status_code, self.detail], relleno="-")
        
        super().__init__(self.param.ret_txt)
        

    def to_dict(self) -> dict:
        return {"detail": self.detail,
                "status_code": self.status_code, 
                "param": self.param
        }