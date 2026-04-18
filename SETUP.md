# Guia de Configuração Detalhado

Este guia explica como preparar seu ambiente do zero para rodar a solução do **Grupo 9**.

---

## 1. Requisitos de Software

Você precisará ter instalado em sua máquina:

*   **Python 3.9+**: [Download aqui](https://www.python.org/downloads/) (Marque a opção "Add Python to PATH" no Windows).
*   **Node.js 18+**: [Download aqui](https://nodejs.org/).
*   **Git**: Para versionamento.

---

## 2. Configuração do Ambiente

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

## 3. Troubleshooting (Resolução de Problemas)

### Erro: "python" não reconhecido
Verifique se o Python está no seu PATH. Em alguns sistemas, o comando pode ser `python3` (o script `run.sh` já tenta usar `python3`).

### Erro: Conexão recusada no Frontend
O Frontend espera que o Backend esteja rodando na porta `5000`. Se o backend falhar ao iniciar, o frontend mostrará uma tela de carregamento infinita ou erro de conexão. Verifique se a porta 5000 não está sendo usada por outro programa.

### Dados Históricos
O backend tenta carregar a base histórica de um arquivo Excel. Se o arquivo `Hackaton_Enter_Base_Candidatos.xlsx` não for encontrado nos caminhos mapeados em `backend/data.py`, o sistema funcionará apenas com os dados mockados de exemplo.
