from typing import Optional
from pydantic import BaseModel

class PrecodigoRequest(BaseModel):
    codigo: str
    usuario_id: Optional[int] = None
