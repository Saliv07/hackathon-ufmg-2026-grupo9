"""
Testes da frente de monitoramento de aderência.

Três níveis:
1. Smoke do parquet enriquecido
2. Propriedades do gerador sintético (vieses esperados)
3. Unitários das métricas via fixture mini local
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.monitor import metrics_adherence as ma


COLS_ADERENCIA = [
    "advogado_id", "escritorio_id", "regiao", "aderencia_esperada",
    "data_distribuicao", "data_decisao", "tempo_decisao_min",
    "acao_recomendada", "valor_acordo_recomendado",
    "acao_tomada", "aderente", "razao_override",
    "valor_acordo_proposto", "resultado_negociacao",
]

CAMPOS_CRITICOS = ["advogado_id", "escritorio_id", "acao_tomada", "aderente"]


# ==================== 1. Smoke ====================

class TestSmoke:
    def test_arquivo_existe(self, casos_enriquecidos_path):
        assert casos_enriquecidos_path.exists()

    def test_shape(self, casos_enriquecidos):
        assert casos_enriquecidos.shape[0] == 60_000
        assert casos_enriquecidos.shape[1] >= 25

    def test_colunas_novas_presentes(self, casos_enriquecidos):
        faltando = set(COLS_ADERENCIA) - set(casos_enriquecidos.columns)
        assert not faltando, f"Colunas ausentes: {faltando}"

    def test_sem_nan_em_campos_criticos(self, casos_enriquecidos):
        nulos = casos_enriquecidos[CAMPOS_CRITICOS].isna().sum()
        assert (nulos == 0).all(), f"NaNs encontrados: {nulos.to_dict()}"


# ==================== 2. Propriedades do gerador ====================

class TestPropriedadesGerador:
    def test_taxa_aderencia_global_em_faixa(self, casos_enriquecidos):
        taxa = casos_enriquecidos["aderente"].mean()
        assert 0.75 <= taxa <= 0.85, f"Taxa global fora de [0.75, 0.85]: {taxa:.3f}"

    def test_variacao_entre_escritorios(self, casos_enriquecidos):
        por_esc = casos_enriquecidos.groupby("escritorio_id")["aderente"].mean()
        spread = por_esc.max() - por_esc.min()
        assert spread > 0.15, f"Spread entre escritórios muito baixo: {spread:.3f}"

    def test_razao_override_mais_frequente(self, casos_enriquecidos):
        dist = ma.distribuicao_razoes_override(casos_enriquecidos)
        assert dist.index[0] == "discordancia_score"

    def test_aderente_binario(self, casos_enriquecidos):
        assert set(casos_enriquecidos["aderente"].unique()).issubset({0, 1})

    def test_razao_override_somente_quando_nao_aderente(self, casos_enriquecidos):
        aderentes = casos_enriquecidos[casos_enriquecidos["aderente"] == 1]
        nao_aderentes = casos_enriquecidos[casos_enriquecidos["aderente"] == 0]
        assert aderentes["razao_override"].isna().all()
        assert nao_aderentes["razao_override"].notna().all()

    def test_data_decisao_nao_futura(self, casos_enriquecidos):
        limite = pd.Timestamp("2026-03-31")
        assert (casos_enriquecidos["data_decisao"] <= limite + pd.Timedelta(days=1)).all()

    def test_todas_combinacoes_presentes(self, casos_enriquecidos):
        combos = (
            casos_enriquecidos
            .groupby(["acao_recomendada", "acao_tomada", "aderente"])
            .size()
        )
        esperadas = {
            ("acordo", "acordo", 1),
            ("acordo", "defesa", 0),
            ("defesa", "defesa", 1),
            ("defesa", "acordo", 0),
        }
        faltando = esperadas - set(combos.index)
        assert not faltando, f"Combinações faltando: {faltando}"


# ==================== 3. Unitários das métricas ====================

@pytest.fixture
def df_mini_ader(df_mini) -> pd.DataFrame:
    """df_mini enriquecido com colunas sintéticas de aderência."""
    rng = np.random.default_rng(seed=7)
    n = len(df_mini)
    df = df_mini.copy()
    df["advogado_id"] = rng.choice([f"ADV{i:03d}" for i in range(1, 11)], size=n)
    df["escritorio_id"] = rng.choice([f"ESC{i:02d}" for i in range(1, 4)], size=n)
    df["acao_recomendada"] = np.where(df["subs_total"] <= 3, "acordo", "defesa")
    segue = rng.random(n) < 0.78
    acao_inversa = np.where(df["acao_recomendada"] == "acordo", "defesa", "acordo")
    df["acao_tomada"] = np.where(segue, df["acao_recomendada"], acao_inversa)
    df["aderente"] = (df["acao_tomada"] == df["acao_recomendada"]).astype("int8")
    return df


class TestMetricas:
    def test_taxa_seguimento_em_unit_interval(self, df_mini_ader):
        v = ma.taxa_seguimento_global(df_mini_ader)
        assert 0.0 <= v <= 1.0

    def test_taxa_override_complementa_seguimento(self, df_mini_ader):
        tsg = ma.taxa_seguimento_global(df_mini_ader)
        tov = ma.taxa_override(df_mini_ader)
        assert tsg + tov == pytest.approx(1.0)

    def test_aderencia_ponderada_em_unit_interval(self, df_mini_ader):
        v = ma.aderencia_ponderada_por_valor(df_mini_ader)
        assert 0.0 <= v <= 1.0

    def test_alertas_retorna_lista(self, df_mini_ader):
        alertas = ma.alertas_ativos(df_mini_ader)
        assert isinstance(alertas, list)
