from fastapi import FastAPI
from app.database import engine, Base
from app.routers import produto_router, categoria_router, movimentacao_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistema de Estoque")

app.include_router(produto_router.router)
app.include_router(categoria_router.router)
app.include_router(movimentacao_router.router)
