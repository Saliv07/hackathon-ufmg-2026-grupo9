# Guia de Configuração Detalhado

Este guia explica como preparar seu ambiente do zero para rodar a solução do **Grupo 9**.

O projeto tem três frentes convivendo no mesmo repositório:

- **Plataforma do advogado** (backend Flask + frontend React)
- **Política de acordos** (pacote `src/policy/` + modelo XGBoost em `artefatos/`)
- **Monitoramento** (dashboards Dash de aderência e efetividade, montados no mesmo Flask)

Tudo roda em **um único processo Python** na porta **5000**.

---

## 1. Requisitos de Software

Você precisará ter instalado em sua máquina:

- **Python 3.10+** — [download](https://www.python.org/downloads/) (marque "Add Python to PATH" no Windows)
- **Node.js 20.19+ ou 22.12+** — [download](https://nodejs.org/) (ver `.nvmrc`)
- **Git** — para versionamento

Nenhum outro binário externo é necessário (sem Docker, sem Caddy, sem scripts shell-specific).

---

## 2. Configuração do Ambiente

### Passo 1: Clone
```bash
git clone https://github.com/Saliv07/hackathon-ufmg-2026-grupo9.git
cd hackathon-ufmg-2026-grupo9
```

### Passo 2: Variáveis de ambiente
Crie o arquivo `.env` na raiz do projeto:

```env
OPENAI_API_KEY=sk-sua-chave-aqui-da-openai
```

### Passo 3: Artefatos do XGBoost (opcional, mas recomendado)

Os arquivos pesados do modelo (`*.pkl`, ~20 MB) são ignorados pelo git. Para baixá-los:

```bash
git checkout origin/master -- artefatos/
```

Sem isso o monitoramento cai num fallback de política mock.

### Passo 4: Execução

**Um único comando, idêntico em Windows, macOS e Linux:**

```bash
python run.py
```

O script cuida de tudo automaticamente:

1. Verifica pré-requisitos (Python 3.10+, Node 20+)
2. Cria o venv do backend e instala as dependências Python
3. Instala as dependências do Node (`npm install`)
4. Faz o build do frontend (`npm run build`)
5. Gera os artefatos do monitoramento (parquets) se faltarem
6. Sobe o Flask + Dash em foreground

Após iniciar, acesse:

- `http://localhost:5000/` — plataforma (frontend React)
- `http://localhost:5000/api/*` — backend Flask
- `http://localhost:5000/monitoramento/` — dashboard Dash (também pelo menu "Monitoramento" dentro da plataforma)

**Para parar:** `Ctrl+C`.

---

## 3. Troubleshooting

### "Python 3.10+ necessário"
Atualize o Python. Se tiver múltiplas versões, rode explicitamente: `python3.10 run.py` ou `python3.12 run.py`.

### "Node.js/npm não encontrado no PATH"
Instale Node 20+ em [nodejs.org](https://nodejs.org/). Depois feche e reabra o terminal.

### Backend sobe, mas o frontend mostra "página não encontrada"
Verifique se `frontend/dist/index.html` existe. Se não, rode `python run.py` de novo — a etapa de build pode ter falhado silenciosamente.

### Dashboard de monitoramento mostra "indisponível"
Os parquets em `data/processed/` são necessários. Rode `python run.py` uma vez completo para gerá-los. Se persistir, verifique se o Excel `Hackaton_Enter_Base_Candidatos.xlsx` existe em `data/` ou `data/raw/`.

### `pip install` falha por política corporativa / proxy
Configure o proxy do pip:
```bash
./backend/venv/bin/pip install --proxy http://seu.proxy:porta -r backend/requirements.txt
```
E rode `python run.py` de novo — o script pula a instalação se as deps já estiverem OK.

### `Address already in use` na porta 5000
Outra aplicação está ocupando a 5000. Encerre-a ou defina `FLASK_RUN_PORT=5050` e ajuste `run.py`.

---

## 4. Suíte de testes

A frente de monitoramento tem 65 testes automáticos:

```bash
./backend/venv/bin/pytest tests/ -q
```

Cobertura em 3 camadas: smoke, propriedades e unitários (ver `docs/DECISOES.md`).

---

## 5. Pipeline manual (debug)

Se preferir rodar as etapas isoladamente sem o `run.py`:

```bash
# Backend venv e deps
python3 -m venv backend/venv
./backend/venv/bin/pip install -r backend/requirements.txt

# Frontend build
cd frontend && npm install && npm run build && cd ..

# Artefatos do monitoramento
./backend/venv/bin/python -m src.monitor.load_data
./backend/venv/bin/python -m src.monitor.baseline
./backend/venv/bin/python -m src.monitor.gerar_sintetico
# Opcional (se artefatos/ tiver o modelo)
./backend/venv/bin/python -m src.monitor.politica_xgboost

# Sobe o servidor
cd backend && ./venv/bin/python main.py
```
