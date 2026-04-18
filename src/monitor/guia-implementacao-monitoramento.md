# Guia de Implementação — Monitoramento de Aderência e Efetividade

**Projeto:** Hackathon UFMG / Enter — Política de Acordos do Banco UFMG
**Escopo deste guia:** implementação da frente de **monitoramento** (requisitos 4 e 5 do enunciado).
**Autor responsável:** Matheus — Nekark Data Intelligence.
**Data:** 17 de abril de 2026.

---

## Contexto do projeto

### Visão geral

A Enter é uma empresa de Enterprise AI focada em processos jurídicos cíveis massificados. O Banco UFMG recebe ~5.000 processos por mês em que o autor alega não reconhecer a contratação de um empréstimo. Para cada processo, o banco precisa decidir entre **defesa** ou **acordo**.

O projeto constrói uma **política de acordos** suportada por IA, que:

1. Define a regra de decisão (acordo vs defesa) e o valor de oferta.
2. É implementada pelo advogado externo através de uma plataforma.
3. É monitorada quanto à aderência (advogados seguem?) e à efetividade (está dando resultado?).

### Divisão de frentes no time

| Frente | Responsável | Entregável |
|---|---|---|
| Label sintético + XGBoost | 2 pessoas | Modelo treinado que produz `acao_recomendada` + `valor_acordo_recomendado` + `score_confianca` por caso |
| Plataforma do advogado | 2 pessoas | Interface onde o advogado consome a recomendação e registra a decisão |
| **Monitoramento (este guia)** | **1 pessoa (Matheus)** | **Dashboards de aderência e efetividade + baseline + motor contrafactual** |
| Suporte geral | 1 pessoa | Integração e apresentação |

### Escopo específico deste guia

Implementar os dois monitoramentos exigidos pelo enunciado:

- **Monitoramento de Aderência** — os advogados estão seguindo a política? Natureza operacional, audiência é coordenação jurídica.
- **Monitoramento de Efetividade** — a política está gerando o resultado esperado? Natureza estratégica, audiência é diretoria/C-level.

---

## Dados disponíveis

### Dados reais (já entregues pela Enter)

Arquivo: `hackathon_Hackaton_Enter_Base_Candidatos.xlsx` com duas abas:

**Aba 1 — Resultados dos processos (60.000 linhas × 8 colunas):**
- `Número do processo` · `UF` · `Assunto` · `Sub-assunto` (Golpe/Genérico)
- `Resultado macro` (Êxito/Não Êxito)
- `Resultado micro` (Improcedência · Extinção · Parcial procedência · Procedência · Acordo)
- `Valor da causa` (R$) · `Valor da condenação/indenização` (R$)

**Aba 2 — Subsídios disponibilizados (60.000 linhas × 7 colunas):**
- Número do processo + 6 colunas binárias (0/1) indicando presença de cada documento: Contrato, Extrato, Comprovante de crédito, Dossiê, Demonstrativo de evolução da dívida, Laudo referenciado.

### Dados que NÃO existem e precisam ser simulados

A base do hackathon **não contém** as dimensões operacionais necessárias para aderência:

- `advogado_id`, `escritorio_id` — agentes que tomam decisão
- `data_distribuicao`, `data_decisao` — séries temporais
- `acao_tomada` — decisão efetiva do advogado
- `razao_override` — justificativa quando desvia da política
- `valor_acordo_proposto`, `resultado_negociacao` — dados de negociação

Esses campos serão **gerados sinteticamente** com vieses controlados e plausíveis.

### Dados que chegarão de outras frentes

- **Da frente XGBoost (até 23h do dia 17):** CSV com `numero_processo`, `acao_recomendada`, `valor_acordo_recomendado`, `score_confianca`. Esse é o **output da política** e será consumido pelo pipeline de monitoramento.

---

## Baseline pré-política (números dos 60k)

Estes são os números que servem de benchmark. Cada métrica de efetividade se compara contra eles.

### Volumetria

| Métrica | Valor | Observação |
|---|---:|---|
| Total de casos | 60.000 | |
| Taxa de êxito macro | 69,56% | 41.733 casos |
| Taxa de não êxito | 30,44% | 18.267 casos |
| % Improcedência | 46,56% | 27.935 casos |
| % Extinção | 23,00% | 13.798 casos |
| % Parcial procedência | 20,41% | 12.248 casos |
| % Procedência total | 9,57% | 5.739 casos |
| % Acordo atual | 0,47% | 280 casos — política implícita atual é "defender sempre" |

### Financeiro

| Métrica | Valor |
|---|---:|
| Valor médio da causa | R$ 14.982 |
| Condenação média (geral) | R$ 3.216 |
| Condenação média \| Procedência | R$ 13.525 |
| Condenação média \| Parcial | R$ 9.315 |
| Valor médio do acordo | R$ 4.540 |
| Custo total estimado | ~R$ 193M |

### Correlação completude × êxito (preditor primário)

