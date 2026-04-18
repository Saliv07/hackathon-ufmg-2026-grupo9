"""
Orquestrador único — Hackathon UFMG / Enter 2026 · Grupo 9

Comando único, portável para Windows, macOS e Linux:

    python run.py

Responsável por:
1. Verificar pré-requisitos (Python 3.10+, Node 20+)
2. Criar o venv do backend e instalar dependências Python
3. Instalar dependências Node (npm install) e buildar o frontend
4. Gerar os artefatos do monitoramento (parquets) se faltarem
5. Subir o Flask + Dash em http://localhost:5000/

Aborta com mensagem clara quando alguma dependência está faltando.
Ctrl+C para encerrar.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = REPO_ROOT / "backend"
FRONTEND_DIR = REPO_ROOT / "frontend"
DATA_PROCESSED = REPO_ROOT / "data" / "processed"
ARTEFATOS = REPO_ROOT / "artefatos"

BACKEND_VENV = BACKEND_DIR / "venv"
IS_WINDOWS = os.name == "nt"
VENV_PY = BACKEND_VENV / ("Scripts" if IS_WINDOWS else "bin") / ("python.exe" if IS_WINDOWS else "python")


# ─────────────────────────────────────────────────────────────────────────────
# Utilitários de terminal
# ─────────────────────────────────────────────────────────────────────────────
def step(n: int, total: int, title: str) -> None:
    print(f"\n[{n}/{total}] {title}")


def die(msg: str, code: int = 1) -> None:
    print(f"\n✗ ERRO: {msg}\n", file=sys.stderr)
    sys.exit(code)


def run(cmd: list[str], *, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    """Roda um comando e propaga stdout/stderr. Aborta em erro quando check=True."""
    # Resolve 'npm' no Windows, que na verdade é 'npm.cmd', prevenindo FileNotFoundError
    if IS_WINDOWS and cmd[0] == "npm":
        cmd[0] = "npm.cmd"
        
    result = subprocess.run(cmd, cwd=cwd)
    if check and result.returncode != 0:
        die(f"comando falhou: {' '.join(cmd)} (exit {result.returncode})")
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Verificações de pré-requisitos
# ─────────────────────────────────────────────────────────────────────────────
def check_python() -> None:
    major, minor = sys.version_info[:2]
    if (major, minor) < (3, 10):
        die(
            f"Python 3.10+ necessário. Você está usando {major}.{minor}.\n"
            "Instale em https://www.python.org/downloads/"
        )


def check_node() -> None:
    if shutil.which("npm") is None:
        die(
            "Node.js/npm não encontrado no PATH.\n"
            "Instale Node 20.19+ ou 22.12+ em https://nodejs.org/"
        )
    try:
        out = subprocess.run(
            ["node", "--version"], capture_output=True, text=True, check=True
        ).stdout.strip()
        v = out.lstrip("v").split(".")[0]
        if v.isdigit() and int(v) < 20:
            die(
                f"Node {out} detectado. Necessário 20.19+ ou 22.12+.\n"
                "Atualize em https://nodejs.org/"
            )
    except subprocess.CalledProcessError:
        die("Falha ao invocar `node --version`.")


# ─────────────────────────────────────────────────────────────────────────────
# Venv do backend
# ─────────────────────────────────────────────────────────────────────────────
def ensure_backend_venv() -> None:
    if not BACKEND_VENV.exists():
        print(f"  Criando venv em {BACKEND_VENV.relative_to(REPO_ROOT)} ...")
        venv.EnvBuilder(with_pip=True).create(str(BACKEND_VENV))
    if not VENV_PY.exists():
        die(f"venv parece quebrado: {VENV_PY} não existe. Apague `backend/venv` e rode de novo.")


def install_backend_deps() -> None:
    req_file = BACKEND_DIR / "requirements.txt"
    flag_file = BACKEND_VENV / ".reqs_installed"
    
    if flag_file.exists() and flag_file.stat().st_mtime >= req_file.stat().st_mtime:
        print("  Dependências Python atualizadas (venv já instalado). Pulando pip install...")
        return

    print("  Instalando dependências Python (pip install -r backend/requirements.txt) ...")
    run([str(VENV_PY), "-m", "pip", "install", "--quiet", "--upgrade", "pip"])
    run([str(VENV_PY), "-m", "pip", "install", "--quiet", "-r", str(req_file)])
    
    flag_file.touch()


# ─────────────────────────────────────────────────────────────────────────────
# Frontend
# ─────────────────────────────────────────────────────────────────────────────
def install_frontend_deps() -> None:
    node_modules = FRONTEND_DIR / "node_modules"
    if node_modules.exists():
        print("  node_modules já existe — pulando npm install (apague a pasta para forçar).")
        return
    print("  Instalando dependências Node (npm install) ...")
    run(["npm", "install", "--silent"], cwd=FRONTEND_DIR)


def build_frontend() -> None:
    print("  Buildando frontend (npm run build) ...")
    run(["npm", "run", "build"], cwd=FRONTEND_DIR)


# ─────────────────────────────────────────────────────────────────────────────
# Artefatos do monitoramento
# ─────────────────────────────────────────────────────────────────────────────
def ensure_monitoring_artefacts() -> None:
    casos_60k = DATA_PROCESSED / "casos_60k.parquet"
    casos_enr = DATA_PROCESSED / "casos_enriquecidos.parquet"

    if casos_60k.exists() and casos_enr.exists():
        print("  Parquets do monitoramento já existem — pulando geração.")
        return

    print("  Gerando artefatos do monitoramento (pode levar ~20s) ...")
    run([str(VENV_PY), "-m", "src.monitor.load_data"], cwd=REPO_ROOT)
    run([str(VENV_PY), "-m", "src.monitor.baseline"], cwd=REPO_ROOT)
    run([str(VENV_PY), "-m", "src.monitor.gerar_sintetico"], cwd=REPO_ROOT)

    if (ARTEFATOS / "modelo_xgboost.pkl").exists():
        print("  Gerando política XGBoost (politica_output.csv) ...")
        # Falha graciosamente — monitoramento cai no mock
        run(
            [str(VENV_PY), "-m", "src.monitor.politica_xgboost"],
            cwd=REPO_ROOT,
            check=False,
        )
    else:
        print(
            "  (Modelo XGBoost não encontrado em ./artefatos/.\n"
            "   Para baixar: git checkout origin/master -- artefatos/\n"
            "   Sem ele o monitoramento usa política mock.)"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Servidor
# ─────────────────────────────────────────────────────────────────────────────
def run_server() -> None:
    print(
        "\n=================================================="
        "\n  Acesse:   http://localhost:5000/"
        "\n  API:      http://localhost:5000/api/"
        "\n  Monitor:  http://localhost:5000/monitoramento/"
        "\n==================================================\n"
    )
    try:
        # Foreground: Ctrl+C encerra
        subprocess.run([str(VENV_PY), "main.py"], cwd=BACKEND_DIR, check=False)
    except KeyboardInterrupt:
        print("\n  Encerrando...")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    print("==================================================")
    print(" Plataforma Jurídica · Grupo 9 (Hackathon UFMG 2026)")
    print("==================================================")

    step(1, 4, "Verificando pré-requisitos")
    check_python()
    check_node()
    print(f"  Python {sys.version.split()[0]} OK")
    print("  Node/npm OK")

    step(2, 4, "Preparando backend (venv + pip)")
    ensure_backend_venv()
    install_backend_deps()

    step(3, 4, "Preparando frontend (npm + build)")
    install_frontend_deps()
    build_frontend()

    step(4, 4, "Artefatos do monitoramento e servidor")
    ensure_monitoring_artefacts()
    run_server()


if __name__ == "__main__":
    main()
