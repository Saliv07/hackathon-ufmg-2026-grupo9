# Log de Decisões — Frente de Monitoramento

**Projeto:** Hackathon UFMG 2026 / Enter — Política de Acordos Banco UFMG
**Escopo:** Requisitos 4 (Aderência) e 5 (Efetividade)
**Responsável:** Arthur Vilas
**Branch:** `vilas`

---

## Como usar este documento

Este é um log **vivo** — toda decisão não-trivial, assunção numérica, limitação conhecida ou ponto de integração com outra frente é registrado aqui com data e racional. Serve três propósitos:

1. **Memória de trabalho** — recuperar por que uma escolha foi feita dias depois.
2. **Transparência para a banca** — qualquer número que aparece no dashboard tem rastreabilidade até uma entrada aqui.
3. **Handoff** — se outra pessoa pegar a frente, consegue se situar lendo só este arquivo + o guia.

**Formato de entrada:**
```
### [YYYY-MM-DD HH:MM] Título curto da decisão
**Contexto:** o que motivou a decisão
**Decisão:** o que foi escolhido
**Alternativas consideradas:** o que foi descartado e por quê
**Impacto:** o que muda no sistema por causa dessa decisão
**Revisitar se:** condição que forçaria reavaliação
```

Entradas mais recentes no topo.

---

## Assunções centrais do modelo

Estas são as premissas que sustentam todas as métricas. Se alguma cai, o número associado no dashboard perde validade.

| # | Assunção | Valor padrão | Fonte / justificativa | Onde impacta |
|---|---|---:|---|---|
| H1 | Probabilidade de o autor aceitar o acordo recomendado pela política | **0.40** | Calibração da equipe do modelo (17/04 ~18h40); parametrizável via slider no dashboard | `counterfactual.py` — métrica E02 (Economia Total) |
| H2 | Valor de acordo recomendado (mock, até XGBoost chegar) | **30% do valor da causa** | Calibração da equipe; fonte única em `gerar_sintetico.ACORDO_PCT_CAUSA` | `gerar_sintetico.py` + `counterfactual.py` (importa dela) — será sobrescrito no Passo 9 |
| H3 | Ação recomendada (mock) | `acordo` se subs_total ≤ 3, senão `defesa` | Derivada do insight do baseline (crítico ≤ 3 subsídios) | `gerar_sintetico.py` — será sobrescrito no Passo 9 |
| H4 | Quando política recomenda defesa, o custo esperado é o custo real observado | — | Política não altera o resultado de uma defesa, só seleciona quais casos defender | `counterfactual.py` — função `custo_caso_sob_politica` |
| H5 | 50 advogados, 10 escritórios, 5 advogados/escritório | — | Escala plausível para ~60k casos/ano | `gerar_sintetico.py` |
| H6 | Aderência dos escritórios segue 3 clusters: ótimos (~93%), medianos (~80%), problemáticos (~62%) | — | Modelagem realista para gerar variação visível nos dashboards | `gerar_sintetico.py` |
| H7 | Advogados desviam mais em casos de Alto valor (−8pp na aderência esperada) | −0.08 | Viés humano plausível: medo de errar em caso caro | `gerar_sintetico.py` |
| H8 | Seed de aleatoriedade | 42 | Reprodutibilidade total | todos os geradores sintéticos |
| H9 | Faixas de ratio proposto/causa para resultado da negociação | `<0.25 → [0.35, 0.35, 0.30]`; `0.25-0.40 → [0.65, 0.25, 0.10]`; `>0.40 → [0.80, 0.15, 0.05]` (aceito/contraproposta/rejeitado) | Heurística do guia — ratio maior = autor aceita mais | `gerar_sintetico.py` |
| H10 | Clamp de `data_decisao` ao limite 2026-03-31 | truncado no limite | Evita datas sintéticas no futuro | `gerar_sintetico.py` |
| H11 | Quando política recomenda acordo e autor recusa, caso mantém `resultado_micro` observado | — | Alternativa (assumir condenação integral) superestima viés a favor da política | `counterfactual.py` (métrica E05) |
| H12 | "Alta perda" para E07 (recall) = top decil de `valor_condenacao` | quantil 0.90 | Parametrizável; decil é convenção em risco de crédito | `metrics_effectiveness.py` |
| H13 | Série temporal de E09 distribui 60k casos uniformemente nos últimos 12 meses (quando `casos_60k` não tem `data_decisao`) | uniforme, seed 42 | Não existe data real nos 60k; uniforme é mais neutro que qualquer viés | `metrics_effectiveness.py` |
| H14 | Taxa de aceitação (E04): se `resultado_negociacao` ausente no df → retorna H1 com `fonte="assumida_H1"` | 0.70 | Rastreabilidade: dashboard sinaliza quando número é observado vs assumido | `metrics_effectiveness.py` |