| Nº Subsídios | Casos | % Êxito Banco |
|---:|---:|---:|
| 0 | 57 | 0% |
| 1 | 745 | 3% |
| 2 | 3.498 | 13% |
| 3 | 8.811 | 34% |
| 4 | 15.719 | 64% |
| 5 | 19.518 | 87% |
| 6 | 11.652 | 96% |

**Insight:** transição crítica em 3 subsídios. Abaixo, defesa é muito arriscada. Acima, banco tem crescente vantagem.

### Oportunidade estimada

- Economia realista: ~R$ 55M/ano (50% dos casos de não-êxito identificáveis ex-ante).
- Economia média por caso: ~R$ 3.091.

---

## Regra crítica de arquitetura

**Dois datasets convivem no projeto. Nunca devem ser misturados:**

| Conjunto | Uso | Contém sintético? |
|---|---|---|
| **A** — 60k crus | Treino do XGBoost · motor contrafactual · calibração da política | Não |
| **B** — 60k enriquecidos | Exclusivamente dashboards de aderência | Sim (advogado, escritório, datas, ação tomada, razão override) |

**Direção de dependência:** Conjunto B consome o output do XGBoost (`acao_recomendada`) como input. Nunca o contrário.

**Risco se misturar:** o XGBoost aprende padrões fabricados pelo gerador sintético. Feature importance fica contaminado. Avaliador técnico identifica na hora como vazamento circular.

---

## Stack técnico

- **Python 3.10+**
- **pandas** — manipulação de dados
- **numpy** — geração sintética com vieses controlados
- **pyarrow** — formato parquet (rápido)
- **openpyxl** — leitura do xlsx original
- **streamlit** — dashboards
- **plotly** — gráficos interativos

---

## Estrutura do projeto

```
hackathon-monitoramento/
├── data/
│   ├── raw/
│   │   └── hackathon_Hackaton_Enter_Base_Candidatos.xlsx
│   └── processed/
│       ├── casos_60k.parquet           (Conjunto A — dados reais)
│       ├── casos_enriquecidos.parquet  (Conjunto B — real + sintético)
│       └── baseline.json               (números de referência)
├── src/
│   ├── baseline.py
│   ├── gerar_sintetico.py
│   ├── metrics_adherence.py
│   ├── metrics_effectiveness.py
│   ├── counterfactual.py
│   └── alerts.py
├── notebooks/
│   └── 01_load_data.ipynb
├── dashboards/
│   └── app.py
├── outputs/
│   └── (screenshots, exports)
├── .gitignore
└── requirements.txt
```

---

## Implementação passo a passo

### Passo 1 — Estrutura e ambiente (15 min)

```bash
mkdir -p hackathon-monitoramento/{data/raw,data/processed,src,notebooks,dashboards,outputs}
cd hackathon-monitoramento
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install pandas numpy openpyxl pyarrow streamlit plotly
git init
```

Criar `.gitignore`:

```
venv/
data/raw/
__pycache__/
.ipynb_checkpoints/
*.pyc
```

Criar `requirements.txt`:

```
pandas>=2.0
numpy>=1.24
openpyxl>=3.1
pyarrow>=14.0
streamlit>=1.28
plotly>=5.18
```

Copiar a planilha original da Enter para `data/raw/`.

**Validação:** `ls data/raw/` mostra o xlsx. `streamlit --version` responde.

---

### Passo 2 — Carregar e persistir os 60k (15 min)

Criar `notebooks/01_load_data.ipynb` ou script `src/load_data.py`:

```python
import pandas as pd
from pathlib import Path

RAW_PATH = Path("data/raw/hackathon_Hackaton_Enter_Base_Candidatos.xlsx")
OUT_PATH = Path("data/processed/casos_60k.parquet")

# Ler as duas abas
res = pd.read_excel(RAW_PATH, sheet_name="Resultados dos processos")
sub = pd.read_excel(RAW_PATH, sheet_name="Subsídios disponibilizados", header=1)

# Normalizar nomes de colunas pra snake_case
res.columns = [
    "numero_processo", "uf", "assunto", "sub_assunto",
    "resultado_macro", "resultado_micro",
    "valor_causa", "valor_condenacao"
]
sub = sub.rename(columns={"Número do processos": "numero_processo"})
sub.columns = [
    "numero_processo",
    "subs_contrato", "subs_extrato", "subs_comprovante",
    "subs_dossie", "subs_demonstrativo", "subs_laudo"
]

# Juntar
df = res.merge(sub, on="numero_processo", how="left")

# Derivar campos (fonte = DERIV no dicionário)
df["subs_total"] = df[[
    "subs_contrato", "subs_extrato", "subs_comprovante",
    "subs_dossie", "subs_demonstrativo", "subs_laudo"
]].sum(axis=1)

df["faixa_valor"] = pd.cut(
    df["valor_causa"],
    bins=[0, 5000, 15000, float("inf")],
    labels=["Baixo", "Médio", "Alto"]
)

df["faixa_completude"] = pd.cut(
    df["subs_total"],
    bins=[-1, 2, 4, 6],
    labels=["Frágil", "Parcial", "Sólida"]
)

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
df.to_parquet(OUT_PATH, index=False)

print(f"Shape: {df.shape}")
print(f"Colunas: {df.columns.tolist()}")
print(df.head())
```

