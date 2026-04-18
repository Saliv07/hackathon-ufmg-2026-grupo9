# Habeas Código

**Hackathon UFMG 2026 · Enter AI Challenge · Grupo 9**
17 e 18 de Abril de 2026


---
## Link para slides

https://www.figma.com/deck/I0CU9AD9X3Hk718NOIOCzv

---
## Demo em vídeo

Veja a aplicação funcionando: **https://youtu.be/Isxih7zVurc**

---

## O problema

O Banco UFMG recebe cerca de **5 mil processos por mês** em que o autor alega não reconhecer a contratação de um empréstimo consignado. Para cada caso, o banco precisa decidir entre **defender-se no judiciário** ou **propor um acordo**. Hoje, apenas 0,47% dos 60 mil casos históricos terminaram em acordo — e o banco desembolsou R$ 192,98 milhões em condenações.

## A solução

**Habeas Código** é uma aplicação Python única que integra três frentes na mesma porta:

- **Política de acordos** — uma engine híbrida em `src/policy/` que combina regras determinísticas auditáveis com um modelo XGBoost (AUC 0,91). Regras cobrem os casos claros (0-1 ou 3 subsídios críticos presentes, UF de alto risco, dossiê não conforme); o modelo decide apenas na zona cinzenta (2 subsídios críticos). O valor do acordo parte de 30% do valor da causa, calibrado com 280 acordos históricos, com ajustes de ±3pp por perfil probatório e ±2pp por UF.
- **Plataforma do advogado** — Flask (backend) + React com Vite (frontend). O advogado acessa os autos e subsídios de cada caso, recebe a recomendação da política com justificativa gerada por agente OpenAI (GPT-4o + Whisper para áudio + Vision para imagens) e registra a decisão.
- **Monitoramento** — dashboards em Plotly Dash montados como sub-app do mesmo Flask. Respondem os requisitos 4 (aderência) e 5 (efetividade) do enunciado, com 20 métricas catalogadas (A01-A20 e E02-E11), análise de sensibilidade da economia à taxa de aceitação e alertas operacionais sobre advogados e escritórios com aderência crítica.

Sobre os 60 mil casos históricos, a simulação da política estima **R$ 64 milhões de economia anual** (redução de 33% no gasto contencioso).

---

## Como executar

Tudo roda em **um único processo Python** na porta **5000** (ou na próxima livre se a 5000 estiver ocupada — comum em macOS, onde o AirPlay Receiver reserva essa porta).

### Pré-requisitos

- **Python 3.10+** — [download](https://www.python.org/downloads/)
- **Node.js 20.19+** ou **22.12+** — [download](https://nodejs.org/) (necessário para buildar o frontend)
- Arquivo `.env` na raiz com `OPENAI_API_KEY=sk-...`

### Um comando

```bash
python run.py
```

O script cuida de todo o bootstrap:

1. Verifica versões de Python e Node
2. Cria `backend/venv` e instala dependências Python
3. Roda `npm install` e `npm run build` no frontend
4. Gera os artefatos do monitoramento (parquets) se faltarem
5. Detecta uma porta livre automaticamente
6. Sobe Flask + Dash em foreground

Acesse `http://localhost:5000/` (ou a porta indicada no console). Ctrl+C encerra tudo.

### Rotas expostas

```
/                        frontend React (plataforma do advogado)
/api/*                   endpoints Flask (cases, stats, analyze, uploads)
/monitoramento/          dashboard Dash (aderência + efetividade)
```

### Artefatos pesados do modelo (opcional, melhora o monitoramento)

Os `.pkl` do XGBoost (~20 MB) são ignorados pelo git. Para baixar:

```bash
git checkout origin/master -- artefatos/
```

Sem isso o monitoramento usa uma política de fallback.

### Forçar uma porta específica

```bash
PORT=8000 python run.py
```

---

## Estrutura do repositório

```
src/policy/              engine Python da política (regras + XGBoost + pricing)
src/monitor/             frente de monitoramento
  ├─ load_data.py        xlsx → parquet
  ├─ baseline.py         números de referência dos 60k
  ├─ gerar_sintetico.py  dataset enriquecido (advogados, escritórios, datas)
  ├─ politica_xgboost.py roda o modelo e gera politica_output.csv
  ├─ metrics_adherence   A01–A20 (seguimento, override, rankings)
  ├─ metrics_effective   E02–E11 (economia, sensibilidade, redistribuição)
  ├─ counterfactual.py   motor contrafactual
  └─ dash_app.py         app Dash (Aderência + Efetividade)
backend/                 API Flask + integração OpenAI + montagem do Dash
frontend/                React + Vite (Login, Dashboard macro, Workspace, Monitoramento)
artefatos/               modelo XGBoost treinado + metadados
tests/                   suíte pytest da frente de monitoramento (65 testes)
docs/                    política escrita, slide deck, decisões técnicas
run.py                   orquestrador único (venv, build, porta, servidor)
```

---

## Stack

**Backend** · Python 3.10+ · Flask 3 · Dash 4 · Plotly · flask-caching · pandas · pyarrow · XGBoost · OpenAI SDK

**Frontend** · React 19 · Vite · lucide-react

**Dados** · 60 mil casos reais da base da Enter · 50 advogados e 10 escritórios sintéticos (seed=42) · modelo XGBoost treinado com 9 features (AUC 0,91)

---

## Testes

```bash
./backend/venv/bin/pytest tests/ -q
```

65 testes cobrindo smoke, propriedades e unitários sobre load_data, baseline, métricas de aderência, métricas de efetividade e contrafactual. Executam em ~2 segundos.

---

## Documentação adicional

- `docs/politica_acordo.md` — política v2.1 completa (regras, matriz de decisão, pricing)
- `docs/DECISOES.md` — log vivo de decisões técnicas e 14 assunções (H1-H14) do monitoramento
- `SETUP.md` — guia detalhado de setup e troubleshooting

---

## Requisitos do enunciado atendidos

| # | Requisito | Onde |
|---|-----------|------|
| 1 | Regra de decisão (acordo ou defesa) | `src/policy/engine.py` |
| 2 | Sugestão de valor para o acordo | `src/policy/pricing.py` |
| 3 | Acesso à recomendação pelo advogado | Plataforma React + backend Flask |
| 4 | Monitoramento de aderência | Dashboard Dash · aba Aderência · métricas A01-A20 |
| 5 | Monitoramento de efetividade | Dashboard Dash · aba Efetividade · métricas E02-E11 |
