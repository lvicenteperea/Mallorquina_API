from typing import Optional, Dict, Any
from pydantic import BaseModel

class ValidaUrlResponse(BaseModel):
    codigo_error: int
    mensaje: str
    datos: Optional[Dict[str, Any]] = None