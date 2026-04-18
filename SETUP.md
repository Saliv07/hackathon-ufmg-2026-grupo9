# Guia de Configuração Detalhado

Este guia explica como preparar seu ambiente do zero para rodar a solução do **Grupo 9**.

O projeto tem três frentes convivendo no mesmo repositório:

- **Plataforma do advogado** (backend Flask + frontend React) — seção 2
- **Modelo XGBoost** (política de acordos) — ver `docs/politica_acordo.md`
- **Monitoramento** (dashboards de aderência e efetividade) — seção 4

---

## 1. Requisitos de Software

Você precisará ter instalado em sua máquina:

*   **Python 3.9+**: [Download aqui](https://www.python.org/downloads/) (Marque a opção "Add Python to PATH" no Windows).
*   **Node.js 18+**: [Download aqui](https://nodejs.org/).
*   **Git**: Para versionamento.

---

## 2. Configuração da Plataforma (backend + frontend)

### Passo 1: Download/Clone
```bash
git clone https://github.com/Saliv07/hackathon-ufmg-2026-grupo9.git
cd hackathon-ufmg-2026-grupo9
```

### Passo 2: Variáveis de Ambiente
Crie um arquivo chamado `.env` na raiz da pasta `hackathon-ufmg-2026-grupo9`. O conteúdo deve ser:

```env
OPENAI_API_KEY=sk-sua-chave-aqui-da-openai
```

### Passo 3: Execução

#### Windows (PowerShell)
Se for a primeira vez rodando scripts no seu PowerShell, você pode precisar liberar a permissão:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Depois, basta rodar o facilitador:
```powershell
.\run.ps1
```

#### Linux ou macOS
```bash
bash run.sh
```

---

## 3. Troubleshooting da plataforma

### Erro: "python" não reconhecido
Verifique se o Python está no seu PATH. Em alguns sistemas, o comando pode ser `python3` (o script `run.sh` já tenta usar `python3`).

### Erro: Conexão recusada no Frontend
O Frontend espera que o Backend esteja rodando na porta `5000`. Se o backend falhar ao iniciar, o frontend mostrará uma tela de carregamento infinita ou erro de conexão. Verifique se a porta 5000 não está sendo usada por outro programa.

### Dados Históricos
O backend tenta carregar a base histórica de um arquivo Excel. Se o arquivo `Hackaton_Enter_Base_Candidatos.xlsx` não for encontrado nos caminhos mapeados em `backend/data.py`, o sistema funcionará apenas com os dados mockados de exemplo.

---

## 4. Rodar apenas a frente de monitoramento

A frente de monitoramento (requisitos 4 e 5 do enunciado) tem seu próprio pipeline independente da plataforma. Use esta seção se quer rodar só os dashboards de aderência e efetividade.

### Pré-requisitos
- Python 3.10 ou superior (testado em 3.14.3)
- Arquivo `Hackaton_Enter_Base_Candidatos.xlsx` em `data/` ou `data/raw/`

### Instalação

```bash
cd hackathon-ufmg-2026-grupo9
git checkout vilas  # ou a branch onde a frente está
python3 -m venv venv
source venv/bin/activate      # Linux/Mac
# venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

### Pipeline de geração de artefatos

Execute na ordem (cada etapa depende da anterior):

```bash
# 1. Carrega o xlsx → casos_60k.parquet (~2 MB, 60k × 17 colunas)
python -m src.monitor.load_data

# 2. Calcula números de referência → baseline.json
python -m src.monitor.baseline

# 3. Gera dataset enriquecido → casos_enriquecidos.parquet (60k × 31 colunas)
python -m src.monitor.gerar_sintetico
```

Tempo total: < 30 segundos em máquina moderna.

### Executar o dashboard

```bash
streamlit run src/monitor/dashboards/app.py
```

Abre em `http://localhost:8501`. Sidebar tem 3 abas:
- **Visão Geral** — baseline pré-política (dados reais dos 60k)
- **Aderência** — os advogados estão seguindo a política? (dados sintéticos enriquecidos)
- **Efetividade** — a política está gerando resultado? (contrafactual com slider de sensibilidade)

### Rodar a bateria de testes

```bash
pytest tests/ -v
```

Esperado: **65+ testes passando em ~2s.** Cobertura em 3 níveis (smoke, propriedades, unitários).

### Integração com output real do XGBoost

Quando a frente de algoritmo entregar o CSV com a política real:

```bash
cp /caminho/para/politica_output.csv data/processed/
# Reiniciar o Streamlit — ele detecta o CSV automaticamente
```

Formato esperado:
```
numero_processo,acao_recomendada,valor_acordo_recomendado,score_confianca
```

### Troubleshooting do monitoramento

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
