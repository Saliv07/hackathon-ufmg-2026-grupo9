"""Caminhos canônicos do projeto. Todos os scripts do monitor importam daqui."""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

DATA_RAW = REPO_ROOT / "data" / "raw"
DATA_PROCESSED = REPO_ROOT / "data" / "processed"

XLSX_BASE = DATA_RAW / "Hackaton_Enter_Base_Candidatos.xlsx"

CASOS_60K = DATA_PROCESSED / "casos_60k.parquet"
CASOS_ENRIQUECIDOS = DATA_PROCESSED / "casos_enriquecidos.parquet"
BASELINE_JSON = DATA_PROCESSED / "baseline.json"

POLITICA_OUTPUT = DATA_PROCESSED / "politica_output.csv"
