"""Motor de recomendação (SIMULADO) da próxima melhor ação.

Para o MVP, a recomendação sai de regras de negócio simples. A interface
chama apenas `gerar_recomendacao`; para plugar um modelo real (Azure OpenAI,
GraphRAG, etc.) basta trocar o corpo de `_regras` mantendo o formato do
dicionário de retorno.
"""
from __future__ import annotations

import time
from typing import Callable

from formatos import brl

ETAPAS = [
    "Lendo perfil e evidências do cliente",
    "Estimando o valor incremental de cada ação",
    "Aplicando a restrição de orçamento",
    "Montando a recomendação",
]


class RecomendacaoErro(Exception):
    """Falha ao gerar a recomendação (serviço indisponível, tempo esgotado, etc.)."""


def gerar_recomendacao(
    cliente: dict,
    *,
    latencia: float = 1.5,
    falhar: bool = False,
    ao_avancar: Callable[[int, str], None] | None = None,
) -> dict:
    """Gera a recomendação de próxima melhor ação para um cliente.

    `latencia` simula o tempo de resposta total; `falhar` simula uma falha no
    meio do processo, para exercitar o estado de erro da interface;
    `ao_avancar(indice, rotulo)` é chamado a cada etapa, para a barra de progresso.
    """
    passo = max(latencia, 0) / len(ETAPAS)
    for i, etapa in enumerate(ETAPAS):
        if ao_avancar:
            ao_avancar(i, etapa)
        if passo:
            time.sleep(passo)
        if falhar and i == 2:
            raise RecomendacaoErro("O serviço de recomendação não respondeu (falha simulada).")
    return _regras(cliente)


def _regras(c: dict) -> dict:
    risco, clv, seg = float(c["risco"]), float(c["clv"]), str(c["segmento"])
    em_risco = clv * risco / 100

    if seg == "Corporativo" and risco >= 60:
        acao = ("Reunião executiva de retenção com o gestor de contas e proposta de renovação "
                "antecipada do contrato, com condições comerciais ajustadas ao volume de voos.")
        canal, prazo, custo, efeito = "Gerente de contas (presencial ou vídeo)", "Em até 7 dias", 0.02 * clv, 0.40
    elif seg == "Corporativo":
        acao = "Revisão trimestral de negócios com relatório de economia e uso do contrato."
        canal, prazo, custo, efeito = "Gerente de contas", "Em até 30 dias", 0.005 * clv, 0.15
    elif seg == "Influenciador" and risco >= 50:
        acao = "Convite para experiência exclusiva (upgrade e embarque prioritário) com ação de conteúdo combinada."
        canal, prazo, custo, efeito = "Relacionamento com parceiros", "Em até 14 dias", 0.05 * clv, 0.35
    elif seg == "Executivo" and risco >= 50:
        acao = "Oferta de upgrade de nível por 90 dias e contato do atendimento exclusivo."
        canal, prazo, custo, efeito = "Atendimento exclusivo", "Em até 10 dias", 0.03 * clv, 0.30
    elif risco >= 60:
        acao = f"Campanha de reativação com bônus de pontos nos próximos voos da rota {c['rota']}."
        canal, prazo, custo, efeito = "E-mail e aplicativo", "Em até 5 dias", 0.01 * clv, 0.20
    else:
        acao = "Manter o relacionamento regular, sem ação extra de retenção."
        canal, prazo, custo, efeito = "Comunicação padrão", "Sem urgência", 0.0, 0.0

    ganho = em_risco * efeito
    return {
        "acao": acao,
        "canal": canal,
        "prazo": prazo,
        "custo_estimado": round(custo),
        "ganho_incremental": round(ganho),
        "roi": (ganho / custo) if custo else None,
        "confianca": round(min(0.9, 0.55 + 0.04 * int(c.get("reclamacoes_90d", 0)) + 0.002 * risco), 2),
        "justificativa": (
            f"Cliente com CLV de {brl(clv)} e risco de perda de {risco:.0f}%, o que deixa cerca de "
            f"{brl(em_risco)} em risco. A ação escolhida tem o melhor retorno esperado dentro do "
            f"orçamento de retenção do segmento {seg.lower()}."
        ),
        "simulado": True,
    }
