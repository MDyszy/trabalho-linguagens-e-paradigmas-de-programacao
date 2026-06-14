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

def test_frontend_dashboard_e_assets(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "DataStock" in response.text

    app_js = client.get("/static/app.js")
    assert app_js.status_code == 200
    assert "fetchProducts" in app_js.text

    style_css = client.get("/static/style.css")
    assert style_css.status_code == 200
    assert "app-container" in style_css.text

def test_buscar_categoria_inexistente_retorna_404(client):
    response = client.get("/categorias/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Categoria não encontrada"

def test_historico_produto_inexistente_retorna_404(client):
    response = client.get("/produtos/999/movimentacoes")
    assert response.status_code == 404
    assert response.json()["detail"] == "Produto não encontrado"

def test_criar_produto_com_estoque_minimo_zero_retorna_422(client):
    response = client.post(
        "/produtos/",
        json={"nome": "Produto Inválido", "categoria_nome": "Teste", "quantidade": 0, "estoque_minimo": 0}
    )
    assert response.status_code == 422

def test_fluxo_ponta_a_ponta_produto_movimentacoes_alerta_e_exports(client):
    resp_prod = client.post(
        "/produtos/",
        json={"nome": "Produto E2E", "categoria_nome": "Fluxo", "quantidade": 7, "estoque_minimo": 7}
    )
    assert resp_prod.status_code == 200
    produto = resp_prod.json()
    produto_id = produto["id"]
    assert produto["quantidade"] == 7

    categorias = client.get("/categorias/")
    assert categorias.status_code == 200
    assert any(c["nome"] == "Fluxo" for c in categorias.json())

    resp_entrada = client.post(
        f"/produtos/{produto_id}/movimentacoes",
        json={"tipo": "entrada", "quantidade": 3}
    )
    assert resp_entrada.status_code == 200

    resp_saida = client.post(
        f"/produtos/{produto_id}/movimentacoes",
        json={"tipo": "saida", "quantidade": 4}
    )
    assert resp_saida.status_code == 200

    resp_prod_after = client.get(f"/produtos/{produto_id}")
    assert resp_prod_after.status_code == 200
    assert resp_prod_after.json()["quantidade"] == 6

    resp_historico = client.get(f"/produtos/{produto_id}/movimentacoes")
    assert resp_historico.status_code == 200
    historico = resp_historico.json()
    assert [m["tipo"] for m in historico] == ["entrada", "entrada", "saida"]

    resp_alertas = client.get("/produtos/alertas")
    assert resp_alertas.status_code == 200
    assert any(p["id"] == produto_id for p in resp_alertas.json())

    resp_inventario = client.get("/produtos/exportar/inventario")
    assert resp_inventario.status_code == 200
    assert "text/csv" in resp_inventario.headers["content-type"]
    assert "Produto E2E" in resp_inventario.text

    resp_export_mov = client.get(f"/produtos/{produto_id}/exportar/movimentacoes")
    assert resp_export_mov.status_code == 200
    assert "text/csv" in resp_export_mov.headers["content-type"]
    assert "ENTRADA" in resp_export_mov.text
    assert "SAIDA" in resp_export_mov.text

def test_seed_popula_banco_e_e_idempotente(client):
    response = client.post("/produtos/seed")
    assert response.status_code == 200
    assert "Seed completo" in response.json()["message"]

    produtos = client.get("/produtos/")
    assert produtos.status_code == 200
    assert len(produtos.json()) == 6

    segunda_execucao = client.post("/produtos/seed")
    assert segunda_execucao.status_code == 200
    assert "Seed abortado" in segunda_execucao.json()["message"]
