"""Gráficos Plotly do Co-Piloto de Valor."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dados import NIVEIS, PESOS, ROTULOS_FATORES, SEGMENTOS
from formatos import brl

CORES_SEGMENTO = {
    "Corporativo": "#2f6fdb",
    "Executivo": "#8a5cf0",
    "Influenciador": "#e8890c",
    "Lazer frequente": "#17a58a",
    "Lazer ocasional": "#8c96a8",
}
COR_RISCO = "#e0392d"
COR_SEGURO = "#5b8def"
LIMIAR_RISCO_ALTO = 70
LIMIAR_SCORE_ALTO = 60

_CONFIG_BASE = dict(margin=dict(l=8, r=8, t=8, b=8), legend_title_text="")


def fig_score_risco(df: pd.DataFrame, selecionado: str | None = None) -> go.Figure:
    """Score de valor × risco; tamanho = CLV; destaca o cliente selecionado."""
    dados = df.assign(clv_fmt=df["clv"].map(brl))
    fig = px.scatter(
        dados,
        x="risco",
        y="score",
        size="clv",
        size_max=26,
        color="segmento",
        color_discrete_map=CORES_SEGMENTO,
        category_orders={"segmento": SEGMENTOS},
        custom_data=["cliente_id", "nome", "clv_fmt", "nivel"],
        labels={"risco": "Risco de perda (%)", "score": "Score de valor (0–100)"},
    )
    fig.update_traces(
        marker=dict(opacity=0.78, line=dict(width=0.6, color="white")),
        hovertemplate=(
            "<b>%{customdata[1]}</b><br>Risco %{x:.0f}% · Score %{y:.0f}"
            "<br>CLV %{customdata[2]} · %{customdata[3]}<extra></extra>"
        ),
    )
    fig.add_vline(x=LIMIAR_RISCO_ALTO, line_dash="dash", line_color="rgba(150,150,150,.7)")
    fig.add_hline(y=LIMIAR_SCORE_ALTO, line_dash="dash", line_color="rgba(150,150,150,.7)")
    fig.add_annotation(
        x=99, y=99, xanchor="right", yanchor="top", showarrow=False,
        text="<b>Proteger primeiro</b><br>valor alto + risco alto",
        font=dict(color=COR_RISCO, size=12), align="right",
    )
    if selecionado is not None and selecionado in set(dados["cliente_id"]):
        r = dados.loc[dados["cliente_id"] == selecionado].iloc[0]
        fig.add_trace(go.Scatter(
            x=[r["risco"]], y=[r["score"]], mode="markers", hoverinfo="skip", showlegend=False,
            marker=dict(size=38, symbol="circle-open", line=dict(width=3, color="#111111")),
        ))
    fig.update_layout(
        **_CONFIG_BASE, height=430,
        xaxis=dict(range=[0, 102], ticksuffix="%", gridcolor="rgba(150,150,150,.2)"),
        yaxis=dict(range=[0, 102], gridcolor="rgba(150,150,150,.2)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0),
    )
    return fig


def fig_clv_nivel(df: pd.DataFrame) -> go.Figure:
    """Distribuição do CLV por nível (escala logarítmica por causa da assimetria)."""
    fig = px.box(
        df, x="nivel", y="clv", category_orders={"nivel": NIVEIS}, points="outliers", log_y=True,
        labels={"nivel": "", "clv": "CLV (R$, escala log)"},
    )
    fig.update_traces(marker_color="#2f6fdb", line_color="#2f6fdb", fillcolor="rgba(47,111,219,.25)")
    fig.update_layout(**_CONFIG_BASE, height=250, showlegend=False,
                      yaxis=dict(gridcolor="rgba(150,150,150,.2)"))
    return fig


def fig_segmentos(df: pd.DataFrame) -> go.Figure:
    """CLV por segmento dividido em valor em risco e valor protegido."""
    agg = (
        df.groupby("segmento", observed=True)
        .agg(clv=("clv", "sum"), em_risco=("valor_em_risco", "sum"), n=("cliente_id", "count"))
        .reindex([s for s in SEGMENTOS if s in set(df["segmento"])])
    )
    agg["protegido"] = agg["clv"] - agg["em_risco"]
    fig = go.Figure()
    fig.add_bar(
        y=agg.index, x=agg["em_risco"], orientation="h", name="Valor em risco",
        marker_color=COR_RISCO, text=agg["em_risco"].map(lambda v: brl(v, True)), textposition="auto",
        customdata=agg["n"], hovertemplate="%{y}: %{text} em risco · %{customdata} clientes<extra></extra>",
    )
    fig.add_bar(
        y=agg.index, x=agg["protegido"], orientation="h", name="Valor protegido",
        marker_color=COR_SEGURO, text=agg["protegido"].map(lambda v: brl(v, True)), textposition="auto",
        customdata=agg["n"], hovertemplate="%{y}: %{text} protegido · %{customdata} clientes<extra></extra>",
    )
    fig.update_layout(
        **_CONFIG_BASE, height=250, barmode="stack",
        yaxis=dict(autorange="reversed"), xaxis=dict(title="CLV (R$)", gridcolor="rgba(150,150,150,.2)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    return fig


def fig_fatores(cliente: pd.Series) -> go.Figure:
    """Contribuição de cada fator ao score do cliente, contra o máximo possível."""
    chaves = list(PESOS)
    rotulos = [ROTULOS_FATORES[k] for k in chaves]
    maximos = [PESOS[k] * 100 for k in chaves]
    valores = [float(cliente[f"f_{k}"]) for k in chaves]
    fig = go.Figure()
    fig.add_bar(y=rotulos, x=maximos, orientation="h", name="Máximo possível",
                marker_color="rgba(140,150,168,.28)", hoverinfo="skip")
    fig.add_bar(
        y=rotulos, x=valores, orientation="h", name="Pontos do cliente", marker_color="#2f6fdb",
        text=[f"{v:.0f} de {m:.0f}" for v, m in zip(valores, maximos)], textposition="inside",
        insidetextanchor="start", hovertemplate="%{y}: %{x:.1f} pontos<extra></extra>",
    )
    fig.update_layout(
        **_CONFIG_BASE, height=260, barmode="overlay",
        yaxis=dict(autorange="reversed"), xaxis=dict(title="Pontos do score", range=[0, 31]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    return fig
