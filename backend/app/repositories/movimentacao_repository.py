from sqlalchemy.orm import Session
from app.models.movimentacao import Movimentacao


class MovimentacaoRepository:
    """Append-only: movimentações são eventos imutáveis (só INSERT e leitura)."""

    def create(self, db: Session, produto_id: int, tipo: str, quantidade: int):
        movimentacao = Movimentacao(
            produto_id=produto_id,
            tipo=tipo,
            quantidade=quantidade,
        )
        db.add(movimentacao)
        db.commit()
        db.refresh(movimentacao)
        return movimentacao

    def get_by_produto(self, db: Session, produto_id: int):
        return (
            db.query(Movimentacao)
            .filter(Movimentacao.produto_id == produto_id)
            .order_by(Movimentacao.data)
            .all()
        )
