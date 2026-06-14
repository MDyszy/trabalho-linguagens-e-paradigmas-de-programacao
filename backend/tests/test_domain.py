from app.domain.estoque import saldo, em_alerta, pode_retirar, delta, TipoMovimentacao

class DummyMovimentacao:
    def __init__(self, tipo: str, quantidade: int):
        self.tipo = tipo
        self.quantidade = quantidade

def test_delta_calcula_corretamente():
    assert delta("entrada", 10) == 10
    assert delta("saida", 5) == -5

def test_saldo_inicial_zero():
    movimentacoes = []
    assert saldo(movimentacoes) == 0

def test_saldo_acumulado_correto():
    movimentacoes = [
        DummyMovimentacao(TipoMovimentacao.ENTRADA, 50),
        DummyMovimentacao(TipoMovimentacao.SAIDA, 20),
        DummyMovimentacao(TipoMovimentacao.ENTRADA, 10),
        DummyMovimentacao(TipoMovimentacao.SAIDA, 5),
    ]
    # 50 - 20 + 10 - 5 = 35
    assert saldo(movimentacoes) == 35

def test_em_alerta_funcionamento():
    # Saldo menor que estoque mínimo -> Alerta
    assert em_alerta(saldo_atual=5, estoque_minimo=10) is True
    # Saldo igual ou maior que estoque mínimo -> Seguro
    assert em_alerta(saldo_atual=10, estoque_minimo=10) is False
    assert em_alerta(saldo_atual=15, estoque_minimo=10) is False

def test_pode_retirar_funcionamento():
    # Quantidade menor ou igual ao saldo -> Pode retirar
    assert pode_retirar(saldo_atual=20, quantidade=15) is True
    assert pode_retirar(saldo_atual=20, quantidade=20) is True
    # Quantidade maior que o saldo -> Não pode retirar
    assert pode_retirar(saldo_atual=20, quantidade=25) is False