---

## Pontos de integração externa (dependências de outras frentes)

| Frente | Entregável que esperamos | Formato | Prazo declarado | Fallback enquanto não chega |
|---|---|---|---|---|
| XGBoost / Label sintético (2 pessoas) | CSV de output da política: `numero_processo`, `acao_recomendada`, `valor_acordo_recomendado`, `score_confianca` | CSV em `data/politica_output.csv` | 17/04/2026 23h | Mock em `gerar_sintetico.py` (H2 + H3) |
| Plataforma do advogado (2 pessoas) | — (sem dependência) | — | — | — |

**Princípio:** a frente de monitoramento nunca bloqueia em dependência externa. Passo 9 do guia é isolado — trocar o mock pelo CSV real é operação de 1 merge.

---

## Log cronológico (mais recente primeiro)

### [2026-04-18 01:00] Migração Streamlit → Plotly Dash (processo único Flask)
**Contexto:** a arquitetura anterior tinha três processos (Flask :5000, Streamlit :8501, Caddy :8080 como gateway) unificados por um reverse proxy com binário `./bin/caddy`, `Caddyfile` e `dev.sh`. Isso exigia dois venvs distintos (backend/venv para Flask, venv raiz para Streamlit) e tornava o deploy frágil — o avaliador teria que baixar Caddy, orquestrar três processos, lidar com CORS entre portas. O iframe do Streamlit também sofria com redirecionamentos do `/monitoramento/` e não expunha filtros controláveis externamente.
**Decisão:** migrar o dashboard de monitoramento para Plotly Dash montado como sub-app dentro do Flask server existente (rota `/monitoramento/`). Um único `python backend/main.py` agora serve: `/` → React build, `/api/*` → endpoints Flask, `/monitoramento/` → Dash nativo. Toda a lógica pura em `src/monitor/*.py` (métricas A01-A20, E01-E20, contrafactual, baseline, gerador sintético, política XGBoost) permanece intacta.
**Arquivos criados:**
- `src/monitor/dash_app.py` (~870 linhas): factory `create_dash_app(flask_server)`, tema dark replicado como CSS em `app.index_string`, dois `dcc.Tabs` (Aderência + Efetividade), todos os gráficos recriados com Plotly puro (mesma lógica do Streamlit original), `flask_caching.Cache` com `@memoize(timeout=600)` para os parquets. Filtros (UF, escritório, sub-assunto, período, prob_aceita) são lidos da URL query string (`parse_filtros_da_url`) — não há sidebar no Dash; o React controla os filtros via iframe src dinâmico.
- `backend/main.py`: import tardio de `create_dash_app` depois de todas as rotas `/api/*`; novo endpoint `/api/monitoring/filtros` devolve `{ufs, escritorios, escritorios_nomes, periodo}` lidos do `casos_enriquecidos.parquet`; catch-all final serve `frontend/dist/` (index.html para SPA).
- `frontend/src/components/MonitoramentoBanco.jsx`: reescrito com barra de controles React (tabs, chips UF, segmented sub-assunto, date range, multi-dropdown escritórios, slider prob_aceita só em Efetividade). A barra monta a query string e atualiza o `src` do iframe — o Dash re-renderiza via callback do `dcc.Location`. Botão "Recarregar" força remount via `key` incremental; "Abrir isolado" substitui o antigo "Abrir em nova aba" apontando para a URL com filtros aplicados.
- `frontend/src/components/MonitoramentoBanco.css`: tokens reutilizados do `index.css` (var(--bg-panel), var(--accent-color), etc); chips, segmented, dropdown multi, range slider.
**Arquivos removidos:** `Caddyfile`, `dev.sh`, `bin/caddy`, diretório `bin/` (vazio após remoção).
**Arquivos preservados como backup (fallback se algum bug na Dash aparecer na banca):** `src/monitor/dashboards/app.py` (Streamlit original), `src/monitor/dashboards/theme_banco_ufmg.py`, `src/monitor/dashboards/components.py`, `.streamlit/`. Podem ser deletados depois que a banca aprovar a migração.
**Decisões de design não óbvias:**
- Escolhido `dcc.Dropdown`/chips/segmented nativos (sem `dash-bootstrap-components`) — menos peso, controle total do CSS. dbc fica no `requirements.txt` apenas porque foi pedido no briefing, mas não é usado no layout principal.
- Filtros via URL em vez de `dcc.Store`: assim o React controla 100% da experiência (o usuário vê os chips do React, não um segundo conjunto de widgets dentro do iframe). O Dash só reage ao `dcc.Location.search`.
- Cache `SimpleCache` com timeout 600s: tempo suficiente para uma sessão de demo; não precisa de Redis.
- Slider prob_aceita tem callback dedicado (`allow_duplicate=True`) que recomputa apenas a aba Efetividade — a aba Aderência não depende de prob_aceita.
**Dependências adicionadas ao `backend/requirements.txt`:** `dash>=2.18`, `dash-bootstrap-components>=1.6`, `plotly>=5.18`, `pandas>=2.0`, `pyarrow>=14.0`, `numpy>=1.24`, `xgboost>=2.0`, `scikit-learn>=1.3`, `flask-caching>=2.1`. Removido `streamlit` do `requirements.txt` raiz (raiz agora só tem o que é necessário para rodar `python -m src.monitor.{load_data,baseline,gerar_sintetico,politica_xgboost}` standalone).
**Impacto nos testes:** zero. Os 65 testes em `tests/` cobrem lógica pura (métricas, contrafactual, baseline, load_data) — nenhum tocava Streamlit. Continuam verdes.
**Revisitar se:** (a) a Dash apresentar algum travamento em produção → reativar o Streamlit preservado; (b) os filtros de URL estourarem limite de caracteres (improvável com < 30 UFs e < 15 escritórios); (c) o Flask `debug=True` causar reload em loop pelo Dash hot-reload (se for o caso, desligar `debug` em produção).

