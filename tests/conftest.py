"""
Fixtures compartilhadas entre os testes da frente de monitoramento.

Estratégia:
- `casos_60k` e `casos_enriquecidos` são fixtures de módulo (carregam uma vez por sessão de testes)
- Fixtures pequenas e sintéticas para testes de unidade que não precisam dos 60k reais
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PROCESSED = REPO_ROOT / "data" / "processed"


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def casos_60k_path() -> Path:
    return PROCESSED / "casos_60k.parquet"


@pytest.fixture(scope="session")
def baseline_path() -> Path:
    return PROCESSED / "baseline.json"


@pytest.fixture(scope="session")
def casos_enriquecidos_path() -> Path:
    return PROCESSED / "casos_enriquecidos.parquet"


@pytest.fixture(scope="session")
def casos_60k(casos_60k_path) -> pd.DataFrame:
    if not casos_60k_path.exists():
        pytest.skip(f"Arquivo não gerado ainda: {casos_60k_path}")
    return pd.read_parquet(casos_60k_path)


@pytest.fixture(scope="session")
def baseline(baseline_path) -> dict:
    if not baseline_path.exists():
        pytest.skip(f"Arquivo não gerado ainda: {baseline_path}")
    return json.loads(baseline_path.read_text())


@pytest.fixture(scope="session")
def casos_enriquecidos(casos_enriquecidos_path) -> pd.DataFrame:
    if not casos_enriquecidos_path.exists():
        pytest.skip(f"Arquivo não gerado ainda: {casos_enriquecidos_path}")
    return pd.read_parquet(casos_enriquecidos_path)


@pytest.fixture
def df_mini() -> pd.DataFrame:
    """DataFrame sintético pequeno para testes unitários de métricas."""
    rng = np.random.default_rng(seed=123)
    n = 200
    return pd.DataFrame({
        "numero_processo": [f"P{i:06d}" for i in range(n)],
        "uf": rng.choice(["SP", "MG", "RJ", "BA"], size=n),
        "assunto": ["Contratos de Consumo"] * n,
        "sub_assunto": rng.choice(["Genérico", "Golpe"], size=n, p=[0.7, 0.3]),
        "resultado_macro": rng.choice(["Êxito", "Não Êxito"], size=n, p=[0.7, 0.3]),
        "resultado_micro": rng.choice(
            ["Improcedência", "Extinção", "Parcial procedência", "Procedência", "Acordo"],
            size=n,
            p=[0.46, 0.23, 0.20, 0.10, 0.01],
        ),
        "valor_causa": rng.uniform(1000, 50000, size=n).round(2),
        "valor_condenacao": rng.uniform(0, 20000, size=n).round(2),
        "subs_contrato": rng.integers(0, 2, size=n),
        "subs_extrato": rng.integers(0, 2, size=n),
        "subs_comprovante": rng.integers(0, 2, size=n),
        "subs_dossie": rng.integers(0, 2, size=n),
        "subs_demonstrativo": rng.integers(0, 2, size=n),
        "subs_laudo": rng.integers(0, 2, size=n),
    }).assign(
        subs_total=lambda d: d[[c for c in d.columns if c.startswith("subs_")]].sum(axis=1),
        faixa_valor=lambda d: pd.cut(
            d["valor_causa"],
            bins=[0, 5000, 15000, float("inf")],
            labels=["Baixo", "Médio", "Alto"],
        ),
        faixa_completude=lambda d: pd.cut(
            d["subs_total"],
            bins=[-1, 2, 4, 6],
            labels=["Frágil", "Parcial", "Sólida"],
        ),
    )
