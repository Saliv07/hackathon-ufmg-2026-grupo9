"""
Orquestrador único — Hackathon UFMG / Enter 2026 · Grupo 9

Comando único, portável para Windows, macOS e Linux:

    python run.py

Responsável por:
1. Verificar pré-requisitos (Python 3.10+, Node 20+)
2. Criar o venv do backend e instalar dependências Python
3. Instalar dependências Node (npm install) e buildar o frontend
4. Gerar os artefatos do monitoramento (parquets) se faltarem
5. Detectar uma porta livre (mac tem AirPlay na 5000) e subir o
   Flask + Dash em http://localhost:<porta>/

Aborta com mensagem clara quando alguma dependência está faltando.
Ctrl+C para encerrar.

Pode forçar uma porta específica via env:
    PORT=8000 python run.py
"""
from __future__ import annotations

import os
import shutil
import socket
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
# Detecção de porta livre (mac tem AirPlay Receiver na 5000)
# ─────────────────────────────────────────────────────────────────────────────
PORT_CANDIDATES = (5000, 5001, 5050, 5080, 8000, 8080, 8081, 3000)


def _is_port_free(port: int, host: str = "127.0.0.1") -> bool:
    """True se consegue bindar a porta (0.0.0.0 e 127.0.0.1)."""
    for h in (host, "0.0.0.0"):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((h, port))
        except OSError:
            s.close()
            return False
        s.close()
    return True


def resolve_port() -> int:
    """Escolhe a porta a usar. Ordem:
    1. Se PORT env var está setada, usa ela (ou aborta se ocupada).
    2. Tenta 5000 (padrão). Se ocupada (ex: AirPlay no mac), tenta 5001, 5050, 5080, 8000, 8080, 8081, 3000.
    3. Aborta se nenhuma dessas estiver livre.
    """
    forced = os.getenv("PORT")
    if forced:
        try:
            p = int(forced)
        except ValueError:
            die(f"PORT='{forced}' não é um inteiro válido.")
        if not _is_port_free(p):
            die(
                f"Porta {p} (forçada via env PORT) já está em uso.\n"
                "Libere-a ou escolha outra: PORT=8000 python run.py"
            )
        return p

    for p in PORT_CANDIDATES:
        if _is_port_free(p):
            return p
    die(
        "Nenhuma porta livre encontrada em "
        f"{PORT_CANDIDATES}.\n"
        "Libere uma delas ou force via: PORT=9000 python run.py"
    )
    return 0  # unreachable, mas satisfaz o type checker


# ─────────────────────────────────────────────────────────────────────────────
# Servidor
# ─────────────────────────────────────────────────────────────────────────────
def run_server(port: int) -> None:
    print(
        f"\n=================================================="
        f"\n  Acesse:   http://localhost:{port}/"
        f"\n  API:      http://localhost:{port}/api/"
        f"\n  Monitor:  http://localhost:{port}/monitoramento/"
        f"\n==================================================\n"
    )
    if port != 5000:
        print(
            f"  (porta {port} escolhida automaticamente — "
            "a 5000 está em uso, típico em Mac com AirPlay Receiver)\n"
        )
    env = os.environ.copy()
    env["PORT"] = str(port)
    try:
        # Foreground: Ctrl+C encerra
        subprocess.run([str(VENV_PY), "main.py"], cwd=BACKEND_DIR, check=False, env=env)
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
    port = resolve_port()
    run_server(port)


if __name__ == "__main__":
    main()
