import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./estoque.db")

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args) #gerenciamento de conexão com o banco
SessionLocal = sessionmaker(bind=engine) #unidade de trabalho

class Base(DeclarativeBase): #classe que os models herdam
    pass

def get_db(): # função injetada nos endpoints para fornecer sessão
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()