**Validação:**
- Arquivo `data/processed/casos_60k.parquet` existe (~2MB).
- Shape igual a `(60000, 12)`.
- Colunas com nomes em snake_case.

---

### Passo 3 — Calcular e salvar o baseline (30 min)

Criar `src/baseline.py`:

```python
import pandas as pd
import json
from pathlib import Path

df = pd.read_parquet("data/processed/casos_60k.parquet")

# Completude × êxito (converter keys para string para serialização JSON)
completude_exito = df.groupby("subs_total").agg(
    n_casos=("numero_processo", "count"),
    taxa_exito=("resultado_macro", lambda s: (s == "Êxito").mean())
)

sub_assunto = df.groupby("sub_assunto").agg(
    n_casos=("numero_processo", "count"),
    taxa_exito=("resultado_macro", lambda s: (s == "Êxito").mean())
)

baseline = {
    "volumetria": {
        "total_casos": int(len(df)),
        "taxa_exito_macro": float((df["resultado_macro"] == "Êxito").mean()),
        "taxa_nao_exito_macro": float((df["resultado_macro"] == "Não Êxito").mean()),
        "dist_resultado_micro": df["resultado_micro"].value_counts(normalize=True).to_dict(),
    },
    "financeiro": {
        "valor_causa_medio": float(df["valor_causa"].mean()),
        "valor_causa_mediano": float(df["valor_causa"].median()),
        "condenacao_media_geral": float(df["valor_condenacao"].mean()),
        "condenacao_media_procedencia": float(
            df.loc[df["resultado_micro"] == "Procedência", "valor_condenacao"].mean()
        ),
        "condenacao_media_parcial": float(
            df.loc[df["resultado_micro"] == "Parcial procedência", "valor_condenacao"].mean()
        ),
        "valor_medio_acordo": float(
            df.loc[df["resultado_micro"] == "Acordo", "valor_condenacao"].mean()
        ),
        "custo_total_estimado": float(df["valor_condenacao"].sum()),
    },
    "completude_vs_exito": {
        str(k): {"n_casos": int(v["n_casos"]), "taxa_exito": float(v["taxa_exito"])}
        for k, v in completude_exito.to_dict(orient="index").items()
    },
    "sub_assunto": {
        k: {"n_casos": int(v["n_casos"]), "taxa_exito": float(v["taxa_exito"])}
        for k, v in sub_assunto.to_dict(orient="index").items()
    },
}

out = Path("data/processed/baseline.json")
out.write_text(json.dumps(baseline, indent=2, ensure_ascii=False))
print(json.dumps(baseline, indent=2, ensure_ascii=False))
```

Executar:
```bash
python src/baseline.py
```

**Validação:** números devem coincidir (taxa de êxito ~69,56%, condenação média ~R$ 3.216, etc.).

---

### Passo 4 — Esqueleto do dashboard (30 min)

Criar `dashboards/app.py`:

```python
import streamlit as st
import pandas as pd
import json
from pathlib import Path

st.set_page_config(
    page_title="Monitoramento UFMG",
    layout="wide",
    page_icon="⚖️"
)

# ==================== Carregamento ====================
@st.cache_data
def load_baseline():
    with open("data/processed/baseline.json") as f:
        return json.load(f)

@st.cache_data
def load_casos():
    return pd.read_parquet("data/processed/casos_60k.parquet")

@st.cache_data
def load_enriquecidos():
    path = Path("data/processed/casos_enriquecidos.parquet")
    return pd.read_parquet(path) if path.exists() else None

baseline = load_baseline()
df = load_casos()
df_enr = load_enriquecidos()

# ==================== Sidebar ====================
st.sidebar.title("⚖️ Monitoramento")
st.sidebar.caption("Política de Acordos · Banco UFMG")
view = st.sidebar.radio(
    "Visão",
    ["Visão Geral", "Aderência", "Efetividade"]
)

# ==================== Visão Geral ====================
if view == "Visão Geral":
    st.title("Banco UFMG · Política de Acordos")
    st.caption("Baseline pré-política · 60.000 casos históricos")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Casos Analisados",
        f"{baseline['volumetria']['total_casos']:,}".replace(",", ".")
    )
    c2.metric(
        "Taxa de Êxito Banco",
        f"{baseline['volumetria']['taxa_exito_macro']:.1%}"
    )
    c3.metric(
        "Custo Total Estimado",
        f"R$ {baseline['financeiro']['custo_total_estimado']/1e6:.1f}M"
    )
    c4.metric(
        "% Acordo Hoje",
        f"{baseline['volumetria']['dist_resultado_micro'].get('Acordo', 0):.2%}"
    )

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Distribuição de Resultado Micro")
        dist = pd.Series(baseline["volumetria"]["dist_resultado_micro"])
        st.bar_chart(dist)

    with col2:
        st.subheader("Completude Probatória × Êxito do Banco")
        comp = pd.DataFrame(baseline["completude_vs_exito"]).T
        comp.index = comp.index.astype(int)
        st.bar_chart(comp["taxa_exito"])

# ==================== Aderência ====================
elif view == "Aderência":
    st.title("Monitoramento de Aderência")
    st.caption("Os advogados estão seguindo a política?")

    if df_enr is None:
        st.info(
            "Dataset enriquecido ainda não disponível. "
            "Execute `python src/gerar_sintetico.py` para gerar."
        )
    else:
        # KPIs principais
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Taxa de Seguimento", f"{df_enr['aderente'].mean():.1%}")
        c2.metric("Taxa de Override", f"{1 - df_enr['aderente'].mean():.1%}")
        c3.metric("Advogados", df_enr['advogado_id'].nunique())
        c4.metric("Escritórios", df_enr['escritorio_id'].nunique())

        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Aderência por Escritório")
            por_esc = df_enr.groupby("escritorio_id")["aderente"].mean().sort_values()
            st.bar_chart(por_esc)

        with col2:
            st.subheader("Aderência por Faixa de Valor")
            por_faixa = df_enr.groupby("faixa_valor", observed=False)["aderente"].mean()
            st.bar_chart(por_faixa)

# ==================== Efetividade ====================
elif view == "Efetividade":
    st.title("Monitoramento de Efetividade")
    st.caption("A política está gerando o resultado esperado?")
    st.info("Aguardando integração com output da política para cálculo contrafactual.")
```

