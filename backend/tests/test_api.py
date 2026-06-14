import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app
from app.models.categoria import Categoria
from app.models.produto import Produto
from app.models.movimentacao import Movimentacao

from sqlalchemy.pool import StaticPool

# Configuração do banco de dados SQLite em memória com StaticPool para compartilhar a conexão e evitar exclusão das tabelas
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    # Cria as tabelas antes do teste
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Remove as tabelas após o teste
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    # Sobrescreve a dependência de sessão de banco do FastAPI
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def test_criar_produto_sem_estoque_inicial(client):
    response = client.post(
        "/produtos/",
        json={"nome": "Teclado Mecânico", "categoria_nome": "Tecnologia", "quantidade": 0, "estoque_minimo": 5}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["nome"] == "Teclado Mecânico"
    assert data["quantidade"] == 0
    assert data["estoque_minimo"] == 5

def test_criar_produto_com_estoque_inicial(client):
    response = client.post(
        "/produtos/",
        json={"nome": "Mouse Gamer", "categoria_nome": "Tecnologia", "quantidade": 10, "estoque_minimo": 3}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["nome"] == "Mouse Gamer"
    # Saldo derivado deve calcular 10 a partir da movimentação de entrada inicial
    assert data["quantidade"] == 10

def test_registrar_entrada_aumenta_saldo(client):
    # 1. Cria produto com estoque 0
    resp_prod = client.post(
        "/produtos/",
        json={"nome": "Fone Bluetooth", "categoria_nome": "Tecnologia", "quantidade": 0, "estoque_minimo": 5}
    )
    prod_id = resp_prod.json()["id"]

    # 2. Registra entrada de 15 unidades
    resp_mov = client.post(
        f"/produtos/{prod_id}/movimentacoes",
        json={"tipo": "entrada", "quantidade": 15}
    )
    assert resp_mov.status_code == 200
    
    # 3. Consulta produto e verifica saldo recalculado
    resp_prod_after = client.get(f"/produtos/{prod_id}")
    assert resp_prod_after.json()["quantidade"] == 15

def test_impedir_saida_maior_que_saldo_atual(client):
    # 1. Cria produto com estoque 5
    resp_prod = client.post(
        "/produtos/",
        json={"nome": "Caneta Azul", "categoria_nome": "Escritório", "quantidade": 5, "estoque_minimo": 2}
    )
    prod_id = resp_prod.json()["id"]

    # 2. Tenta registrar saída de 10 unidades (excede saldo de 5)
    resp_mov = client.post(
        f"/produtos/{prod_id}/movimentacoes",
        json={"tipo": "saida", "quantidade": 10}
    )
    assert resp_mov.status_code == 400
    assert "maior que o saldo atual" in resp_mov.json()["detail"]

def test_alertas_estoque_baixo(client):
    # 1. Cria produto abaixo do estoque mínimo
    client.post(
        "/produtos/",
        json={"nome": "Café 500g", "categoria_nome": "Alimentos", "quantidade": 2, "estoque_minimo": 5}
    )
    # 2. Cria produto acima do estoque mínimo
    client.post(
        "/produtos/",
        json={"nome": "Chocolate 100g", "categoria_nome": "Alimentos", "quantidade": 20, "estoque_minimo": 5}
    )

    # 3. Verifica se apenas o café está na lista de alertas
    resp_alertas = client.get("/produtos/alertas")
    assert resp_alertas.status_code == 200
    alertas = resp_alertas.json()
    
    assert len(alertas) == 1
    assert alertas[0]["nome"] == "Café 500g"
