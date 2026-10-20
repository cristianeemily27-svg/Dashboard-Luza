"""Co-Piloto de Valor — interface principal do MVP (Streamlit + Plotly).

Rodar com:  streamlit run app.py
"""
from __future__ import annotations

import hashlib
import os

import pandas as pd
import streamlit as st

import dados
import graficos
import recomendacao
import selecao
from formatos import brl

st.set_page_config(page_title="Co-Piloto de Valor", page_icon="🧭", layout="wide")
st.markdown(
    "<style>.block-container{padding-top:1.8rem;} [data-testid='stMetricValue']{font-size:1.6rem;}</style>",
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------- dados
@st.cache_data(show_spinner=False)
def carregar() -> pd.DataFrame:
    return dados.gerar_dados()


with st.spinner("Carregando a carteira de clientes..."):
    df = carregar()

ROTAS_DISPONIVEIS = sorted(df["rota"].unique())
# chave do estado -> (coluna, opções). Lista vazia = "todos".
FILTROS = {
    "f_segmento": ("segmento", dados.SEGMENTOS),
    "f_risco": ("faixa_risco", dados.FAIXAS_RISCO),
    "f_prioridade": ("prioridade", dados.PRIORIDADES),
    "f_rota": ("rota", ROTAS_DISPONIVEIS),
    "f_nivel": ("nivel", dados.NIVEIS),
}
for _chave in FILTROS:
    st.session_state.setdefault(_chave, [])
st.session_state.setdefault("f_busca", "")
st.session_state.setdefault("recs", {})


# --------------------------------------------------------------------------- callbacks
def limpar_filtros() -> None:
    for chave in FILTROS:
        st.session_state[chave] = []
    st.session_state["f_busca"] = ""


def atalho_corporativos_em_risco() -> None:
    limpar_filtros()
    st.session_state["f_segmento"] = ["Corporativo"]
    st.session_state["f_risco"] = ["Alto"]


def abrir_cliente(cliente_id: str) -> None:
    st.session_state["cliente_sel"] = cliente_id


def ao_selecionar_tabela(chave: str, ids: list[str]) -> None:
    escolhido = selecao.id_da_tabela(st.session_state.get(chave), ids)
    if escolhido:
        st.session_state["cliente_sel"] = escolhido


def ao_selecionar_grafico(chave: str) -> None:
    escolhido = selecao.id_do_grafico(st.session_state.get(chave))
    if escolhido:
        st.session_state["cliente_sel"] = escolhido


# --------------------------------------------------------------------------- barra lateral
with st.sidebar:
    st.header("Filtros")
    st.button("🔎 Corporativos em risco alto", on_click=atalho_corporativos_em_risco, type="primary",
              width="stretch", help="Aplica os filtros Segmento = Corporativo e Risco = Alto.")
    st.text_input("Buscar cliente", key="f_busca", placeholder="Nome ou código (ex.: CLI-0001)")
    st.multiselect("Segmento", dados.SEGMENTOS, key="f_segmento", placeholder="Todos")
    st.multiselect("Faixa de risco", dados.FAIXAS_RISCO, key="f_risco", placeholder="Todas",
                   help="Alto: 70% ou mais · Médio: 40% a 69% · Baixo: abaixo de 40%.")
    st.multiselect("Prioridade", dados.PRIORIDADES, key="f_prioridade", placeholder="Todas")
    st.multiselect("Rota", ROTAS_DISPONIVEIS, key="f_rota", placeholder="Todas")
    st.multiselect("Nível", dados.NIVEIS, key="f_nivel", placeholder="Todos")
    st.button("Limpar filtros", on_click=limpar_filtros, width="stretch")
    with st.expander("Modo demonstração"):
        st.toggle("Simular falha na recomendação", key="simular_falha")
        st.slider("Latência simulada (s)", 0.0, 5.0, float(os.getenv("COPILOTO_LATENCIA", "1.5")), 0.5,
                  key="latencia")


def filtrar(base: pd.DataFrame) -> pd.DataFrame:
    mascara = pd.Series(True, index=base.index)
    for chave, (coluna, _) in FILTROS.items():
        escolhidos = st.session_state[chave]
        if escolhidos:
            mascara &= base[coluna].isin(escolhidos)
    busca = st.session_state["f_busca"].strip().lower()
    if busca:
        mascara &= (base["nome"].str.lower().str.contains(busca, regex=False)
                    | base["cliente_id"].str.lower().str.contains(busca, regex=False))
    return base[mascara]


dff = filtrar(df).sort_values("valor_em_risco", ascending=False).reset_index(drop=True)
estado_filtros = repr([st.session_state[k] for k in FILTROS] + [st.session_state["f_busca"]])
chave_filtros = hashlib.md5(estado_filtros.encode()).hexdigest()[:8]  # reinicia seleção da tabela/gráfico

# --------------------------------------------------------------------------- cabeçalho
st.title("🧭 Co-Piloto de Valor")
st.caption("Carteira de clientes de alto valor · protótipo com dados 100% sintéticos")

if dff.empty:
    st.warning("Nenhum cliente encontrado com esses filtros. Ajuste ou limpe os filtros na barra lateral.")
    st.stop()

ids = dff["cliente_id"].tolist()
if st.session_state.get("cliente_sel") not in ids:
    st.session_state["cliente_sel"] = ids[0]  # padrão: maior valor em risco

n_alto = int((dff["faixa_risco"] == "Alto").sum())
m1, m2, m3, m4 = st.columns(4)
m1.metric("Clientes na seleção", f"{len(dff)}", border=True, help=f"{len(df)} clientes na carteira.")
m2.metric("CLV total", brl(dff["clv"].sum(), True), border=True,
          help="Valor do cliente ao longo da vida: gasto direto projetado + valor de influência.")
m3.metric("Valor em risco", brl(dff["valor_em_risco"].sum(), True), border=True,
          help="CLV multiplicado pela probabilidade de perda, somado na seleção.")
m4.metric("Clientes em risco alto", f"{n_alto}", f"{n_alto / len(dff):.0%} da seleção",
          delta_color="off", border=True)

# --------------------------------------------------------------------------- alerta corporativo
criticos = dff[(dff["segmento"] == "Corporativo") & (dff["risco"] >= graficos.LIMIAR_RISCO_ALTO)].head(3)
if not criticos.empty:
    with st.container(border=True):
        st.markdown("**⚠️ Contas corporativas em risco alto** · maior valor em risco primeiro")
        for _, r in criticos.iterrows():
            a, b, c, d = st.columns([4, 2, 2, 2], vertical_alignment="center")
            a.markdown(f"**{r['nome']}**  \n:gray[{r['nivel']} · {r['rota']}]")
            b.markdown(f"Risco **{r['risco']:.0f}%**")
            c.markdown(f"CLV **{brl(r['clv'], True)}**")
            d.button("Abrir perfil", key=f"abrir_{r['cliente_id']}", on_click=abrir_cliente,
                     args=(r["cliente_id"],), width="stretch")

# --------------------------------------------------------------------------- tabela + perfil
ICONE_PRIORIDADE = {"Alta": "🔴 Alta", "Média": "🟠 Média", "Baixa": "⚪ Baixa"}
vista = pd.DataFrame({
    "Cliente": dff["nome"],
    "Segmento": dff["segmento"].astype(str),
    "Nível": dff["nivel"].astype(str),
    "Rota": dff["rota"],
    "Prioridade": dff["prioridade"].astype(str).map(ICONE_PRIORIDADE),
    "Risco": dff["risco"],
    "Score": dff["score"],
    "CLV (R$)": dff["clv"],
})
col_tabela, col_perfil = st.columns([3, 2], gap="large")

with col_tabela:
    st.subheader("Clientes")
    chave_tabela = f"tabela_{chave_filtros}"
    st.dataframe(
        vista,
        key=chave_tabela,
        hide_index=True,
        height=470,
        on_select=lambda: ao_selecionar_tabela(chave_tabela, ids),
        selection_mode="single-row",
        column_config={
            "Risco": st.column_config.ProgressColumn("Risco", min_value=0, max_value=100, format="%d%%"),
            "Score": st.column_config.NumberColumn("Score", format="%d"),
            "CLV (R$)": st.column_config.NumberColumn("CLV (R$)", format="compact"),
        },
    )
    st.caption(f"{len(dff)} clientes, do maior para o menor valor em risco. "
               "Clique em uma linha para abrir o perfil ao lado.")


def render_recomendacao(c: pd.Series) -> None:
    recs: dict = st.session_state["recs"]
    cid = c["cliente_id"]
    rec = recs.get(cid)
    gerar = st.button("Gerar novamente" if rec and "erro" not in rec else "Gerar recomendação",
                      key="btn_gerar", type="primary")
    if gerar:
        with st.status("Gerando recomendação...", expanded=True) as status:
            try:
                recs[cid] = recomendacao.gerar_recomendacao(
                    c.to_dict(),
                    latencia=st.session_state["latencia"],
                    falhar=st.session_state.get("simular_falha", False),
                    ao_avancar=lambda i, t: st.write(f"{i + 1}/{len(recomendacao.ETAPAS)} · {t}"),
                )
                status.update(label="Recomendação pronta", state="complete", expanded=False)
            except recomendacao.RecomendacaoErro as erro:
                recs[cid] = {"erro": str(erro)}
                status.update(label="Falha ao gerar a recomendação", state="error", expanded=False)
        st.rerun()  # redesenha com o resultado (ou o erro) já guardado e o rótulo do botão atualizado

    if rec is None:
        st.info("Ainda não há recomendação para este cliente. Clique em **Gerar recomendação** "
                "para calcular a próxima melhor ação.")
    elif "erro" in rec:
        st.error(f"Não foi possível gerar a recomendação. {rec['erro']} Clique em "
                 "**Gerar recomendação** para tentar de novo.")
    else:
        with st.container(border=True):
            st.markdown(f"**Próxima melhor ação**  \n{rec['acao']}")
            st.caption(f"{rec['canal']} · {rec['prazo']}")
            k1, k2, k3 = st.columns(3)
            k1.metric("Custo estimado", brl(rec["custo_estimado"], True))
            k2.metric("Ganho esperado", brl(rec["ganho_incremental"], True))
            k3.metric("Retorno (ROI)", f"{rec['roi']:.0f}x" if rec["roi"] else "—")
            st.progress(rec["confianca"], text=f"Confiança do modelo: {rec['confianca']:.0%}")
            st.write(rec["justificativa"])
        st.caption("Prévia do MVP: recomendação simulada por regras de negócio, sem modelo de IA real.")


TAGS_EVIDENCIA = {
    "risco": ":red[▲ Risco]",
    "valor": ":green[● Valor]",
    "influencia": ":blue[◆ Influência]",
    "contexto": ":gray[○ Contexto]",
}


def render_perfil(c: pd.Series) -> None:
    st.subheader(c["nome"])
    cor_risco = {"Alto": "red", "Médio": "orange", "Baixo": "green"}[str(c["faixa_risco"])]
    st.markdown(
        f":blue-badge[{c['segmento']}] :violet-badge[{c['nivel']}] "
        f":{cor_risco}-badge[Risco {str(c['faixa_risco']).lower()}] :gray-badge[Prioridade {str(c['prioridade']).lower()}]"
    )
    p1, p2, p3 = st.columns(3)
    p1.metric("Score de valor", f"{c['score']:.0f}", border=True)
    p2.metric("Risco de perda", f"{c['risco']:.0f}%", border=True)
    p3.metric("CLV", brl(c["clv"], True), border=True)
    detalhes = (f"{c['cliente_id']} · rota {c['rota']} · {c['voos_12m']} voos em 12 meses · "
                f"último voo há {c['dias_ultimo_voo']} dias · ticket médio {brl(c['ticket_medio'])}")
    if pd.notna(c["contrato_vence_dias"]):
        detalhes += f" · contrato vence em {c['contrato_vence_dias']:.0f} dias"
    st.caption(detalhes)

    aba_evid, aba_score, aba_rec = st.tabs(["Evidências", "Score explicado", "Recomendação"])
    with aba_evid:
        for e in dados.evidencias(c, df):
            st.markdown(f"{TAGS_EVIDENCIA[e['tipo']]}  {e['texto']}")
            st.caption(f"Fonte: {e['fonte']} (sintético)")
    with aba_score:
        st.plotly_chart(graficos.fig_fatores(c), width="stretch", config={"displayModeBar": False})
        st.caption(f"Score {c['score']:.0f} de 100 = soma dos pontos de cada fator. A barra clara mostra o "
                   "máximo que o fator pode render; o risco é calculado à parte, a partir de queda de "
                   "interações, inatividade, reclamações, satisfação e vencimento de contrato.")
    with aba_rec:
        render_recomendacao(c)


with col_perfil:
    cliente = dff.loc[dff["cliente_id"] == st.session_state["cliente_sel"]].iloc[0]
    render_perfil(cliente)

# --------------------------------------------------------------------------- gráficos
st.divider()
st.subheader("Análises da carteira")
g_esq, g_dir = st.columns([3, 2], gap="large")
with g_esq:
    st.markdown("**Score de valor × risco**")
    st.caption("Tamanho = CLV · cor = segmento · clique em um ponto para abrir o perfil · círculo preto = cliente aberto")
    chave_disp = f"dispersao_{chave_filtros}"
    st.plotly_chart(
        graficos.fig_score_risco(dff, st.session_state["cliente_sel"]),
        key=chave_disp,
        on_select=lambda: ao_selecionar_grafico(chave_disp),
        selection_mode="points",
        width="stretch",
        config={"displayModeBar": False},
    )
with g_dir:
    st.markdown("**CLV por nível**")
    st.plotly_chart(graficos.fig_clv_nivel(dff), width="stretch", config={"displayModeBar": False})
    st.markdown("**Valor em risco por segmento**")
    st.plotly_chart(graficos.fig_segmentos(dff), width="stretch", config={"displayModeBar": False})

st.caption("Protótipo do Hacka Business · dados sintéticos e recomendação simulada. Nada aqui representa clientes reais.")
