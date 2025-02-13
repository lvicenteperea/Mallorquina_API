from app.utils.functions import imprime
from app.utils.InfoTransaccion import InfoTransaccion

class MiException(Exception):
    param: dict = InfoTransaccion(debug="Tenemos un excepción MiException")
    status_code: int = 0
    detail: str = ""

    def __init__(self, param: InfoTransaccion, detail: str = "", status_code: int = 0):
        # if not param:
        #     self.param = InfoTransaccion(ret_code= status_code if status_code!=0 else -99, ret_txt=detail)
        # else:
        #     self.param = param

        # if not self.param.ret_txt:
        #     self.param.ret_txt = detail if detail else "Error no controlado"

        # imprime(["Madre / Excptn: ", self.param, f"{self.status_code}({status_code})", f"{self.detail}({detail})"], relleno="-")
        print("Madre / Excptn: ", self.param, f"{self.status_code}({status_code})", f"{self.detail}({detail})")
        
        # super().__init__(self.param.ret_txt)

        

    def to_dict(self) -> dict:
        return {"detail": self.detail,
                "status_code": self.status_code, 
                "param": self.param
        }