### [2026-04-17 20:50] Integração com output real do XGBoost (H2 e H3 substituídos)
**Contexto:** a frente de modelagem versionou em `origin/master` os artefatos do modelo XGBoost treinado (`artefatos/modelo_xgboost.pkl`, AUC 0.91) e a política escrita em `docs/politica_acordo.md`. Nosso mock (`subs_total <= 3`, acordo fixo 30%) era placeholder até esses artefatos chegarem.
**Decisão:** criar `src/monitor/politica_xgboost.py` que carrega o modelo, aplica a matriz híbrida da política (decisão por regra + ML quando há 2 subsídios críticos) e gera `data/processed/politica_output.csv` no formato esperado pelo `get_df_com_politica()` do dashboard. O mock antigo continua existindo (backward compat para testes).
**Matriz aplicada (politica_acordo.md §3.3 + §4.2):**
- 0-1 subsídios críticos (Contrato/Extrato/Comprovante) → acordo, fator 33%
- 2 críticos → decisão do XGBoost (limiar 0.5), fator 30%
- 3 críticos → defesa, fator 27%
- UF alto risco (AM, AP) + ≤2 críticos → acordo (override), +2pp
- UF baixo risco (fora de {AM, AP, GO, RS, BA, RJ, ES, DF, AL, SP, PE}) → −2pp
**Resultado no dataset real:** 17.505 casos recomendados para acordo (29,18%), 42.495 para defesa (70,83%). Fator médio de acordo 31% (distribuição: 28/30/31/32/33/35). Score de confiança média: 0.91 para defesa, 0.72 para acordo.
**Artefatos baixados de origin/master:** `artefatos/` (modelo + metadados), `scripts/01_prepare_data.py`, `scripts/02_train_model.py`, `docs/politica_acordo.md`.
**.gitignore:** `artefatos/*.pkl`, `artefatos/X.pkl`, `artefatos/y.pkl`, `artefatos/dataset_completo.pkl` (pesados, devem ser baixados do origin/master sob demanda).
**Dependências:** adicionadas `xgboost>=2.0` e `scikit-learn>=1.3` ao `requirements.txt`.
**Impacto:** assunções H2 e H3 do mock ficam ativas como fallback quando o CSV não existe. Quando existe, o dashboard usa automaticamente a política real via `get_df_com_politica()`.
**Revisitar se:** a frente de modelagem re-treinar o modelo (qualquer mudança em `features.json` exige revisar `preparar_features`); ou se a política formal for alterada em `docs/politica_acordo.md`.

