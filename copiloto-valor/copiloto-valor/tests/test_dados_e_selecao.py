import pandas as pd

import dados
import recomendacao
import selecao
from formatos import brl


def test_dados_sao_deterministicos_e_completos():
    a, b = dados.gerar_dados(), dados.gerar_dados()
    pd.testing.assert_frame_equal(a, b)
    assert len(a) == dados.N_CLIENTES
    assert a["cliente_id"].is_unique
    assert not a[["score", "risco", "clv", "nivel", "prioridade", "segmento"]].isna().any().any()
    assert a["risco"].between(1, 99).all() and a["score"].between(0, 100).all()


def test_caso_corporativo_critico_e_o_primeiro_em_valor_em_risco():
    df = dados.gerar_dados()
    topo = df.sort_values("valor_em_risco", ascending=False).iloc[0]
    assert topo["cliente_id"] == dados.CLIENTE_CRITICO
    assert topo["segmento"] == "Corporativo"
    assert topo["nivel"] == "Diamante" and topo["prioridade"] == "Alta"
    assert topo["risco"] >= 70


def test_score_e_soma_dos_fatores():
    df = dados.gerar_dados()
    soma = sum(df[f"f_{k}"] for k in dados.PESOS)
    assert (soma - df["score"]).abs().max() < 0.5  # só arredondamento


def test_evidencias_do_caso_critico_explicam_o_risco():
    df = dados.gerar_dados()
    ev = dados.evidencias(df.iloc[0], df)
    tipos = {e["tipo"] for e in ev}
    assert {"risco", "valor"} <= tipos
    assert any("Contrato" in e["texto"] for e in ev)


def test_selecao_pela_tabela_e_pelo_grafico():
    ids = ["A", "B", "C"]
    assert selecao.id_da_tabela({"selection": {"rows": [2]}}, ids) == "C"
    assert selecao.id_da_tabela({"selection": {"rows": []}}, ids) is None
    assert selecao.id_da_tabela(None, ids) is None
    assert selecao.id_do_grafico({"selection": {"points": [{"customdata": ["CLI-0007", "x"]}]}}) == "CLI-0007"
    assert selecao.id_do_grafico({"selection": {"points": []}}) is None


def test_recomendacao_normal_e_falha():
    df = dados.gerar_dados()
    cliente = df.iloc[0].to_dict()
    etapas = []
    rec = recomendacao.gerar_recomendacao(cliente, latencia=0, ao_avancar=lambda i, t: etapas.append(i))
    assert etapas == list(range(len(recomendacao.ETAPAS)))
    assert rec["ganho_incremental"] > rec["custo_estimado"] > 0 and rec["simulado"]
    try:
        recomendacao.gerar_recomendacao(cliente, latencia=0, falhar=True)
    except recomendacao.RecomendacaoErro:
        pass
    else:
        raise AssertionError("era esperado RecomendacaoErro")


def test_formato_brl():
    assert brl(1234567) == "R$ 1.234.567"
    assert brl(1234567, compacto=True) == "R$ 1,2 mi"
    assert brl(48500, compacto=True) == "R$ 49 mil"
