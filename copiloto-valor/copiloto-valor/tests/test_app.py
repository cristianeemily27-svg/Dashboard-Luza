"""Testes de interface com o AppTest do Streamlit (sem navegador)."""
import pathlib

import pytest
from streamlit.testing.v1 import AppTest

import dados

APP = str(pathlib.Path(__file__).resolve().parents[1] / "app.py")


@pytest.fixture
def app():
    at = AppTest.from_file(APP, default_timeout=60)
    at.session_state["latencia"] = 0.0
    at.run()
    assert not at.exception
    return at


def metrica(at, rotulo):
    return next(m.value for m in at.metric if m.label == rotulo)


def test_abre_sem_erro_e_ja_mostra_o_caso_critico_no_perfil(app):
    assert metrica(app, "Clientes na seleção") == str(dados.N_CLIENTES)
    assert app.session_state["cliente_sel"] == dados.CLIENTE_CRITICO
    assert "Meridian Logística S.A." in [s.value for s in app.subheader]


def test_um_clique_no_atalho_filtra_corporativos_em_risco(app):
    atalho = next(b for b in app.button if b.label.startswith("🔎"))
    atalho.click().run()
    assert not app.exception
    assert app.multiselect(key="f_segmento").value == ["Corporativo"]
    assert app.multiselect(key="f_risco").value == ["Alto"]
    assert int(metrica(app, "Clientes na seleção")) < 15
    assert app.session_state["cliente_sel"] == dados.CLIENTE_CRITICO


def test_busca_por_nome_encontra_o_caso(app):
    app.text_input(key="f_busca").set_value("meridian").run()
    assert metrica(app, "Clientes na seleção") == "1"
    assert app.session_state["cliente_sel"] == dados.CLIENTE_CRITICO


def test_filtros_combinados_reduzem_a_lista(app):
    app.multiselect(key="f_nivel").set_value(["Diamante"]).run()
    app.multiselect(key="f_prioridade").set_value(["Alta"]).run()
    assert not app.exception
    assert 0 < int(metrica(app, "Clientes na seleção")) < dados.N_CLIENTES


def test_filtro_sem_resultado_mostra_aviso(app):
    app.text_input(key="f_busca").set_value("zzzz-nao-existe").run()
    assert not app.exception
    assert any("Nenhum cliente" in w.value for w in app.warning)


def test_abrir_perfil_pelo_alerta_troca_o_cliente(app):
    app.button(key="abrir_CLI-0002").click().run()
    assert app.session_state["cliente_sel"] == "CLI-0002"
    assert any("Aurora" in s.value for s in app.subheader)


def test_botao_gera_recomendacao(app):
    assert any("Ainda não há recomendação" in i.value for i in app.info)
    app.button(key="btn_gerar").click().run()
    assert not app.exception
    rec = app.session_state["recs"][dados.CLIENTE_CRITICO]
    assert "erro" not in rec and rec["acao"]
    assert app.button(key="btn_gerar").label == "Gerar novamente"


def test_estado_de_erro_da_recomendacao_e_recuperavel(app):
    app.toggle(key="simular_falha").set_value(True).run()
    app.button(key="btn_gerar").click().run()
    assert "erro" in app.session_state["recs"][dados.CLIENTE_CRITICO]
    assert any("Não foi possível" in e.value for e in app.error)
    app.toggle(key="simular_falha").set_value(False).run()
    app.button(key="btn_gerar").click().run()
    assert "erro" not in app.session_state["recs"][dados.CLIENTE_CRITICO]
    assert not app.error


def test_limpar_filtros_restaura_a_carteira(app):
    app.text_input(key="f_busca").set_value("meridian").run()
    next(b for b in app.button if b.label == "Limpar filtros").click().run()
    assert metrica(app, "Clientes na seleção") == str(dados.N_CLIENTES)