Executar:
```bash
streamlit run dashboards/app.py
```

**Validação:** navegador abre em `localhost:8501`. As 3 abas funcionam. "Visão Geral" mostra KPIs reais. "Aderência" mostra mensagem informativa. "Efetividade" mostra placeholder.

---

### Passo 5 — Gerador sintético (90-120 min)

Criar `src/gerar_sintetico.py`:

```python
"""
Gera o dataset enriquecido com as colunas SIM necessárias para monitoramento
de aderência. Pega os 60k reais e adiciona advogados, escritórios, datas e
decisões simuladas com vieses plausíveis.

REGRA CRÍTICA: este dataset NÃO deve ser usado para treinar o XGBoost.
Ele é exclusivamente para alimentar os dashboards de aderência.
"""
import pandas as pd
import numpy as np
from pathlib import Path

np.random.seed(42)

IN_PATH = Path("data/processed/casos_60k.parquet")
OUT_PATH = Path("data/processed/casos_enriquecidos.parquet")

df = pd.read_parquet(IN_PATH).copy()

# ==================== 1. Escritórios com perfil de aderência ====================
# 3 escritórios ótimos (~93%), 5 medianos (~80%), 2 problemáticos (~62%)
escritorios = pd.DataFrame({
    "escritorio_id": [f"ESC{i:02d}" for i in range(1, 11)],
    "aderencia_base": [0.95, 0.93, 0.92, 0.85, 0.83, 0.80, 0.78, 0.68, 0.64, 0.60],
    "regiao": ["SE", "SE", "S", "S", "NE", "NE", "N", "CO", "N", "NE"],
})

# ==================== 2. Advogados distribuídos nos escritórios ====================
# 50 advogados, 5 por escritório
advogados_rows = []
for i in range(50):
    esc = escritorios.iloc[i % 10]
    # Desvio individual ±5pp em torno do perfil do escritório
    aderencia_indiv = np.clip(
        esc["aderencia_base"] + np.random.normal(0, 0.05),
        0.40, 0.99
    )
    advogados_rows.append({
        "advogado_id": f"ADV{i+1:03d}",
        "escritorio_id": esc["escritorio_id"],
        "aderencia_esperada": aderencia_indiv,
    })
advogados = pd.DataFrame(advogados_rows)

# ==================== 3. Atribuir advogado a cada caso ====================
df["advogado_id"] = np.random.choice(advogados["advogado_id"], size=len(df))
df = df.merge(advogados, on="advogado_id", how="left")

# ==================== 4. Datas ao longo de 12 meses ====================
data_inicial = pd.Timestamp("2025-04-01")
data_final = pd.Timestamp("2026-03-31")
dias_periodo = (data_final - data_inicial).days

df["data_distribuicao"] = data_inicial + pd.to_timedelta(
    np.random.randint(0, dias_periodo, size=len(df)),
    unit="d"
)

# Tempo de decisão: distribuição lognormal (maioria 30min-4h, cauda até 50h)
df["tempo_decisao_min"] = np.clip(
    np.random.lognormal(mean=5.0, sigma=1.4, size=len(df)),
    5, 3000
)
df["data_decisao"] = df["data_distribuicao"] + pd.to_timedelta(
    df["tempo_decisao_min"], unit="m"
)

# ==================== 5. Ação recomendada (MOCK até XGBoost chegar) ====================
# Regra primitiva temporária — substituir pelo CSV do XGBoost quando disponível
# Lógica: poucos subsídios ou hipervulnerabilidade → acordo; caso contrário → defesa
df["acao_recomendada"] = np.where(
    df["subs_total"] <= 3,
    "acordo",
    "defesa"
)

# Valor de acordo recomendado (MOCK): 30% do valor da causa para acordos
df["valor_acordo_recomendado"] = np.where(
    df["acao_recomendada"] == "acordo",
    df["valor_causa"] * 0.30,
    np.nan
)

# ==================== 6. Ação tomada com viés controlado ====================
# Viés adicional: advogados tendem a desviar MAIS em casos de alto valor
ajuste_valor = np.where(df["faixa_valor"] == "Alto", -0.08, 0.0)
prob_seguir = np.clip(df["aderencia_esperada"] + ajuste_valor, 0.2, 0.99)

segue = np.random.random(len(df)) < prob_seguir
df["acao_tomada"] = np.where(
    segue,
    df["acao_recomendada"],
    np.where(df["acao_recomendada"] == "acordo", "defesa", "acordo")
)
df["aderente"] = (df["acao_tomada"] == df["acao_recomendada"]).astype(int)

# ==================== 7. Razão de override ====================
razoes = ["discordancia_score", "info_nova", "neg_em_andamento", "erro_ferramenta", "outro"]
probs_razoes = [0.40, 0.25, 0.15, 0.10, 0.10]
df["razao_override"] = np.where(
    df["aderente"] == 0,
    np.random.choice(razoes, size=len(df), p=probs_razoes),
    None
)

# ==================== 8. Valor de acordo proposto (só se ação_tomada=acordo) ====================
# Proposto tende a ser próximo do recomendado, com ruído ±15%
ruido = np.random.normal(1.0, 0.15, size=len(df))
df["valor_acordo_proposto"] = np.where(
    df["acao_tomada"] == "acordo",
    np.where(
        df["valor_acordo_recomendado"].notna(),
        df["valor_acordo_recomendado"] * ruido,
        df["valor_causa"] * 0.30 * ruido  # quando recomendação era defesa mas advogado fez acordo
    ),
    np.nan
)
df["valor_acordo_proposto"] = df["valor_acordo_proposto"].round(2)

# ==================== 9. Resultado da negociação ====================
# Aceitação depende de quão próximo o proposto está do valor de causa
# Heurística: mais próximo de 30% = mais aceito
resultados_neg = []
for _, row in df.iterrows():
    if pd.isna(row["valor_acordo_proposto"]):
        resultados_neg.append(None)
    else:
        ratio = row["valor_acordo_proposto"] / row["valor_causa"]
        # ratio alto (>0.40) = mais aceito; ratio baixo (<0.20) = rejeitado
        if ratio > 0.40:
            probs = [0.80, 0.15, 0.05]  # aceito, contraproposta, rejeitado
        elif ratio > 0.25:
            probs = [0.65, 0.25, 0.10]
        else:
            probs = [0.35, 0.35, 0.30]
        resultados_neg.append(
            np.random.choice(["aceito", "contraproposta", "rejeitado"], p=probs)
        )
df["resultado_negociacao"] = resultados_neg

# ==================== 10. Salvar ====================
df.to_parquet(OUT_PATH, index=False)

print(f"Dataset enriquecido salvo: {OUT_PATH}")
print(f"Shape: {df.shape}")
print(f"\nColunas: {df.columns.tolist()}")
print(f"\nTaxa de aderência geral: {df['aderente'].mean():.2%}")
print(f"\nAderência por escritório:")
print(df.groupby("escritorio_id")["aderente"].agg(["mean", "count"]).sort_values("mean"))
print(f"\nDistribuição de razões de override:")
print(df.loc[df["aderente"] == 0, "razao_override"].value_counts(normalize=True))
```