### [2026-04-17 20:30] Remoção da aba "Visão Geral" do dashboard de monitoramento
**Contexto:** a plataforma React (`frontend/src/components/Dashboard.jsx`) já entrega o papel de visão executiva macro com os números do baseline pré-política. Manter uma aba "Visão Geral" no Streamlit duplicava escopo e diluía o foco do dashboard de monitoramento, que existe para atender exclusivamente os requisitos 4 (Aderência) e 5 (Efetividade) do enunciado.
**Decisão:**
- `src/monitor/dashboards/app.py`: removida a aba "Visão Geral" inteira (manchete, KPIs, distribuição de resultado micro, completude × êxito, custo total, expander por UF/financeiro). Removida função `baseline_mtime_iso`. Radio de navegação passa a ter apenas `["Aderência", "Efetividade"]`, default = Aderência.
- Removidos da sidebar: o caption "Política de Acordos · Banco UFMG" e o caption de fontes ("Baseline: 60k reais · Enriquecido: sintético (H5) · Política: mock/CSV"). Removidos também os dois `st.info("Fonte da política: ...")` que ficavam no topo das abas — transparência segue documentada aqui no DECISOES.
- Navegação: `st.radio` nativo preservado, mas envolvido por `<div class="ufmg-nav-radio">` + CSS no tema que esconde os círculos e estiliza os labels como pills horizontais dentro de um container arredondado (abordagem A do briefing). Item selecionado usa accent laranja #FFAE35 + borda suave.
- Título "Monitoramento" renderizado como `<h1 class="ufmg-sidebar-title">` via `st.markdown`, com CSS forçando `white-space: nowrap`, font-size 19px e `text-overflow: ellipsis` — garante uma linha única sem quebrar.
- `baseline.json` continua sendo carregado: a função `metrics_effectiveness.redistribuicao_resultado_micro` depende dele para o gráfico "antes × depois" da aba Efetividade. Import `datetime` removido (ficou órfão).
**Alternativas consideradas:**
- `st.segmented_control` (opção B) — rejeitado: Streamlit 1.56 suporta, mas o CSS dos pills com radio + `label:has(input:checked)` oferece controle visual maior e casa melhor com as regras de tabs/expander já existentes no tema.
- Dois `st.button` lado a lado (opção C) — rejeitado: precisaria de `st.session_state` próprio para simular seleção persistente, adicionando complexidade desnecessária.
**Impacto:**
- `app.py`: 1361 → 1083 linhas (−278 linhas).
- Carga cognitiva da banca reduzida: uma só tela por frente (macro na plataforma React, micro = monitoramento aqui).
- Nenhum teste tocado: `metrics_adherence`, `metrics_effectiveness`, `counterfactual` e `baseline` continuam intactos. Os 65 testes devem passar sem alteração.
- Filtros globais (UF, escritório, sub-assunto, período) e slider `prob_aceita` preservados.
**Revisitar se:** a banca pedir de volta uma visão-síntese dentro do Streamlit, ou se a plataforma React for removida.

