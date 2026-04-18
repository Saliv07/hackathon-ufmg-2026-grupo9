"""
Testes do motor contrafactual e das métricas de efetividade.

Três camadas:
- Smoke (casos_60k)       — as funções rodam e retornam estrutura esperada
- Propriedades (casos_60k)— invariantes matemáticos do contrafactual
- Unitários (df_mini)     — casos de borda e determinismo
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from src.monitor import counterfactual, metrics_effectiveness as mx


SIM_KEYS = {
    "custo_observado_total",
    "custo_politica_total",
    "economia_total",
    "economia_percentual",
    "economia_por_caso",
    "n_casos",
    "prob_aceita_assumida",
}


# ---------- Smoke (casos_60k) ----------

class TestSmokeCasos60k:
    def test_aplicar_politica_mock_adiciona_colunas(self, casos_60k):
        out = counterfactual.aplicar_politica_mock(casos_60k)
        assert "acao_recomendada_mock" in out.columns
        assert "valor_acordo_recomendado_mock" in out.columns
        # valores válidos
        assert set(out["acao_recomendada_mock"].unique()).issubset({"acordo", "defesa"})
        assert (out["valor_acordo_recomendado_mock"] >= 0).all()

    def test_simular_politica_retorna_chaves_esperadas(self, casos_60k):
        df = counterfactual.aplicar_politica_mock(casos_60k)
        sim = counterfactual.simular_politica(df)
        assert set(sim.keys()) == SIM_KEYS
        assert sim["n_casos"] == len(casos_60k)

    def test_valores_numericos_finitos(self, casos_60k):
        df = counterfactual.aplicar_politica_mock(casos_60k)
        sim = counterfactual.simular_politica(df)
        for k in [
            "custo_observado_total", "custo_politica_total",
            "economia_total", "economia_percentual", "economia_por_caso",
        ]:
            assert math.isfinite(sim[k]), f"{k} não finito: {sim[k]}"


# ---------- Propriedades do contrafactual ----------

class TestPropriedadesContrafactual:
    def test_economia_monotonica_em_prob_aceita(self, casos_60k):
        df = counterfactual.aplicar_politica_mock(casos_60k)
        sens = counterfactual.simular_sensibilidade(df, probs=[0.3, 0.5, 0.7, 0.9])
        economias = sens["economia_total"].to_numpy()
        # Monotonicamente crescente
        assert np.all(np.diff(economias) > 0), f"Não monotônica: {economias}"

    def test_extremos_probabilidade(self, casos_60k):
        df = counterfactual.aplicar_politica_mock(casos_60k)
        sens = counterfactual.simular_sensibilidade(df, probs=[0.0, 0.5, 1.0])
        econ = sens.set_index("prob_aceita_assumida")["economia_total"]
        # p=1 é máxima, p=0 é mínima
        assert econ.loc[1.0] >= econ.loc[0.5] >= econ.loc[0.0]
        # Em p=0, para casos em que acao==acordo, custo = valor_condenacao
        # (igual ao observado) -> economia_total == 0 exatamente
        assert abs(econ.loc[0.0]) < 1e-6

    def test_consistencia_economia(self, casos_60k):
        df = counterfactual.aplicar_politica_mock(casos_60k)
        sim = counterfactual.simular_politica(df, prob_aceita=0.7)
        assert math.isclose(
            sim["economia_total"],
            sim["custo_observado_total"] - sim["custo_politica_total"],
            rel_tol=1e-9,
        )

    def test_custo_observado_bate_baseline(self, casos_60k, baseline):
        df = counterfactual.aplicar_politica_mock(casos_60k)
        sim = counterfactual.simular_politica(df)
        baseline_total = baseline["financeiro"]["custo_total_estimado"]
        assert math.isclose(
            sim["custo_observado_total"], baseline_total, rel_tol=1e-3
        ), f"{sim['custo_observado_total']} vs baseline {baseline_total}"

    def test_mock_recomenda_acordo_so_para_subs_total_baixo(self, casos_60k):
        df = counterfactual.aplicar_politica_mock(casos_60k)
        mask_acordo = df["acao_recomendada_mock"] == "acordo"
        assert (df.loc[mask_acordo, "subs_total"] <= 3).all()
        # E o complemento: subs_total > 3 sempre recomenda defesa
        mask_defesa = df["acao_recomendada_mock"] == "defesa"
        assert (df.loc[mask_defesa, "subs_total"] > 3).all()


# ---------- Unitários (df_mini) ----------

class TestUnitariosDfMini:
    def test_aplicar_politica_mock_df_mini(self, df_mini):
        out = counterfactual.aplicar_politica_mock(df_mini)
        assert "acao_recomendada_mock" in out.columns
        assert "valor_acordo_recomendado_mock" in out.columns
        assert len(out) == len(df_mini)

    def test_simular_politica_deterministico(self, df_mini):
        df = counterfactual.aplicar_politica_mock(df_mini)
        a = counterfactual.simular_politica(df, prob_aceita=0.7)
        b = counterfactual.simular_politica(df, prob_aceita=0.7)
        assert a == b

    def test_todos_subs_total_altos_economia_zero(self, df_mini):
        # Força subs_total > 3 em todos os casos -> mock recomenda defesa -> economia = 0
        df = df_mini.copy()
        df["subs_total"] = 5
        df = counterfactual.aplicar_politica_mock(df)
        assert (df["acao_recomendada_mock"] == "defesa").all()
        sim = counterfactual.simular_politica(df, prob_aceita=0.7)
        assert math.isclose(sim["economia_total"], 0.0, abs_tol=1e-9)
        assert math.isclose(
            sim["custo_politica_total"], sim["custo_observado_total"], rel_tol=1e-9
        )

    def test_df_vazio_sem_zerodiv(self):
        df_empty = pd.DataFrame({
            "numero_processo": [],
            "valor_causa": [],
            "valor_condenacao": [],
            "subs_total": [],
            "resultado_macro": [],
            "resultado_micro": [],
            "faixa_completude": [],
        })
        df_empty = counterfactual.aplicar_politica_mock(df_empty)
        sim = counterfactual.simular_politica(df_empty)
        assert sim["n_casos"] == 0
        assert sim["economia_total"] == 0.0
        assert sim["economia_percentual"] == 0.0
        assert sim["economia_por_caso"] == 0.0

    def test_custo_caso_sob_politica_formula(self, df_mini):
        df = counterfactual.aplicar_politica_mock(df_mini)
        p = 0.6
        custo = counterfactual.custo_caso_sob_politica(df, prob_aceita=p)
        # Recalcula manualmente em numpy
        is_acordo = (df["acao_recomendada_mock"] == "acordo").to_numpy()
        esperado = np.where(
            is_acordo,
            p * df["valor_acordo_recomendado_mock"].to_numpy()
            + (1 - p) * df["valor_condenacao"].to_numpy(),
            df["valor_condenacao"].to_numpy(),
        )
        np.testing.assert_allclose(custo.to_numpy(), esperado, rtol=1e-12)


# ---------- Métricas de efetividade (uso leve) ----------

class TestMetricasEfetividade:
    def test_economia_total_vs_baseline(self, casos_60k, baseline):
        df = counterfactual.aplicar_politica_mock(casos_60k)
        out = mx.economia_total_vs_baseline(df, baseline)
        assert out["economia_total"] > 0
        assert 0 < out["economia_percentual"] < 1

    def test_custo_medio_por_caso(self, casos_60k):
        df = counterfactual.aplicar_politica_mock(casos_60k)
        v = mx.custo_medio_por_caso_politica(df)
        assert v > 0 and math.isfinite(v)

    def test_taxa_aceitacao_fallback_H1(self, casos_60k):
        out = mx.taxa_aceitacao_acordo(casos_60k)
        assert out["fonte"] == "assumida_H1"
        assert out["taxa_aceitacao"] == 0.40

    def test_redistribuicao_resultado_micro(self, casos_60k, baseline):
        df = counterfactual.aplicar_politica_mock(casos_60k)
        out = mx.redistribuicao_resultado_micro(df, baseline)
        # Acordo sobe (mais acordos na política)
        acordo_row = out.loc[out["resultado_micro"] == "Acordo"].iloc[0]
        assert acordo_row["delta_pp"] > 0
        # As probabilidades antes somam ~1 e depois também
        assert math.isclose(out["antes_pct"].sum(), 1.0, abs_tol=1e-6)
        assert math.isclose(out["depois_pct"].sum(), 1.0, abs_tol=1e-6)

    def test_custo_por_faixa_completude(self, casos_60k):
        df = counterfactual.aplicar_politica_mock(casos_60k)
        g = mx.custo_por_faixa_completude(df)
        assert {"faixa_completude", "n_casos", "custo_observado", "custo_politica", "economia"} <= set(g.columns)
        # Faixa Sólida (subs_total >= 5) deveria ter economia 0 (só defesa)
        solida = g.loc[g["faixa_completude"] == "Sólida"]
        if not solida.empty:
            assert math.isclose(float(solida["economia"].iloc[0]), 0.0, abs_tol=1e-6)

    def test_recall_alta_perda(self, casos_60k):
        df = counterfactual.aplicar_politica_mock(casos_60k)
        out = mx.recall_alta_perda(df)
        assert 0.0 <= out["recall"] <= 1.0
        assert out["n_alta_perda"] > 0

    def test_precision_defesa(self, casos_60k):
        df = counterfactual.aplicar_politica_mock(casos_60k)
        out = mx.precision_defesa(df)
        assert 0.0 <= out["precision"] <= 1.0

    def test_economia_acumulada_temporal(self, casos_60k):
        df = counterfactual.aplicar_politica_mock(casos_60k)
        out = mx.economia_acumulada_temporal(df, n_meses=6, seed=42)
        assert "mes" in out.columns and "economia_acumulada" in out.columns
        # cumulativa é não-decrescente quando economia mensal >= 0
        assert out["economia_acumulada"].is_monotonic_increasing

    def test_distribuicao_valores_acordo(self, casos_60k):
        df = counterfactual.aplicar_politica_mock(casos_60k)
        out = mx.distribuicao_valores_acordo(df)
        assert out["n"] > 0
        assert out["min"] <= out["median"] <= out["max"]
