"""Gerador de dados 100% sintéticos para o protótipo do Co-Piloto de Valor.

Nada aqui vem de dados reais. A semente é fixa, então a carteira é sempre a
mesma. Um caso corporativo em risco (CLI-0001) é plantado de propósito para
que o critério de aceite "achar o caso em poucos passos" seja testável.
"""
from __future__ import annotations

import unicodedata

import numpy as np
import pandas as pd

SEMENTE = 42
N_CLIENTES = 400

SEGMENTOS = ["Corporativo", "Executivo", "Influenciador", "Lazer frequente", "Lazer ocasional"]
NIVEIS = ["Diamante", "Ouro", "Prata", "Bronze"]
PRIORIDADES = ["Alta", "Média", "Baixa"]
FAIXAS_RISCO = ["Alto", "Médio", "Baixo"]
ROTAS = [
    "REC–VCP", "REC–GRU", "REC–CNF", "REC–BSB", "REC–FOR",
    "SSA–VCP", "FOR–VCP", "POA–VCP", "CNF–VCP", "BSB–VCP",
]

CLIENTE_CRITICO = "CLI-0001"

# Pesos do score de valor (somam 1.0). Cada fator contribui com peso*100 pontos no máximo.
PESOS = {
    "recencia": 0.20,
    "frequencia": 0.20,
    "valor": 0.30,
    "influencia": 0.15,
    "engajamento": 0.15,
}
ROTULOS_FATORES = {
    "recencia": "Recência de voo",
    "frequencia": "Frequência de voos",
    "valor": "Valor gasto (12 meses)",
    "influencia": "Influência / rede",
    "engajamento": "Engajamento recente",
}

# Parâmetros por segmento: probabilidade, média de voos/ano, ticket médio,
# escala (dias) desde o último voo, índice de influência (média, desvio),
# mediana do alcance da rede e valor-base de influência (R$).
PERFIS = {
    "Corporativo":     dict(p=0.10, voos=70, ticket=1050, dias=25,  infl=(55, 15), alcance=35,     base_infl=60_000),
    "Executivo":       dict(p=0.10, voos=24, ticket=1250, dias=30,  infl=(60, 15), alcance=12,     base_infl=45_000),
    "Influenciador":   dict(p=0.06, voos=9,  ticket=700,  dias=45,  infl=(75, 15), alcance=180_000, base_infl=60_000),
    "Lazer frequente": dict(p=0.30, voos=8,  ticket=520,  dias=50,  infl=(15, 8),  alcance=5,      base_infl=3_000),
    "Lazer ocasional": dict(p=0.44, voos=2,  ticket=430,  dias=120, infl=(6, 4),   alcance=2,      base_infl=500),
}

# Casos plantados (índice -> campos). O primeiro é o caso corporativo crítico.
CASOS_PLANTADOS = {
    0: dict(nome="Meridian Logística S.A.", segmento="Corporativo", rota="REC–GRU", voos=240,
            ticket=1420.0, dias=41, queda=0.46, reclam=4, nps=3, contrato=38, indice=72, alcance=420),
    1: dict(nome="Aurora Têxtil Ltda", segmento="Corporativo", rota="REC–VCP", voos=95,
            ticket=1180.0, dias=52, queda=0.38, reclam=3, nps=5, contrato=61, indice=55, alcance=60),
    2: dict(nome="Vale Verde Agropecuária S.A.", segmento="Corporativo", rota="BSB–VCP", voos=48,
            ticket=980.0, dias=47, queda=0.31, reclam=2, nps=5, contrato=85, indice=45, alcance=28),
    3: dict(nome="@luh.viaja", segmento="Influenciador", rota="SSA–VCP", voos=14,
            ticket=760.0, dias=88, queda=0.35, reclam=1, nps=5, contrato=None, indice=85, alcance=310_000),
}
RISCO_FIXO = {0: 87.0, 1: 78.0, 2: 71.0, 3: 74.0}

_PRIMEIROS = ["Ana", "Bruno", "Carla", "Diego", "Elisa", "Felipe", "Gabriela", "Heitor", "Isabela",
              "João", "Karen", "Lucas", "Mariana", "Nathália", "Otávio", "Paula", "Rafael", "Sofia",
              "Thiago", "Vitória", "André", "Beatriz", "Caio", "Daniela", "Eduardo", "Fernanda",
              "Gustavo", "Helena", "Igor", "Juliana"]
_SOBRENOMES = ["Albuquerque", "Barbosa", "Cavalcanti", "Dantas", "Estevão", "Ferreira", "Gomes",
               "Holanda", "Lacerda", "Macedo", "Nogueira", "Oliveira", "Pereira", "Queiroz",
               "Ribeiro", "Santos", "Teixeira", "Uchoa", "Vasconcelos", "Xavier"]
_EMPRESA_NOME = ["Atlântica", "Nordeste", "Horizonte", "Capibaribe", "Paulista", "Litoral", "Planalto",
                 "Sertão Forte", "Boa Vista", "Solaris", "Vertice", "Norte Sul"]
