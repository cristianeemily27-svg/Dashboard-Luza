# Co-Piloto de Valor — interface principal do MVP

Interface em **Streamlit + Plotly** para a carteira de clientes de alto valor (Hacka Business · Desafio 3).
Roda inteira com **dados 100% sintéticos** e recomendação simulada por regras.

> Material confidencial do hackathon: mantenha o repositório privado.

## Como rodar

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Testes (opcional): `pytest`

## O que tem na tela

| Entrega | Onde está |
|---|---|
| Filtros por segmento, risco, prioridade, rota e nível | Barra lateral (vazio = todos) + busca por nome/código |
| Tabela de clientes e perfil detalhado | Centro/esquerda: tabela ordenada por valor em risco; clique numa linha para abrir o perfil à direita |
| Gráficos de score × risco, CLV e segmentos | Seção "Análises da carteira" (dispersão clicável, CLV por nível, valor em risco por segmento) |
| Evidências e explicação do score | Abas **Evidências** e **Score explicado** do perfil |
| Botão e estados de carregamento da recomendação | Aba **Recomendação**: botão, progresso por etapas, resultado, estado de erro e "gerar novamente" |

## Critério "achar o caso corporativo em risco em poucos passos"

1. **Zero cliques:** o app abre com um alerta "Contas corporativas em risco alto" no topo e o perfil do maior valor em risco já aberto (o caso plantado, *Meridian Logística S.A.*, CLI-0001).
2. **Um clique:** o botão "Corporativos em risco alto" na barra lateral aplica os dois filtros.
3. **Um clique no alerta:** "Abrir perfil" em qualquer conta da lista.

## Estrutura

```
app.py            interface (layout, filtros, tabela, perfil, abas, gráficos)
dados.py          gerador de dados sintéticos, score, risco, evidências
graficos.py       figuras Plotly
recomendacao.py   motor de recomendação SIMULADO (ponto de troca para IA real)
selecao.py        extrai o cliente selecionado da tabela/gráfico
formatos.py       formatação em pt-BR (R$, milhar)
tests/            testes de dados, seleção e fluxos da interface (AppTest)
```

## Como o score e o risco funcionam (sintético)

- **Score de valor (0–100):** soma ponderada de recência (20), frequência (20), valor gasto (30), influência (15) e engajamento (15). O gráfico "Score explicado" mostra os pontos de cada fator.
- **Risco (%):** função de queda de interações, dias sem voar, reclamações, nota de satisfação e vencimento de contrato. Alto ≥ 70, médio 40–69, baixo < 40.
- **CLV:** gasto direto projetado + valor de influência. **Valor em risco** = CLV × risco.

## Para plugar IA de verdade

Troque o corpo de `_regras` em `recomendacao.py` (por exemplo, chamando Azure OpenAI/GraphRAG) mantendo as chaves do dicionário de retorno: `acao, canal, prazo, custo_estimado, ganho_incremental, roi, confianca, justificativa`. A interface já trata espera, progresso e erro (`RecomendacaoErro`).
Para dados reais, substitua `dados.gerar_dados()` por um leitor que devolva as mesmas colunas.

## Modo demonstração

Na barra lateral, "Modo demonstração" permite simular falha da recomendação e mudar a latência, útil para mostrar os estados de carregamento e erro no pitch. A variável `COPILOTO_LATENCIA` define a latência inicial.
