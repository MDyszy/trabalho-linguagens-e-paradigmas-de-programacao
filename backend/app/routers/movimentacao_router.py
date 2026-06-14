from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.movimentacao_service import MovimentacaoService
from app.schemas.movimentacao import MovimentacaoCreate, MovimentacaoResponse

router = APIRouter(prefix="/produtos", tags=["movimentacoes"])
service = MovimentacaoService()

@router.post("/{produto_id}/movimentacoes", response_model=MovimentacaoResponse)
def registrar(produto_id: int, data: MovimentacaoCreate, db: Session = Depends(get_db)):
    try:
        return service.registrar(db, produto_id, data)
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Erro ao registrar movimentação") from exc

@router.get("/{produto_id}/movimentacoes", response_model=list[MovimentacaoResponse])
def historico(produto_id: int, db: Session = Depends(get_db)):
    try:
        return service.get_historico(db, produto_id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Erro ao buscar histórico de movimentações") from exc
