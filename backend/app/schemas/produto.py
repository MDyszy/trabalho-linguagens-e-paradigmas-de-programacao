from pydantic import BaseModel

# Create -> O que o usuário mandar para criar
class ProdutoCreate(BaseModel):
    nome: str
    categoria_nome: str
    quantidade: int = 0          # estoque inicial -> vira a 1ª movimentação de entrada
    estoque_minimo: int
    imagem_url: str | None = None

# Read -> O que a API retorna
class ProdutoResponse(BaseModel):
    id: int
    nome: str
    categoria_id: int
    quantidade: int              # saldo DERIVADO das movimentações (não é coluna)
    estoque_minimo: int
    imagem_url: str | None = None

    class Config:
        from_attributes = True
