from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


class Movimentacao(Base):
    __tablename__ = "movimentacao"

    # Eventos imutáveis: a tabela é append-only (só INSERT e leitura).
    id = Column(Integer, primary_key=True, index=True)
    produto_id = Column(Integer, ForeignKey("produto.id"), nullable=False, index=True)
    tipo = Column(String, nullable=False)        # "entrada" ou "saida"
    quantidade = Column(Integer, nullable=False)
    data = Column(DateTime, default=datetime.utcnow, nullable=False)

    produto = relationship("Produto", back_populates="movimentacoes")
