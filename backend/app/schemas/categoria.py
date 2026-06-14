from pydantic import BaseModel, ConfigDict, Field

# Create -> O que o usuário mandar para criar
class CategoriaCreate(BaseModel):
    nome: str = Field(..., min_length=1, max_length=100)

# Read -> O que a API retorna
class CategoriaResponse(BaseModel):
    id: int
    nome: str

    model_config = ConfigDict(from_attributes=True)

# Update -> O que o usuário manda para atualizar
class CategoriaUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=100)