Executar:
```bash
python src/gerar_sintetico.py
```

**Validação:**
- Arquivo `data/processed/casos_enriquecidos.parquet` existe.
- Taxa de aderência geral entre 75% e 85%.
- Variação entre escritórios visível (o pior ~60%, o melhor ~95%).
- Distribuição de razões próxima aos pesos `[0.40, 0.25, 0.15, 0.10, 0.10]`.

**Observação importante:** quando o CSV do XGBoost chegar, substituir apenas o **passo 5** deste script pela leitura do CSV. Tudo o mais continua funcionando.

---

### Passo 6 — Módulo de métricas de aderência (60 min)

Criar `src/metrics_adherence.py`:

```python
"""
Cálculo das métricas de aderência conforme catálogo (A01 a A20).
Prioriza as métricas P0 (críticas para o dashboard principal).
"""
import pandas as pd
import numpy as np


# ==================== P0 - Métricas críticas ====================

def taxa_seguimento_global(df: pd.DataFrame) -> float:
    """A01 - Percentual de casos em que ação tomada = recomendação."""
    return float(df["aderente"].mean())


def taxa_override(df: pd.DataFrame) -> float:
    """A02 - Complemento da A01."""
    return 1.0 - taxa_seguimento_global(df)


def distribuicao_acao(df: pd.DataFrame) -> pd.DataFrame:
    """A03 - Compara ação recomendada vs tomada."""
    rec = df["acao_recomendada"].value_counts(normalize=True).rename("recomendada")
    tom = df["acao_tomada"].value_counts(normalize=True).rename("tomada")
    return pd.concat([rec, tom], axis=1).fillna(0)


def aderencia_por_advogado(df: pd.DataFrame) -> pd.DataFrame:
    """A05 - Aderência individual por advogado."""
    return (
        df.groupby("advogado_id")
        .agg(
            aderencia=("aderente", "mean"),
            n_casos=("numero_processo", "count"),
            escritorio=("escritorio_id", "first"),
        )
        .sort_values("aderencia")
    )


def aderencia_por_escritorio(df: pd.DataFrame) -> pd.DataFrame:
    """A06 - Aderência por escritório."""
    return (
        df.groupby("escritorio_id")
        .agg(
            aderencia=("aderente", "mean"),
            n_casos=("numero_processo", "count"),
            n_advogados=("advogado_id", "nunique"),
        )
        .sort_values("aderencia")
    )


def aderencia_por_faixa_valor(df: pd.DataFrame) -> pd.Series:
    """A08 - Aderência por faixa de valor da causa. P0 crítico."""
    return df.groupby("faixa_valor", observed=False)["aderente"].mean()


def aderencia_ponderada_por_valor(df: pd.DataFrame) -> float:
    """A20 - Aderência ponderada pelo valor da causa. P0."""
    return float(
        (df["aderente"] * df["valor_causa"]).sum() / df["valor_causa"].sum()
    )


def drift_temporal_aderencia(df: pd.DataFrame, freq: str = "M") -> pd.Series:
    """A18 - Evolução mensal da taxa de aderência."""
    return (
        df.set_index("data_decisao")["aderente"]
        .resample(freq)
        .mean()
    )


# ==================== P1 - Importantes ====================

def aderencia_por_completude(df: pd.DataFrame) -> pd.Series:
    """A04 - Aderência por faixa de completude probatória."""
    return df.groupby("faixa_completude", observed=False)["aderente"].mean()


def aderencia_por_uf(df: pd.DataFrame) -> pd.Series:
    """A07 - Aderência por UF."""
    return df.groupby("uf")["aderente"].mean().sort_values()


def aderencia_por_subassunto(df: pd.DataFrame) -> pd.Series:
    """A09 - Aderência por sub-assunto (Golpe vs Genérico)."""
    return df.groupby("sub_assunto")["aderente"].mean()


def desvio_valor_acordo(df: pd.DataFrame) -> dict:
    """
    A10, A11 - Desvio entre valor proposto e valor recomendado em acordos.
    Retorna média, mediana e p95 do desvio relativo.
    """
    mask = (
        (df["acao_tomada"] == "acordo")
        & df["valor_acordo_proposto"].notna()
        & df["valor_acordo_recomendado"].notna()
    )
    sub = df.loc[mask].copy()
    if sub.empty:
        return {"n": 0}

    sub["desvio_abs"] = sub["valor_acordo_proposto"] - sub["valor_acordo_recomendado"]
    sub["desvio_rel"] = sub["desvio_abs"] / sub["valor_acordo_recomendado"]
    return {
        "n": len(sub),
        "desvio_rel_medio": float(sub["desvio_rel"].mean()),
        "desvio_rel_mediano": float(sub["desvio_rel"].median()),
        "desvio_abs_p95": float(sub["desvio_abs"].quantile(0.95)),
    }


def distribuicao_razoes_override(df: pd.DataFrame) -> pd.Series:
    """A13 - Distribuição das razões de override."""
    return (
        df.loc[df["aderente"] == 0, "razao_override"]
        .value_counts(normalize=True)
    )


def tempo_decisao_percentis(df: pd.DataFrame) -> dict:
    """A15 - Percentis do tempo até decisão."""
    return {
        "p10_min": float(df["tempo_decisao_min"].quantile(0.10)),
        "mediana_min": float(df["tempo_decisao_min"].median()),
        "p90_min": float(df["tempo_decisao_min"].quantile(0.90)),
        "pct_abaixo_5min": float((df["tempo_decisao_min"] < 5).mean()),
        "pct_acima_48h": float((df["tempo_decisao_min"] > 2880).mean()),
    }


# ==================== Alertas derivados ====================

def alertas_ativos(df: pd.DataFrame) -> list:
    """Avalia todos os thresholds e retorna alertas P0 ativos."""
    alertas = []

    tsg = taxa_seguimento_global(df)
    if tsg < 0.70:
        alertas.append({
            "id": "A01",
            "nome": "Taxa de Seguimento Global",
            "severidade": "P0",
            "valor": tsg,
            "threshold": 0.70,
            "mensagem": f"Taxa de seguimento em {tsg:.1%} (mínimo 70%)",
        })

    tov = taxa_override(df)
    if tov > 0.30:
        alertas.append({
            "id": "A02",
            "nome": "Taxa de Override",
            "severidade": "P0",
            "valor": tov,
            "threshold": 0.30,
            "mensagem": f"Taxa de override em {tov:.1%} (máximo 30%)",
        })

    # Advogados com aderência < 60%
    por_adv = aderencia_por_advogado(df)
    criticos = por_adv[por_adv["aderencia"] < 0.60]
    for adv_id, row in criticos.iterrows():
        alertas.append({
            "id": "A05",
            "nome": f"Aderência individual crítica — {adv_id}",
            "severidade": "P0",
            "valor": row["aderencia"],
            "threshold": 0.60,
            "mensagem": f"{adv_id} ({row['escritorio']}) em {row['aderencia']:.1%} — requer intervenção",
        })

    # Aderência em faixa Alto < 70%
    por_faixa = aderencia_por_faixa_valor(df)
    if "Alto" in por_faixa.index and por_faixa["Alto"] < 0.70:
        alertas.append({
            "id": "A08",
            "nome": "Aderência em casos de alto valor",
            "severidade": "P0",
            "valor": float(por_faixa["Alto"]),
            "threshold": 0.70,
            "mensagem": f"Aderência em faixa Alto: {por_faixa['Alto']:.1%} — possível viés",
        })

    return alertas


if __name__ == "__main__":
    df = pd.read_parquet("data/processed/casos_enriquecidos.parquet")

    print(f"Taxa de seguimento global: {taxa_seguimento_global(df):.2%}")
    print(f"Taxa de override: {taxa_override(df):.2%}")
    print(f"Aderência ponderada por valor: {aderencia_ponderada_por_valor(df):.2%}")
    print("\nPor escritório:")
    print(aderencia_por_escritorio(df))
    print("\nAlertas ativos:")
    for a in alertas_ativos(df):
        print(f"  [{a['severidade']}] {a['mensagem']}")
```

