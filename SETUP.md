# Setup e Execução — Frente de Monitoramento

Instruções para rodar a frente de **monitoramento** (requisitos 4 e 5 do enunciado) localmente.

> Escopo deste SETUP: apenas dashboards de aderência e efetividade. As frentes de algoritmo (XGBoost) e plataforma do advogado têm instruções próprias em seus subdiretórios.

---

## Pré-requisitos

- Python 3.10 ou superior (testado em 3.14.3)
- 500 MB livres em disco (para o parquet gerado e cache do Streamlit)
- Arquivo `Hackaton_Enter_Base_Candidatos.xlsx` fornecido pela Enter

---

## Instalação

```bash
# 1. Clonar o repo e entrar
git clone <url-do-repo>
cd hackathon-ufmg-2026-grupo9
git checkout vilas

# 2. Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate      # Linux/Mac
# venv\Scripts\activate       # Windows

# 3. Instalar dependências
pip install -r requirements.txt
```

---

## Dados

Coloque o arquivo `Hackaton_Enter_Base_Candidatos.xlsx` em `data/raw/` (crie a pasta se precisar):

```bash
mkdir -p data/raw
cp /caminho/para/Hackaton_Enter_Base_Candidatos.xlsx data/raw/
```

Se o arquivo estiver em outro lugar do sistema, pode usar symlink:

```bash
ln -s /caminho/absoluto/Hackaton_Enter_Base_Candidatos.xlsx data/raw/
```

---

## Pipeline de geração de artefatos

Execute na seguinte ordem (cada etapa depende da anterior):

```bash
# 1. Carrega o xlsx → casos_60k.parquet (~2 MB, 60k × 17 colunas)
python -m src.monitor.load_data

# 2. Calcula números de referência → baseline.json
python -m src.monitor.baseline

# 3. Gera dataset enriquecido → casos_enriquecidos.parquet (~60k × 31 colunas)
python -m src.monitor.gerar_sintetico

# 4. (opcional) Valida o contrafactual
python -m src.monitor.counterfactual

# 5. (opcional) Valida as métricas de aderência e efetividade
python -m src.monitor.metrics_adherence
python -m src.monitor.metrics_effectiveness
```

Tempo total: < 30 segundos em máquina moderna.

---

## Executar o dashboard

```bash
streamlit run src/monitor/dashboards/app.py
```

Abre automaticamente em `http://localhost:8501`.

**Navegação:** sidebar à esquerda tem 3 abas:
- **Visão Geral** — baseline pré-política (dados reais dos 60k)
- **Aderência** — os advogados estão seguindo a política? (dados sintéticos enriquecidos)
- **Efetividade** — a política está gerando resultado? (contrafactual com slider de sensibilidade)

---

## Rodar a bateria de testes

```bash
pytest tests/ -v
```

Esperado: **65+ testes passando em ~2s.** Cobertura em 3 níveis por módulo:
- Smoke (arquivos existem, shapes corretos, campos críticos sem NaN)
- Propriedades (monotonicidades, ranges esperados, números do guia)
- Unitários (comportamento das funções de métrica com fixtures sintéticas)

---

## Integração com output real do XGBoost

Quando a frente de algoritmo entregar o CSV com a política real:

```bash
# 1. Copiar o CSV entregue pela equipe
cp /caminho/para/politica_output.csv data/processed/

# 2. Reiniciar o Streamlit (ele detecta o CSV automaticamente)
# O dashboard mostra badge "Fonte: CSV do XGBoost" em vez de "Fonte: mock"
```

Formato esperado do CSV:
```
numero_processo,acao_recomendada,valor_acordo_recomendado,score_confianca
1764352-89.2025.8.06.1818,acordo,4494.75,0.87
...
```

---

## Variáveis de ambiente

Nenhuma variável obrigatória — a frente de monitoramento não depende de APIs externas.

`.env.example` existe para documentação das outras frentes.

---

## Estrutura do projeto (frente de monitoramento)

```
hackathon-ufmg-2026-grupo9/
├── data/
│   ├── raw/                                (xlsx original, não versionado)
│   └── processed/                          (parquet + json gerados)
├── docs/
│   └── DECISOES.md                         (log vivo de decisões, H1-H14)
├── src/monitor/
│   ├── paths.py                            (caminhos canônicos)
│   ├── load_data.py                        (Passo 2 — xlsx → parquet)
│   ├── baseline.py                         (Passo 3 — baseline.json)
│   ├── gerar_sintetico.py                  (Passo 5 — Conjunto B)
│   ├── metrics_adherence.py                (Passo 6 — A01-A20)
│   ├── metrics_effectiveness.py            (Passo 8 — E01-E20)
│   ├── counterfactual.py                   (Passo 8 — motor contrafactual)
│   ├── dashboards/
│   │   └── app.py                          (Streamlit)
│   └── guia-implementacao-monitoramento.md (guia do projeto)
├── tests/
│   ├── conftest.py                         (fixtures compartilhadas)
│   ├── test_load_data.py
│   ├── test_baseline.py
│   ├── test_adherence.py
│   └── test_effectiveness.py
├── requirements.txt
└── SETUP.md
```

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'src.monitor.paths'`**
→ Você está executando de fora do repo root. `cd` pro repo e rode com `python -m src.monitor.<script>`.

**Streamlit pede email no primeiro uso**
→ Crie `~/.streamlit/credentials.toml`:
```toml
[general]
email = ""
```

**Parquet não encontrado ao abrir o dashboard**
→ Rode o pipeline de geração (passos 1-3 acima) antes do `streamlit run`.

**Dashboard está lento quando mexo no slider**
→ Esperado: o contrafactual roda sobre 60k linhas a cada mudança. Está vetorizado com `np.where` (<2s por rodada). Se estiver >5s, checar se `@st.cache_data` está no `load_*()`.
