from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.categoria_service import CategoriaService
from app.schemas.categoria import CategoriaResponse

router = APIRouter(prefix="/categorias", tags=["categorias"])
service = CategoriaService()

@router.get("/", response_model=list[CategoriaResponse])
def listar(db: Session = Depends(get_db)):
    return service.get_all(db)

@router.get("/{id}", response_model=CategoriaResponse)
def buscar(id: int, db: Session = Depends(get_db)):
    return service.get_by_id(db, id)
