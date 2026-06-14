from pydantic import BaseModel, ConfigDict, Field

# Create -> O que o usuário mandar para criar
class ProdutoCreate(BaseModel):
    nome: str = Field(..., min_length=1, max_length=100)
    categoria_nome: str = Field(..., min_length=1, max_length=100)
    quantidade: int = Field(default=0, ge=0)          # estoque inicial -> vira a 1ª movimentação de entrada
    estoque_minimo: int = Field(..., ge=1)
    imagem_url: str | None = Field(default=None, max_length=500)

# Read -> O que a API retorna
class ProdutoResponse(BaseModel):
    id: int
    nome: str
    categoria_id: int
    quantidade: int              # saldo DERIVADO das movimentações (não é coluna)
    estoque_minimo: int
    imagem_url: str | None = None

    model_config = ConfigDict(from_attributes=True)