Executar:
```bash
python src/metrics_adherence.py
```

**Validação:** números coerentes com os vieses do gerador. Lista de alertas ativos impressa (deve incluir pelo menos os 2 escritórios problemáticos).

---

### Passo 7 — Dashboard de aderência completo (60-90 min)

Expandir a aba "Aderência" no `dashboards/app.py` com:

- 4 KPIs no topo (Taxa de Seguimento, Taxa de Override, Aderência Ponderada, % Overrides Justificados).
- Série temporal da aderência (mensal).
- Ranking de advogados (top 10 melhores, top 10 piores).
- Aderência por escritório (barras horizontais).
- Aderência por faixa de valor + por faixa de completude (side by side).
- Distribuição de razões de override (pizza ou barras).
- Painel lateral com alertas ativos.
- Filtros globais: UF, escritório, período, sub-assunto.

Usar plotly para gráficos interativos (`st.plotly_chart`).

---

### Passo 8 — Métricas de efetividade e motor contrafactual (90-120 min)

Criar `src/counterfactual.py`:

```python
"""
Motor contrafactual: dado o baseline dos 60k e a política, simula
qual teria sido o custo total se a política tivesse operado retroativamente.
Produz a métrica E02 (Economia Total vs Baseline).
"""
import pandas as pd
import json


def custo_caso_observado(row: pd.Series) -> float:
    """Custo real de cada caso na base."""
    return float(row["valor_condenacao"])


def custo_caso_sob_politica(row: pd.Series, prob_aceita: float = 0.70) -> float:
    """
    Custo esperado se a política fosse aplicada retroativamente.

    Lógica:
    - Se acao_recomendada = defesa → usa o resultado real (aposta na capacidade do modelo)
    - Se acao_recomendada = acordo → custo esperado = valor_acordo_recomendado × prob_aceita
      + custo_caso_observado × (1 - prob_aceita)  [rejeitou, segue pra sentença]
    """
    if row["acao_recomendada"] == "defesa":
        return row["valor_condenacao"]

    acordo = row.get("valor_acordo_recomendado", row["valor_causa"] * 0.30)
    custo_se_rejeitar = row["valor_condenacao"]
    return prob_aceita * acordo + (1 - prob_aceita) * custo_se_rejeitar


def simular_politica(df: pd.DataFrame, prob_aceita: float = 0.70) -> dict:
    """
    Compara custo observado vs custo sob política.
    Retorna dict com totais e economia.
    """
    df = df.copy()
    df["custo_observado"] = df.apply(custo_caso_observado, axis=1)
    df["custo_politica"] = df.apply(
        lambda r: custo_caso_sob_politica(r, prob_aceita), axis=1
    )

    custo_obs_total = float(df["custo_observado"].sum())
    custo_pol_total = float(df["custo_politica"].sum())
    economia = custo_obs_total - custo_pol_total

    return {
        "custo_observado_total": custo_obs_total,
        "custo_politica_total": custo_pol_total,
        "economia_total": economia,
        "economia_percentual": economia / custo_obs_total if custo_obs_total else 0,
        "economia_por_caso": economia / len(df),
        "n_casos": len(df),
        "prob_aceita_assumida": prob_aceita,
    }


if __name__ == "__main__":
    df = pd.read_parquet("data/processed/casos_enriquecidos.parquet")
    resultado = simular_politica(df)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
```