### [2026-04-17 20:10] Nomes próprios PT-BR para escritórios e advogados
**Contexto:** o gerador entregava apenas IDs opacos (ESC01, ADV001...) no dataset enriquecido. Para a demo, o dashboard precisa mostrar nomes reconhecíveis ao lado dos rankings — ID puro não comunica nada à banca.
**Decisão:** adicionar colunas de rotulagem sem alterar a estrutura:
- `escritorio_nome`, `cidade_sede` no catálogo de escritórios (ESCRITORIOS).
- `advogado_nome`, `numero_oab` em `gerar_advogados` (OAB/UF condizente com a região do escritório).
- `cidade_sede_escritorio` propagada para cada linha do dataset enriquecido via map por `escritorio_id`.
- Catálogos hardcoded: 15 nomes de escritórios (estilo médio/grande porte BR), ~60 primeiros nomes e 30 sobrenomes PT-BR, com diversidade de gênero e de região.
- `metrics_adherence.aderencia_por_advogado` e `aderencia_por_escritorio` passam a carregar os nomes no groupby quando as colunas existirem no df (preserva compatibilidade com `df_mini` dos testes, que não tem essas colunas).
**Backend/data.py:** inspecionado (`CASES`). Contém apenas nomes de autores (`plaintiff`: "Maria das Graças Silva Pereira", "José Raimundo Oliveira Costa") — são clientes, não advogados da plataforma. Nenhum nome foi importado para os 50 advogados. Catálogo fica só com a lista hardcoded. Cidades-sede usam a mesma granularidade do `profile.location` do backend ("São Luís - MA", "Manaus - AM") por consistência visual.
**Estrutura (H5, H6, H7, H8) intacta:**
- 10 escritórios com a mesma sequência de `aderencia_base` (3 clusters: ótimos 0.95/0.93/0.92, medianos 0.85/0.83/0.80/0.78, problemáticos 0.68/0.64/0.60).
- 50 advogados (5 por escritório, round-robin).
- Viés H7 (−8pp em faixa Alto) e seed=42 inalterados.
- Ordem das chamadas `rng.*` dentro de `build()` preserva reprodutibilidade das demais colunas (datas, recomendações, ações, razões, valores).
**API preservada:** `ESCRITORIOS`, `gerar_advogados`, `build`, `build_and_save` mantidos. Novas colunas são aditivas — nenhum teste existente (tests/test_adherence.py) valida ausência de `advogado_nome`/`escritorio_nome`.
**Revisitar se:** surgir necessidade de unicidade determinística (hoje o desempate usa sufixo romano em colisões raras) ou se o backend publicar uma lista real de advogados da plataforma — nesse caso usamos prefixo.

### [2026-04-17 19:15] Não replicar números exatos da equipe de modelagem
**Contexto:** equipe reporta R$ 30M de economia atual e R$ 50M no melhor caso (70% aceitação). Nosso contrafactual, com as mesmas premissas declaradas (mock `subs_total ≤ 3`, acordo 30%, aceitação 40%), calcula R$ 17,3M. Com aceitação 70% calcula R$ 30,2M — bate com "atual" mas não com "melhor caso".
**Decisão:** não tentar calibrar o contrafactual para bater número-por-número com o pitch da equipe. Nosso papel é diferente:
- Dashboard = **ferramenta analítica** (demo ao vivo, slider interativo, transparência metodológica)
- Cálculo da equipe = **número narrativo** do pitch
**Como justificar na demo:** "a estimativa de R$ 50M da equipe usa metodologia própria; o dashboard permite explorar cenários com o slider — cada premissa é rastreável no log de decisões". Transparência > coincidência numérica.
**Alternativas descartadas:**
- "Oracle" que recomenda acordo em todos procedência+parcial — rejeitado pelo usuário como conteúdo hipotético
- Card "teto teórico" no dashboard — rejeitado: ênfase em arquitetura robusta, não em análises extras
**Impacto:** libera tempo da Fase 2 para entregar as abas Aderência e Efetividade com rigor, não com recursos decorativos.
**Revisitar se:** a banca questionar diretamente "por que os números no dashboard são diferentes dos slides?" — resposta pronta: metodologias independentes, slider permite alinhar.

### [2026-04-17 19:00] H1 recalibrado: prob_aceita 0.70 → 0.40
**Contexto:** alinhamento com equipe do modelo. Calibração real da taxa de aceitação empírica nos testes deles: 40%, não 70% como o guia assumia originalmente.
**Decisão:**
- `counterfactual.py`: default de `prob_aceita` muda de 0.70 para 0.40
- `metrics_effectiveness.py`: default em 6 funções muda para 0.40
- `dashboards/app.py`: slider default 0.40, faixa ampliada para 0.10–0.95
- Teste `test_taxa_aceitacao_fallback_H1` atualizado para 0.40
**Impacto:** economia default apresentada no dashboard cai de R$ 30M para R$ 17M. Mais conservador, alinhado com empírico.

