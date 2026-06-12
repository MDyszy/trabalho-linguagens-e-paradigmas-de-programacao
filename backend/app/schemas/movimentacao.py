from datetime import datetime
from pydantic import BaseModel
from app.domain.estoque import TipoMovimentacao


# Create -> o que o usuário manda para registrar uma movimentação
class MovimentacaoCreate(BaseModel):
    tipo: TipoMovimentacao
    quantidade: int


# Read -> o que a API retorna
class MovimentacaoResponse(BaseModel):
    id: int
    produto_id: int
    tipo: TipoMovimentacao
    quantidade: int
    data: datetime

    class Config:
        from_attributes = True
