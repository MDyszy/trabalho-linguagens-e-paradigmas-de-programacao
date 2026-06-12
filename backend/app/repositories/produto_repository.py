from sqlalchemy.orm import Session
from app.models.produto import Produto

class ProdutoRepository:
    def get_all(self, db: Session):
        return db.query(Produto).all()

    def get_by_id(self, db: Session, id: int):
        return db.query(Produto).filter(Produto.id == id).first()

    def create_from_dict(self, db: Session, data: dict):
        produto = Produto(**data)
        db.add(produto)
        db.commit()
        db.refresh(produto)
        return produto