### [2026-04-17 18:35] Centralização da constante ACORDO_PCT_CAUSA
**Contexto:** originalmente o valor 30% aparecia hardcoded em 3 lugares (gerar_sintetico.py × 2, counterfactual.py × 1). Refatoração para fonte única.
**Decisão:** centralizar em `gerar_sintetico.ACORDO_PCT_CAUSA`. `counterfactual.py` importa. Com isso, mudanças futuras no percentual do acordo tocam apenas uma linha.
**Impacto:**
- Volume de economia esperado no contrafactual sobe (acordo fica mais caro, mas ainda é melhor que condenar)
- Re-geração obrigatória de `casos_enriquecidos.parquet` (que hard-codava 30%)
- Sanity check: se economia ficar negativa a prob_aceita=0.70, alguma coisa está errada no H4
**Revisitar se:** a equipe do modelo mudar o percentual após ajuste fino do XGBoost, ou se o CSV real chegar com valores divergentes.

### [2026-04-17 18:30] Item 1 — usar datas do `casos_enriquecidos` na série temporal de E09
**Contexto:** dataset real (`casos_60k`) não tem `data_decisao`. Agente B havia optado por distribuição uniforme própria; Agente A já gerou datas realistas (5.000 ± 180 casos/mês em 12 meses abr/2025–mar/2026, batendo com os 5k/mês do enunciado).
**Decisão:** métrica `economia_acumulada_temporal` deve priorizar as datas do `casos_enriquecidos.parquet` quando disponíveis.
**Alternativas consideradas:**
- Forçar exatos 5.000/mês — rejeitado: ruído natural (±3,6%) é mais realista e dá textura ao gráfico
- Manter distribuições separadas entre aderência e efetividade — rejeitado: banca pode estranhar incoerência
**Impacto:** dashboard de efetividade, na Fase 2, precisa usar `casos_enriquecidos` para a série temporal.

