from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.repositories.movimentacao_repository import MovimentacaoRepository
from app.repositories.produto_repository import ProdutoRepository
from app.schemas.movimentacao import MovimentacaoCreate
from app.domain.estoque import TipoMovimentacao, saldo, pode_retirar

movimentacao_repo = MovimentacaoRepository()
produto_repo = ProdutoRepository()


class MovimentacaoService:

    def registrar(self, db: Session, produto_id: int, data: MovimentacaoCreate):
        produto = produto_repo.get_by_id(db, produto_id)
        if not produto:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        if data.quantidade <= 0:
            raise HTTPException(status_code=400, detail="Quantidade deve ser positiva")

        # A decisão de negócio é uma função pura sobre os dados (não mexe em estado).
        saldo_atual = saldo(produto.movimentacoes)
        if data.tipo == TipoMovimentacao.SAIDA and not pode_retirar(saldo_atual, data.quantidade):
            raise HTTPException(
                status_code=400,
                detail=f"Saída de {data.quantidade} maior que o saldo atual ({saldo_atual})",
            )

        return movimentacao_repo.create(db, produto_id, data.tipo.value, data.quantidade)

    def get_historico(self, db: Session, produto_id: int):
        produto = produto_repo.get_by_id(db, produto_id)
        if not produto:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        return movimentacao_repo.get_by_produto(db, produto_id)
