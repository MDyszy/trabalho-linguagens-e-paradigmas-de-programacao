"""Lógica de estoque em funções puras (paradigma orientado a dados).

Estas funções não conhecem banco de dados nem framework: recebem dados e
devolvem dados, sem efeitos colaterais. O saldo de um produto é DERIVADO do
histórico de movimentações — um fold (reduce) sobre eventos imutáveis — em vez
de ser um campo mutável guardado no banco.
"""
from enum import Enum
from functools import reduce


class TipoMovimentacao(str, Enum):
    ENTRADA = "entrada"
    SAIDA = "saida"

def delta(tipo: str, quantidade: int) -> int:
    """Efeito de uma movimentação no saldo: entrada soma, saída subtrai."""
    return quantidade if tipo == TipoMovimentacao.ENTRADA else -quantidade

def saldo(movimentacoes) -> int:
    """Saldo atual = soma dos deltas de todas as movimentações (fold)."""
    return reduce(lambda acc, m: acc + delta(m.tipo, m.quantidade), movimentacoes, 0)

def em_alerta(saldo_atual: int, estoque_minimo: int) -> bool:
    """Produto em alerta quando o saldo está abaixo do estoque mínimo."""
    return saldo_atual < estoque_minimo

def pode_retirar(saldo_atual: int, quantidade: int) -> bool:
    """Só permite saída se houver saldo suficiente (não deixa o saldo negativo)."""
    return quantidade <= saldo_atual