### [2026-04-17 18:20] Fase 1 concluída — 3 agentes paralelos
**Contexto:** após a Fase 0 (foundation com load_data + baseline + testes), lancei 3 agentes paralelos para os módulos principais.
**Decisão:** divisão por dataset — Agente A só escreve no Conjunto B, Agente B só lê Conjunto A, Agente C só lê `baseline.json`. Zero colisão de arquivos.
**Resultado:**
- Agente A (Aderência): `gerar_sintetico.py` vetorizado (~2s em 60k), `metrics_adherence.py` com A01-A20, 15 testes. Taxa de aderência geral 76,13%, spread escritórios 37,9pp.
- Agente B (Efetividade): `counterfactual.py` vetorizado (~1,5s), `metrics_effectiveness.py` com E01-E20, 22 testes. Economia a `prob_aceita=0.70`: R$ 30,2M (15,65%). Monotônico em prob_aceita (6,71% → 20,13% entre 0,3 e 0,9).
- Agente C (Dashboard): `app.py` com Visão Geral completa, abas Aderência/Efetividade com placeholders, paleta institucional fixa (#1F4E79, #4A90C2, #E8A33D, #C0392B), slider prob_aceita na sidebar da aba Efetividade.
- **Testes totais: 65 passam em 1,36s.**
**Assunções novas:** H9-H14 adicionadas à tabela acima. Todas documentadas com racional.
**Revisitar se:** APIs dos módulos forem revisadas durante a integração (Fase 2).

### [2026-04-17 17:40] Setup inicial da frente de monitoramento
**Contexto:** início da sessão de implementação dos requisitos 4 e 5. Guia pronto em `src/monitor/guia-implementacao-monitoramento.md`.
**Decisão:**
- Python 3.14.3 via venv em `venv/`
- Dependências: pandas 3.0, numpy 2.4, pyarrow 23, streamlit 1.56, plotly 6.7, openpyxl 3.1, pytest 9
- Estrutura: `src/monitor/` contém todos os scripts de monitoramento; dashboard em `src/monitor/dashboards/app.py`
- Data file via symlink em `data/raw/` (fonte real em `../../docs/Hackaton_Enter_Base_Candidatos.xlsx`)
**Alternativas consideradas:**
- Copiar xlsx fisicamente — rejeitado: duplica arquivo de 60k linhas e quebra se a fonte atualizar
- Python 3.12 — rejeitado: 3.14 é o stable atual no sistema e todas as deps têm wheels
**Impacto:** `data/raw/` é ignorado no git; só o symlink é versionável mas o alvo não. Developers de outra máquina precisam configurar o symlink manualmente (documentado no SETUP.md).
**Revisitar se:** alguma dep falhar wheel no 3.14.

### [2026-04-17 17:35] Vetorização de loops sobre 60k linhas
**Contexto:** revisão do guia apontou uso de `df.apply(axis=1)` em `counterfactual.py` e `df.iterrows()` em `gerar_sintetico.py`. Ambos custam ~60s em 60k linhas.
**Decisão:** reescrever com `np.where` / máscaras booleanas. Custo esperado: <1s.
**Alternativas consideradas:**
- Manter apply — rejeitado: em dashboard interativo, recalcular a cada mudança de slider fica inviável
- Numba / Cython — rejeitado: complexidade desnecessária para 60k linhas
**Impacto:** funções `custo_caso_sob_politica` e `simular_politica` precisam ser reescritas vetorialmente. Resultado do cálculo negociação (ratios) também vetoriza bem com `pd.cut`.
**Revisitar se:** precisarmos de lógica caso-a-caso que não vetoriza (ex.: dependência entre linhas).

### [2026-04-17 17:35] `prob_aceita` vira parâmetro de sensibilidade
**Contexto:** valor 0.70 era chute hardcoded em `counterfactual.py`. Em hackathon, a banca questiona números mágicos.
**Decisão:** expor como slider na sidebar do Streamlit (faixa 0.30–0.95, passo 0.05, default 0.70). O dashboard de efetividade recalcula o contrafactual a cada mudança.
**Alternativas consideradas:**
- Manter 0.70 fixo — rejeitado: esconde uma premissa frágil
- Rodar grid 0.30, 0.50, 0.70, 0.90 e mostrar todos — rejeitado: polui UI, slider é mais elegante
**Impacto:** função `simular_politica` precisa ser rápida (ver decisão de vetorização) para UX fluida.
**Revisitar se:** surgir dado empírico real de taxa de aceitação → substituir slider por valor calibrado + banda de incerteza.

### [2026-04-17 17:30] Regra crítica: Conjunto A vs Conjunto B
**Contexto:** o dataset enriquecido (com advogado, escritório, datas) contém campos sintéticos. Usar esse dataset para treinar o XGBoost vazaria os padrões fabricados.
**Decisão:** manter dois parquets separados e nunca misturá-los:
- `casos_60k.parquet` (Conjunto A, dados reais) — treino, baseline, contrafactual
- `casos_enriquecidos.parquet` (Conjunto B, real + sintético) — exclusivamente dashboards de aderência
**Direção de dependência:** B consome output do XGBoost. Nunca o contrário.
**Impacto:** duas cargas de leitura no dashboard. `@st.cache_data` neutraliza o custo.
**Revisitar se:** a frente XGBoost decidir que quer o dataset enriquecido para alguma análise — aí precisamos remover os sintéticos ou documentar que são features, não labels.

---

## Glossário de métricas

Atalhos de nomes usados no código:

| ID | Nome | Descrição curta | Arquivo |
|---|---|---|---|
| A01 | Taxa de Seguimento Global | `% casos onde ação tomada = recomendada` | `metrics_adherence.py` |
| A02 | Taxa de Override | `1 − A01` | `metrics_adherence.py` |
| A05 | Aderência por advogado | ranking individual | `metrics_adherence.py` |
| A06 | Aderência por escritório | ranking organizacional | `metrics_adherence.py` |
| A08 | Aderência por faixa de valor | P0 — detecta viés em casos caros | `metrics_adherence.py` |
| A18 | Drift temporal | série mensal da aderência | `metrics_adherence.py` |
| A20 | Aderência ponderada por valor | R$ seguindo política / R$ total | `metrics_adherence.py` |
| E02 | Economia Total vs Baseline | contrafactual com `prob_aceita` | `counterfactual.py` |

Catálogo completo das 40 métricas (A01–A20 + E01–E20) em `hackathon_metricas_monitoramento(1).xlsx`.

---

## Pendências conhecidas

- [ ] Receber CSV real da política da frente XGBoost (até 17/04 23h)
- [ ] Calibrar `prob_aceita` com dado empírico (pós-hackathon)
- [ ] Adicionar testes de regressão para mudança de baseline
