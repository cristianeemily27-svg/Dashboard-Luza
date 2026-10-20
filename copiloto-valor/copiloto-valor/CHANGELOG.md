# Changelog

## 2026-10-16 — v0.1 (interface principal do MVP)

### Feito
- Dados sintéticos determinísticos (400 clientes, 5 segmentos, 4 níveis, 10 rotas) com caso corporativo crítico plantado (CLI-0001) e três casos de apoio.
- Filtros: segmento, faixa de risco, prioridade, rota, nível, busca por nome/código, atalho "Corporativos em risco alto" e limpar filtros.
- Métricas de topo (clientes, CLV total, valor em risco, risco alto) e alerta de contas corporativas em risco com "Abrir perfil".
- Tabela ordenada por valor em risco com seleção de linha; perfil com badges, métricas e detalhes.
- Abas do perfil: Evidências (com fonte), Score explicado (pontos por fator) e Recomendação.
- Gráficos: score × risco (clicável, com quadrante "proteger primeiro"), CLV por nível e valor em risco por segmento.
- Recomendação simulada com botão, progresso por etapas, resultado, estado de erro, tentar de novo e modo demonstração.
- 16 testes automatizados (dados, seleção, fluxos da interface) passando; servidor sobe e responde.

### Falta
- Revisar a interface em um navegador real (os testes cobrem comportamento, não aparência): ajustar larguras, cores e densidade da tabela.
- Plugar o motor real de recomendação (IA/GraphRAG) e a restrição de orçamento de retenção na recomendação.
- Trocar os dados sintéticos pelo formato real do desafio, se a organização liberar um esquema.
- Cobrir influência por rede/papel estratégico com sinais mais ricos (hoje é um índice sintético).
- Gravar o vídeo de pitch (até 5 min) e fechar o repositório privado para a entrega de 26/10.
