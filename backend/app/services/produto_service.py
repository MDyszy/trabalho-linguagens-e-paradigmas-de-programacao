from sqlalchemy.orm import Session
from app.repositories.produto_repository import ProdutoRepository
from app.repositories.categoria_repository import CategoriaRepository
from app.repositories.movimentacao_repository import MovimentacaoRepository
from app.schemas.produto import ProdutoCreate
from app.domain.estoque import TipoMovimentacao, em_alerta

produto_repo = ProdutoRepository()
categoria_repo = CategoriaRepository()
movimentacao_repo = MovimentacaoRepository()

class ProdutoService:

    def get_all(self, db: Session):
        return produto_repo.get_all(db)

    def get_by_id(self, db: Session, id: int):
        return produto_repo.get_by_id(db, id)

    def create(self, db: Session, data: ProdutoCreate):
        categoria = categoria_repo.get_by_nome(db, data.categoria_nome)
        if not categoria:
            categoria = categoria_repo.create(db, data.categoria_nome)

        produto_data = data.model_dump(exclude={"categoria_nome", "quantidade"})
        produto_data["categoria_id"] = categoria.id
        produto = produto_repo.create_from_dict(db, produto_data)

        # O estoque inicial vira a 1ª movimentação de entrada (evento imutável).
        if data.quantidade > 0:
            movimentacao_repo.create(
                db, produto.id, TipoMovimentacao.ENTRADA.value, data.quantidade
            )
            db.refresh(produto)
        return produto

    def get_alertas(self, db: Session):
        # Filtro funcional sobre o saldo DERIVADO (não há mais coluna quantidade).
        produtos = produto_repo.get_all(db)
        return [p for p in produtos if em_alerta(p.quantidade, p.estoque_minimo)]
