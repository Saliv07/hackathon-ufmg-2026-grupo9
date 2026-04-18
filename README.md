# HACKATHON UFMG 2026 — Enter AI Challenge

**17 e 18 de Abril de 2026**

---

# 🚀 Início Rápido (Quick Start)

Para rodar o projeto agora mesmo, siga estes passos:

1. **Abra o seu terminal.**
2. **Entre na pasta onde o código foi baixado:**

    ```bash
    cd hackathon-ufmg-2026-grupo9
    ```

    *(Dica: o nome da pasta pode variar dependendo de como você baixou. Pode ser `Grupo-9-Hackathon-master`, por exemplo).*

3. **Rode o script automático:**
    - **No Windows**: `.\run`
    - **No Linux ou macOS**: `./run.sh` (ou `bash run.sh`)

---

# 🛠️ Como rodar manualmente (caso o script automático falhe)

Se os scripts acima derem erro, você pode subir o projeto manualmente. O projeto é dividido em duas partes que devem rodar ao mesmo tempo (em terminais separados).

### Pré-requisitos (Dependências)

- **Node.js (v18+) e npm** (para rodar o painel frontend)
- **Python 3.8+** (para rodar a inteligência artificial do backend)

### 1. Rodando o Backend (Python)

Abra uma janela no terminal na pasta raiz do projeto e execute:

```bash
# Entre na pasta do backend
cd backend

# Crie um ambiente virtual para instalar as dependências
python3 -m venv venv

# Ative o ambiente virtual
# -> No Linux/macOS:
source venv/bin/activate
# -> No Windows:
# .\venv\Scripts\activate

# Instale as dependências da aplicação
pip install -r requirements.txt

# Inicie a aplicação
python main.py
```

### 2. Rodando o Frontend (Node.js)

Abra uma **nova janela (ou aba) do terminal**, vá até a pasta raiz do projeto e execute:

```bash
# Entre na pasta do frontend
cd frontend

# Instale as dependências
npm install

# Inicie o servidor
npm run dev
```

Por fim, acesse o link (geralmente `http://localhost:5000`) que irá aparecer no terminal do Frontend!
## 🚀 Como Executar o Projeto

Tudo roda em **um único processo Python** na porta **5000** (Flask servindo React + API + Dash do monitoramento).

### 1. Pré-requisitos
- **Python** 3.10+ ([download](https://www.python.org/downloads/))
- **Node.js** 20.19+ ou 22.12+ ([download](https://nodejs.org/)) — pra buildar o frontend
- Chave da OpenAI no arquivo `.env` (na raiz do projeto)

### 2. `.env`
```env
OPENAI_API_KEY=sk-sua-chave-aqui
```

### 3. Execução — um comando só (Windows, macOS, Linux)
```bash
python run.py
```

O script cuida de tudo:
- cria o venv do backend e instala dependências Python
- instala dependências Node (`npm install`)
- faz `npm run build` do frontend
- gera os artefatos do monitoramento (parquets) se faltarem
- sobe o Flask+Dash em `http://localhost:5000/`

Para parar: `Ctrl+C`.

Acessos:
```
http://localhost:5000/                    → frontend React
http://localhost:5000/api/*               → backend Flask (cases, stats, analyze, upload)
http://localhost:5000/monitoramento/      → dashboard Dash (aderência + efetividade)
```

### 4. Artefatos pesados do modelo (opcional, melhora o monitoramento)

Os `.pkl` do XGBoost não são versionados. Para baixá-los:

```bash
git checkout origin/master -- artefatos/
```

Sem isso o monitoramento cai num fallback de política mock.

---

## 🛠️ Estrutura do Projeto

O projeto tem **três frentes** integradas no mesmo repositório:

| Frente | Pasta | Papel |
|---|---|---|
| **Política de acordos** | `src/policy/`, `artefatos/`, `scripts/`, `docs/politica_acordo.md` | Engine Python (regras + XGBoost) que decide acordo vs defesa e sugere valor |
| **Plataforma do advogado** | `backend/`, `frontend/` | Interface onde o advogado consome a recomendação e registra a decisão |
| **Monitoramento** | `src/monitor/`, `tests/`, `docs/DECISOES.md` | Dashboards de aderência (req. 4) e efetividade (req. 5), montados como sub-app Dash no mesmo Flask |

### Integração cruzada

- O Dashboard Macro (`frontend/src/components/Dashboard.jsx`) consome `stats.policy_projection` — simulação da engine `src/policy/` via endpoint `/api/stats`.
- O dashboard de monitoramento (`/monitoramento/`) consome `data/processed/politica_output.csv` (output do XGBoost) quando existe; senão cai no mock.
- Filtros do monitoramento (UF, escritório, sub-assunto, período, prob_aceita) vivem na sidebar React e são passados via URL query string.

### Estrutura de pastas

- `run.py`: orquestrador único (substituiu `run.sh`/`run.ps1`/`run.bat`)
- `backend/`: API Flask com rotas `/api/*` + montagem do Dash
- `frontend/`: Interface React (Vite)
- `src/policy/`: Engine da política de acordos (regras + pricing + ML)
- `src/monitor/`: Frente de monitoramento (gerador sintético, métricas, Dash app, política XGBoost)
- `tests/`: Suíte pytest (65 testes)
- `data/`: Base histórica + documentos de exemplo
- `artefatos/`: Modelo XGBoost e metadados (arquivos leves versionados; `.pkl` em `.gitignore`)
- `scripts/`: Pipelines de preparação e treino do modelo
- `docs/`: Documentação, política, DECISOES.md
