from fastapi import APIRouter
from app.api.routes import mallorquina

router = APIRouter()
router.include_router(mallorquina.router, tags=["Mallorquina"])
# router.include_router(backend.router, prefix="/backend", tags=["backend"])
# router.include_router(partners.router, prefix="/partners", tags=["partners"])
