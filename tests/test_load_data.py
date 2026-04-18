"""Testes para load_data.py — smoke + propriedades do Conjunto A."""
import pandas as pd
import pytest

from src.monitor.load_data import SUBS_COLS


EXPECTED_COLS = {
    "numero_processo", "uf", "assunto", "sub_assunto",
    "resultado_macro", "resultado_micro",
    "valor_causa", "valor_condenacao",
    "subs_contrato", "subs_extrato", "subs_comprovante",
    "subs_dossie", "subs_demonstrativo", "subs_laudo",
    "subs_total", "faixa_valor", "faixa_completude",
}


class TestSmoke:
    def test_parquet_existe_e_carrega(self, casos_60k):
        assert isinstance(casos_60k, pd.DataFrame)
        assert len(casos_60k) > 0

    def test_shape_60k(self, casos_60k):
        assert len(casos_60k) == 60_000

    def test_colunas_esperadas(self, casos_60k):
        assert EXPECTED_COLS <= set(casos_60k.columns)


class TestIntegridade:
    def test_numero_processo_unico(self, casos_60k):
        assert casos_60k["numero_processo"].is_unique

    def test_sem_nan_em_campos_criticos(self, casos_60k):
        criticos = ["numero_processo", "uf", "resultado_macro",
                    "valor_causa", "valor_condenacao"]
        for c in criticos:
            assert casos_60k[c].notna().all(), f"NaN em {c}"

    def test_resultado_macro_apenas_duas_categorias(self, casos_60k):
        assert set(casos_60k["resultado_macro"].unique()) <= {"Êxito", "Não Êxito"}

    def test_subsidios_sao_binarios(self, casos_60k):
        for c in SUBS_COLS:
            uniques = set(casos_60k[c].unique())
            assert uniques <= {0, 1}, f"{c} tem valores não-binários: {uniques}"

    def test_subs_total_coerente(self, casos_60k):
        """subs_total deve ser a soma exata das 6 colunas binárias, entre 0 e 6."""
        calc = casos_60k[SUBS_COLS].sum(axis=1)
        assert (casos_60k["subs_total"] == calc).all()
        assert casos_60k["subs_total"].between(0, 6).all()


class TestPropriedades:
    """Propriedades dos dados que, se quebradas, indicam regressão no baseline."""

    def test_taxa_exito_macro_proxima_de_70pct(self, casos_60k):
        taxa = (casos_60k["resultado_macro"] == "Êxito").mean()
        assert 0.68 <= taxa <= 0.72, f"taxa êxito fora do esperado: {taxa:.4f}"

    def test_distribuicao_completude_bate_com_guia(self, casos_60k):
        """Números exatos do baseline do guia — regression guard."""
        esperado = {0: 57, 1: 745, 2: 3498, 3: 8811, 4: 15719, 5: 19518, 6: 11652}
        obtido = casos_60k["subs_total"].value_counts().sort_index().to_dict()
        assert obtido == esperado

    def test_faixa_valor_tem_tres_categorias(self, casos_60k):
        cats = set(casos_60k["faixa_valor"].cat.categories)
        assert cats == {"Baixo", "Médio", "Alto"}

    def test_faixa_completude_tem_tres_categorias(self, casos_60k):
        cats = set(casos_60k["faixa_completude"].cat.categories)
        assert cats == {"Frágil", "Parcial", "Sólida"}

    def test_valor_causa_positivo(self, casos_60k):
        assert (casos_60k["valor_causa"] > 0).all()

    def test_valor_condenacao_nao_negativo(self, casos_60k):
        assert (casos_60k["valor_condenacao"] >= 0).all()
