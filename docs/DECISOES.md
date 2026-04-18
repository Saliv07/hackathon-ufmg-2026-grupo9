# Log de Decisões — Frente de Monitoramento

**Projeto:** Hackathon UFMG 2026 / Enter — Política de Acordos Banco UFMG
**Escopo:** Requisitos 4 (Aderência) e 5 (Efetividade)
**Responsável:** Matheus — Nekark Data Intelligence
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
