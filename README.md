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
