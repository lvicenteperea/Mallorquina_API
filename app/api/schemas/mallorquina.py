from typing import Optional
from pydantic import BaseModel

class MallorquinaResponse(BaseModel):
    codigo_error: int
    mensaje: Optional[str] = None
    datos: Optional[str] = None