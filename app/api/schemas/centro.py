from typing import Optional
from pydantic import BaseModel
from typing import List, Dict

class CentroRequest(BaseModel):
    codigo: str
    centro_id: Optional[int] = None
    nombre: str


class ListaCentrosResponse(BaseModel):
    codigo_error: int
    mensaje: str
    lista: List[Dict[str, str]]