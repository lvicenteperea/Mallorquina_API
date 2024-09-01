from typing import Optional
from pydantic import BaseModel

class ValidaPrecodigoRequest(BaseModel):
    codigo_error: int
    mensaje: str
    # datos: Optional[Dict[str, Any]] = None
    # datos: Optional[list] = None

    id_Frontal: Optional[int] = None
    id_Catalogo: Optional[int] = None
    id_Campaign: Optional[int] = None
    id_Canje: Optional[int] = None
    id_Participante: Optional[int] = None
    id_Precodigo: Optional[int] = None
    

    def asigna_salida(self, param: list):
        self.id_Frontal = param[0]
        self.id_Catalogo = param[1]
        self.id_Campaign = param[2]
        self.id_Canje = param[3]
        self.id_Participante = param[4]
        self.id_Precodigo = param[5]
