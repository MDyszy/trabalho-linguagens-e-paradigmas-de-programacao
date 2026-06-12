import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://usuario:senha@db:5432/estoque")

engine = create_engine(DATABASE_URL) #gerenciamento de conexão com o banco
SessionLocal = sessionmaker(bind=engine) #unidade de trabalho

class Base(DeclarativeBase): #classe que os models herdam
    pass

def get_db(): # função injetada nos endpoints para fornecer sessão
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()