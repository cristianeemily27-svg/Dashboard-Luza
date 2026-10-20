"""Funções puras que extraem o cliente selecionado a partir do estado dos widgets."""
from __future__ import annotations

from typing import Sequence


def id_da_tabela(estado, ids: Sequence[str]) -> str | None:
    """Estado de st.dataframe(on_select=...) -> id do cliente da primeira linha selecionada."""
    try:
        linhas = estado["selection"]["rows"]
    except (KeyError, TypeError):
        return None
    if linhas and 0 <= linhas[0] < len(ids):
        return ids[linhas[0]]
    return None


def id_do_grafico(estado) -> str | None:
    """Estado de st.plotly_chart(on_select=...) -> id do cliente do primeiro ponto selecionado."""
    try:
        pontos = estado["selection"]["points"]
    except (KeyError, TypeError):
        return None
    for ponto in pontos or []:
        dados = ponto.get("customdata")
        if dados:
            return dados[0]
    return None
