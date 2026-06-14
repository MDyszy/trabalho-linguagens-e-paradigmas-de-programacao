from contextlib import asynccontextmanager
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.database import engine, Base
from app.routers import produto_router, categoria_router, movimentacao_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Aviso: Não foi possível criar as tabelas no PostgreSQL ({e}). "
              f"Isso é normal se você estiver executando testes locais sem o container do banco rodando.")
    yield

app = FastAPI(
    title="Sistema de Controle de Estoque (LPP)",
    description="API para Controle de Estoque utilizando Paradigma Orientado a Dados.",
    version="1.0.0",
    lifespan=lifespan
)

# Configuração de CORS para permitir acesso de qualquer origem
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclui os routers da API
app.include_router(produto_router.router)
app.include_router(categoria_router.router)
app.include_router(movimentacao_router.router)

# Rota para servir o Dashboard Frontend
@app.get("/")
def read_index():
    static_file_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if not os.path.exists(static_file_path):
        raise HTTPException(
            status_code=404,
            detail="Interface Web não inicializada. Crie o index.html na pasta static.",
        )
    return FileResponse(static_file_path)

# Monta o diretório de arquivos estáticos (/static/style.css, /static/app.js)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/static", StaticFiles(directory=static_dir), name="static")
