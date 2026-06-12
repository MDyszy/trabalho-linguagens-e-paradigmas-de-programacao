from sqlalchemy.orm import Session
from app.repositories.categoria_repository import CategoriaRepository

categoria_repo = CategoriaRepository()

class CategoriaService:

    def get_all(self, db: Session):
        return categoria_repo.get_all(db)

    def get_by_id(self, db: Session, id: int):
        return categoria_repo.get_by_id(db, id)