Criar `src/metrics_effectiveness.py` com as métricas E01 a E20 (priorizar P0).

Implementar a aba "Efetividade" no dashboard com:

- 3 KPIs gigantes (Economia Total, Custo Médio por Caso, Taxa de Aceitação).
- Gráfico de economia acumulada ao longo do tempo.
- Distribuição de Resultado Micro: antes × depois (barras comparativas).
- Custo por faixa de completude.
- Recall em casos de alta perda · Precision de defesa.

---

### Passo 9 — Integração com output real do XGBoost (30 min)

Quando a frente de algoritmo entregar o CSV com as colunas `numero_processo`, `acao_recomendada`, `valor_acordo_recomendado`, `score_confianca`:

Modificar o **passo 5 do `gerar_sintetico.py`** para:

```python
# Substituir o mock por:
politica_output = pd.read_csv("data/politica_output.csv")
df = df.merge(
    politica_output[["numero_processo", "acao_recomendada", "valor_acordo_recomendado", "score_confianca"]],
    on="numero_processo",
    how="left"
)
```

Reexecutar o gerador. Reiniciar o Streamlit. Os dashboards agora operam sobre output real da política.

---

### Passo 10 — Polimento e entrega (30-60 min)

- Capturar 3-4 screenshots dos dashboards para os slides.
- Gravar trecho do vídeo mostrando navegação pelos dashboards (30-45s).
- Garantir que `README.md` do repositório explica como rodar localmente.
- Commit final + push.

