"""Testes para baseline.py — números de referência não podem drifar silenciosamente."""
import pytest


class TestEstruturaBaseline:
    def test_chaves_principais(self, baseline):
        assert {"volumetria", "financeiro", "completude_vs_exito",
                "sub_assunto", "por_uf"} <= set(baseline.keys())

    def test_volumetria_tem_campos_esperados(self, baseline):
        vol = baseline["volumetria"]
        assert {"total_casos", "taxa_exito_macro", "taxa_nao_exito_macro",
                "dist_resultado_micro"} <= set(vol.keys())

    def test_financeiro_tem_campos_esperados(self, baseline):
        fin = baseline["financeiro"]
        assert {"valor_causa_medio", "condenacao_media_geral",
                "custo_total_estimado"} <= set(fin.keys())


class TestNumerosCentrais:
    """Valores do baseline do guia — se qualquer um drifar, alguma coisa mudou nos dados."""

    def test_total_casos(self, baseline):
        assert baseline["volumetria"]["total_casos"] == 60_000

    def test_taxa_exito_macro_69_56pct(self, baseline):
        taxa = baseline["volumetria"]["taxa_exito_macro"]
        assert abs(taxa - 0.6956) < 0.001, f"taxa êxito drift: {taxa:.4f}"

    def test_taxas_somam_100pct(self, baseline):
        vol = baseline["volumetria"]
        assert abs(vol["taxa_exito_macro"] + vol["taxa_nao_exito_macro"] - 1.0) < 1e-6

    def test_valor_causa_medio_aproximado(self, baseline):
        v = baseline["financeiro"]["valor_causa_medio"]
        assert 14_500 < v < 15_500, f"valor_causa_medio drift: {v:.2f}"

    def test_condenacao_media_aproximada(self, baseline):
        v = baseline["financeiro"]["condenacao_media_geral"]
        assert 3_000 < v < 3_500, f"condenacao_media drift: {v:.2f}"

    def test_custo_total_estimado_aproximado(self, baseline):
        v = baseline["financeiro"]["custo_total_estimado"]
        assert 190e6 < v < 196e6, f"custo_total drift: {v:,.2f}"

    def test_percentual_acordo_historico_baixo(self, baseline):
        """Política implícita atual é 'defender sempre'. Acordo < 1%."""
        pct = baseline["volumetria"]["dist_resultado_micro"].get("Acordo", 0)
        assert pct < 0.01

    def test_distribuicao_resultado_micro_soma_1(self, baseline):
        total = sum(baseline["volumetria"]["dist_resultado_micro"].values())
        assert abs(total - 1.0) < 1e-6


class TestCompletudeVsExito:
    """Insight central do projeto: transição crítica em 3 subsídios."""

    def test_taxa_exito_cresce_com_subsidios(self, baseline):
        comp = baseline["completude_vs_exito"]
        taxas = [comp[str(k)]["taxa_exito"] for k in range(7)]
        # Monotonicidade não-estrita: taxa nunca cai ao adicionar subsídio
        for i in range(1, 7):
            assert taxas[i] >= taxas[i-1] - 0.02, (
                f"Quebra de monotonicidade em subs={i}: {taxas[i-1]:.3f} → {taxas[i]:.3f}"
            )

    def test_taxa_exito_frageis_baixa(self, baseline):
        """Com 0-2 subsídios, banco tem muita dificuldade."""
        comp = baseline["completude_vs_exito"]
        taxa_2 = comp["2"]["taxa_exito"]
        assert taxa_2 < 0.20

    def test_taxa_exito_solidos_alta(self, baseline):
        """Com 5-6 subsídios, banco ganha na grande maioria."""
        comp = baseline["completude_vs_exito"]
        taxa_5 = comp["5"]["taxa_exito"]
        assert taxa_5 > 0.80
