from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.categoria_service import CategoriaService
from app.schemas.categoria import CategoriaResponse

router = APIRouter(prefix="/categorias", tags=["categorias"])
service = CategoriaService()

@router.get("/", response_model=list[CategoriaResponse])
def listar(db: Session = Depends(get_db)):
    try:
        return service.get_all(db)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Erro ao listar categorias") from exc

@router.get("/{id}", response_model=CategoriaResponse)
def buscar(id: int, db: Session = Depends(get_db)):
    categoria = service.get_by_id(db, id)
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    return categoria
