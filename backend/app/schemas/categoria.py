from pydantic import BaseModel

# Create -> O que o usuário mandar para criar
class CategoriaCreate(BaseModel):
    nome: str

# Read -> O que a API retorna
class CategoriaResponse(BaseModel):
    id: int
    nome: str

    class Config:
        from_attributes = True

# Update -> O que o usuário manda para atualizar
class CategoriaUpdate(BaseModel):
    nome: str | None = None