_EMPRESA_SETOR = ["Engenharia", "Consultoria", "Tecnologia", "Construções", "Saúde", "Comércio",
                  "Energia", "Serviços"]
_EMPRESA_TIPO = ["Ltda", "S.A.", "Ltda", "EIRELI"]
_HANDLE = ["viaja", "trip", "mundo", "rota", "destinos", "nuvens"]


def _ascii(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()


def _nome(rng: np.random.Generator, segmento: str) -> str:
    if segmento == "Corporativo":
        return f"{rng.choice(_EMPRESA_NOME)} {rng.choice(_EMPRESA_SETOR)} {rng.choice(_EMPRESA_TIPO)}"
    primeiro = str(rng.choice(_PRIMEIROS))
    if segmento == "Influenciador":
        return f"@{_ascii(primeiro)}.{rng.choice(_HANDLE)}"
    return f"{primeiro} {rng.choice(_SOBRENOMES)}"


def faixa_risco(risco: float) -> str:
    if risco >= 70:
        return "Alto"
    if risco >= 40:
        return "Médio"
    return "Baixo"


def gerar_dados(n: int = N_CLIENTES, semente: int = SEMENTE) -> pd.DataFrame:
    rng = np.random.default_rng(semente)

    seg = rng.choice(SEGMENTOS, size=n, p=[PERFIS[s]["p"] for s in SEGMENTOS]).astype(object)
    for i, caso in CASOS_PLANTADOS.items():
        seg[i] = caso["segmento"]

    def por_seg(chave, sub=None):
        return np.array([PERFIS[s][chave] if sub is None else PERFIS[s][chave][sub] for s in seg], dtype=float)

    voos = np.maximum(rng.poisson(por_seg("voos") * rng.lognormal(0, 0.45, n)), 1).astype(float)
    ticket = por_seg("ticket") * rng.lognormal(0, 0.25, n)
    dias = np.clip(rng.exponential(por_seg("dias")), 1, 365).round()
    queda = np.clip(rng.normal(0.03, 0.18, n), -0.4, 0.8)
    reclam = rng.poisson(0.4, n).astype(float)
    nps = np.clip(np.round(rng.normal(8, 1.6, n) - reclam * 1.2), 0, 10)
    indice = np.clip(rng.normal(por_seg("infl", 0), por_seg("infl", 1)), 0, 100)
    alcance = np.maximum(
        1, np.round(por_seg("alcance") * rng.lognormal(0, 1.0 if "Influenciador" in seg else 0.7, n))
    )
    contrato = np.where(seg == "Corporativo", rng.integers(20, 540, n), np.nan).astype(float)
    rota = rng.choice(ROTAS, size=n).astype(object)
    nome = np.array([_nome(rng, s) for s in seg], dtype=object)
    base_infl = por_seg("base_infl") * rng.lognormal(0, 0.5, n)
    mult_clv = rng.uniform(2.0, 3.5, n)

    for i, c in CASOS_PLANTADOS.items():
        nome[i], rota[i], voos[i], ticket[i], dias[i] = c["nome"], c["rota"], c["voos"], c["ticket"], c["dias"]
        queda[i], reclam[i], nps[i], indice[i], alcance[i] = c["queda"], c["reclam"], c["nps"], c["indice"], c["alcance"]
        contrato[i] = np.nan if c["contrato"] is None else c["contrato"]
        base_infl[i] = PERFIS[c["segmento"]]["base_infl"]
        mult_clv[i] = 3.0

    gasto = voos * ticket
    clv_direto = gasto * mult_clv
    valor_influencia = indice / 100 * base_infl
    clv = clv_direto + valor_influencia

    # Risco: sinais de queda de engajamento, inatividade, reclamações, satisfação e contrato.
    z = (
        -2.2
        + 0.012 * dias
        + 3.0 * np.maximum(queda, 0)
        - 1.2 * np.minimum(queda, 0)
        + 0.30 * reclam
        + 0.25 * np.clip(7 - nps, 0, None)
        + np.where(contrato <= 60, 0.6, 0.0)
        + rng.normal(0, 0.4, n)
    )
    risco = 100 / (1 + np.exp(-z))
    risco = np.clip(risco, 1, 99)
    for i, r in RISCO_FIXO.items():
        risco[i] = r

    # Score de valor: soma ponderada de cinco fatores, cada um normalizado em 0–1.
    componentes = {
        "recencia": 1 - np.clip(dias / 365, 0, 1),
        "frequencia": pd.Series(voos).rank(pct=True).to_numpy(),
        "valor": pd.Series(gasto).rank(pct=True).to_numpy(),
        "influencia": indice / 100,
        "engajamento": np.clip(1 - np.maximum(queda, 0) / 0.6, 0, 1),
    }
    contribuicoes = {k: PESOS[k] * 100 * componentes[k] for k in PESOS}
    score = sum(contribuicoes.values())

    df = pd.DataFrame({
        "cliente_id": [f"CLI-{i + 1:04d}" for i in range(n)],
        "nome": nome,
        "segmento": seg,
        "rota": rota,
        "score": score.round(1),
        "risco": risco.round(0),
        "clv": clv.round(0),
        "clv_direto": clv_direto.round(0),
        "valor_influencia": valor_influencia.round(0),
        "voos_12m": voos.astype(int),
        "ticket_medio": ticket.round(0),
        "gasto_12m": gasto.round(0),
        "dias_ultimo_voo": dias.astype(int),
        "queda_interacoes": queda.round(2),
        "reclamacoes_90d": reclam.astype(int),
        "nps_ultimo": nps.astype(int),
        "contrato_vence_dias": contrato,
        "indice_influencia": indice.round(0),
        "alcance_rede": alcance.astype(int),
    })
    for k, v in contribuicoes.items():
        df[f"f_{k}"] = v.round(1)

    df["faixa_risco"] = df["risco"].map(faixa_risco)
    df["valor_em_risco"] = (df["clv"] * df["risco"] / 100).round(0)

    pct_clv = df["clv"].rank(pct=True)
    df["nivel"] = np.select([pct_clv >= 0.92, pct_clv >= 0.75, pct_clv >= 0.45], NIVEIS[:3], NIVEIS[3])
    pct_risco = df["valor_em_risco"].rank(pct=True)
    df["prioridade"] = np.select([pct_risco >= 0.85, pct_risco >= 0.50], PRIORIDADES[:2], PRIORIDADES[2])
    df["rank_clv_segmento"] = df.groupby("segmento")["clv"].rank(pct=True)

    for coluna, ordem in [("segmento", SEGMENTOS), ("nivel", NIVEIS), ("prioridade", PRIORIDADES),
                          ("faixa_risco", FAIXAS_RISCO)]:
        df[coluna] = pd.Categorical(df[coluna], categories=ordem, ordered=True)
    return df


def evidencias(cliente: pd.Series, df: pd.DataFrame) -> list[dict]:
    """Evidências em linguagem de negócio que sustentam score e risco do cliente."""
    from formatos import brl, inteiro

    c = cliente
    itens: list[dict] = []
    mediana = float(df.loc[df["segmento"] == c["segmento"], "dias_ultimo_voo"].median())

    if c["queda_interacoes"] >= 0.15:
        itens.append(dict(tipo="risco", fonte="CRM · e-mails, ligações e reuniões",
                          texto=f"Interações caíram {c['queda_interacoes'] * 100:.0f}% nos últimos 90 dias em relação aos 90 anteriores."))
    if c["dias_ultimo_voo"] > 45 and c["dias_ultimo_voo"] > 1.5 * mediana:
        itens.append(dict(tipo="risco", fonte="Reservas",
                          texto=f"Sem voar há {c['dias_ultimo_voo']} dias (mediana do segmento: {mediana:.0f})."))
    if c["reclamacoes_90d"] >= 2:
        itens.append(dict(tipo="risco", fonte="SAC",
                          texto=f"{c['reclamacoes_90d']} reclamações registradas nos últimos 90 dias."))
    if c["nps_ultimo"] <= 6:
        itens.append(dict(tipo="risco", fonte="Pesquisa pós-voo",
                          texto=f"Última nota de satisfação: {c['nps_ultimo']}/10."))
    if pd.notna(c["contrato_vence_dias"]) and c["contrato_vence_dias"] <= 90:
        itens.append(dict(tipo="risco", fonte="Contratos",
                          texto=f"Contrato corporativo vence em {c['contrato_vence_dias']:.0f} dias."))
    if not itens:
        itens.append(dict(tipo="contexto", fonte="CRM",
                          texto="Sem sinais relevantes de queda de engajamento nos últimos 90 dias."))

    topo = max(1, round((1 - c["rank_clv_segmento"]) * 100))
    itens.append(dict(tipo="valor", fonte="Reservas e faturamento",
                      texto=f"{c['voos_12m']} voos e {brl(c['gasto_12m'])} gastos em 12 meses; CLV de {brl(c['clv'])}, "
                            f"entre os {topo}% maiores do segmento."))

    if c["indice_influencia"] >= 50:
        if c["segmento"] == "Influenciador":
            texto = f"Alcance estimado de {inteiro(c['alcance_rede'])} seguidores em canais de viagem."
        elif c["segmento"] == "Corporativo":
            texto = f"Decide as viagens de cerca de {inteiro(c['alcance_rede'])} colaboradores."
        else:
            texto = f"Lidera uma rede de cerca de {inteiro(c['alcance_rede'])} pessoas com viagens a negócios."
        itens.append(dict(tipo="influencia", fonte="Rede e organograma",
                          texto=texto + f" Valor de influência estimado em {brl(c['valor_influencia'])}."))
    return itens


if __name__ == "__main__":
    import pathlib

    destino = pathlib.Path(__file__).parent / "data" / "clientes_sinteticos.csv"
    destino.parent.mkdir(exist_ok=True)
    gerar_dados().to_csv(destino, index=False)
    print(f"Gerado: {destino}")
