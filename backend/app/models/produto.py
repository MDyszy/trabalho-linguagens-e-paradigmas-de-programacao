from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.domain.estoque import saldo


class Produto(Base):
    __tablename__ = "produto"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    categoria_id = Column(Integer, ForeignKey("categoria.id"), nullable=False)
    estoque_minimo = Column(Integer, nullable=False)
    imagem_url = Column(String, nullable=True)

    categoria = relationship("Categoria")
    movimentacoes = relationship(
        "Movimentacao",
        back_populates="produto",
        cascade="all, delete-orphan",
    )

    @property
    def quantidade(self) -> int:
        """Saldo derivado do histórico de movimentações (não é coluna no banco)."""
        return saldo(self.movimentacoes)
