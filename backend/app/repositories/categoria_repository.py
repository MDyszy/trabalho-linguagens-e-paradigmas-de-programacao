from sqlalchemy.orm import Session
from app.models.categoria import Categoria

class CategoriaRepository:
    def get_all(self, db: Session):
        return db.query(Categoria).all()

    def get_by_id(self, db: Session, id: int):
        return db.query(Categoria).filter(Categoria.id == id).first()

    def get_by_nome(self, db: Session, nome: str):
        return db.query(Categoria).filter(Categoria.nome == nome).first()

    def create(self, db: Session, nome: str):
        categoria = Categoria(nome=nome)
        db.add(categoria)
        db.commit()
        db.refresh(categoria)
        return categoria
   