---

## Ordem de execução recomendada

| Ordem | Tarefa | Duração | Bloqueia? |
|---|---|---|---|
| 1 | Alinhar com time o schema do output da política | 15 min | Bloqueia 9 |
| 2 | Passo 1 — Ambiente | 15 min | — |
| 3 | Passo 2 — Carregar 60k | 15 min | Bloqueia 4, 5 |
| 4 | Passo 3 — Baseline | 30 min | Bloqueia 8 |
| 5 | Passo 4 — Esqueleto dashboard | 30 min | — |
| 6 | Passo 5 — Gerador sintético | 90-120 min | Bloqueia 6, 7 |
| 7 | Passo 6 — Métricas aderência | 60 min | Bloqueia 7 |
| 8 | Passo 7 — Dashboard aderência completo | 60-90 min | — |
| 9 | Passo 8 — Efetividade + contrafactual | 90-120 min | — |
| 10 | Passo 9 — Integração XGBoost (quando CSV chegar) | 30 min | Depende da frente algoritmo |
| 11 | Passo 10 — Polimento | 30-60 min | Final |

**Tempo total estimado:** 8-12 horas de trabalho efetivo.

---

## Checkpoints de validação

Ao final de cada passo, confirmar:

- [ ] Passo 1: ambiente ativo, `pip list` mostra dependências.
- [ ] Passo 2: `casos_60k.parquet` com shape `(60000, 12)`.
- [ ] Passo 3: `baseline.json` com números coerentes com a base.
- [ ] Passo 4: Streamlit roda, aba "Visão Geral" mostra KPIs reais.
- [ ] Passo 5: `casos_enriquecidos.parquet` com shape `(60000, ~25)` e aderência ~80%.
- [ ] Passo 6: `python src/metrics_adherence.py` imprime métricas e alertas.
- [ ] Passo 7: dashboard de aderência funcional com todos os gráficos.
- [ ] Passo 8: contrafactual calcula economia total no formato esperado.
- [ ] Passo 9: dashboard usa output real da política sem erros.
- [ ] Passo 10: screenshots e vídeo capturados.

---

## Riscos conhecidos e mitigações

| Risco | Mitigação |
|---|---|
| Frente XGBoost atrasa além das 23h | Dashboard funciona com mock de política. Apresenta arquitetura pronta. |
| Schema do output da política muda | Passo 9 é isolado: só troca a fonte de 1 coluna. |
| Performance lenta com 60k linhas no Streamlit | Parquet + `@st.cache_data` já otimiza. Se precisar, pré-agregar em `baseline.json`. |
| Geração sintética com números pouco realistas | Ajustar vieses no passo 5. Dataset sintético é regenerável em segundos. |
| Streamlit trava ou bug visual | Usar plotly direto (mais robusto que componentes nativos). |

---

## Observações para a apresentação

A frente de monitoramento é a que tem a linguagem mais próxima do diretor jurídico (dinheiro economizado, governança, risco). Os slides de maior peso do critério "visão de negócio" têm protagonismo natural:

- **Slide de potencial financeiro:** usa o baseline e a estimativa de ~R$ 55M/ano.
- **Slide de arquitetura do dashboard executivo:** screenshot do dashboard de efetividade.
- **Slide do motor contrafactual:** mostra R$ economizado retroativo.

Assumir explicitamente que os dados operacionais (advogado, escritório) são simulados e que a arquitetura está pronta para dados reais de produção. Isso transforma a limitação em *feature*.

---

*Guia gerado em 17/04/2026. Instruções validadas para execução em 10-12 horas por 1 pessoa.*
