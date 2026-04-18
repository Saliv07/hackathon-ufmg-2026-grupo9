"""
Dashboard de Monitoramento — Política de Acordos · Banco UFMG
Requisitos 4 (Aderência) e 5 (Efetividade) do Hackathon UFMG / Enter 2026.

Frente: monitoramento (Matheus / Nekark Data Intelligence).
Branch: vilas.

Este arquivo implementa:
    - Aba "Visão Geral"  -> completa, alimentada pelo baseline.json + casos_60k.
                             Usa baseline imutável; NÃO é afetada por filtros globais.
    - Aba "Aderência"    -> KPIs A01/A02/A20 + drift temporal A18, razões A13,
                             rankings A05/A06, segmentação A08/A04, painel de alertas.
    - Aba "Efetividade"  -> Potencial vs Realizada vs Gap + sensibilidade +
                             redistribuição E05 + E09 temporal + E06 por completude.

Filtros globais (sidebar): UF, escritório, sub-assunto e período aplicam-se a
Aderência e Efetividade (Visão Geral permanece ancorada ao baseline).

Integração com outras frentes:
    - Quando `data/processed/politica_output.csv` (output do XGBoost) existir,
      `get_df_com_politica()` faz merge automático. Enquanto não existe, mock
      (H2 + H3 do DECISOES.md) já está materializado em casos_enriquecidos.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime
from pathlib import Path

# Garante que o repo root está no sys.path quando este arquivo é invocado
# diretamente pelo `streamlit run` (que não adiciona o root automaticamente).
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.monitor import counterfactual, metrics_adherence, metrics_effectiveness
from src.monitor.paths import (
    BASELINE_JSON,
    CASOS_60K,
    CASOS_ENRIQUECIDOS,
    DATA_PROCESSED,
)


# ============================================================
# Configuração global
# ============================================================
st.set_page_config(
    page_title="Monitoramento UFMG",
    layout="wide",
    page_icon="⚖️",
)

# Paleta institucional (banco + justiça). Evita vermelho puro em KPIs
# para não alarmar visualmente antes do contexto ser lido.
COR_PRIMARIA = "#1F4E79"
COR_SECUNDARIA = "#4A90C2"
COR_DESTAQUE = "#E8A33D"
COR_ALERTA = "#C0392B"
COR_NEUTRO = "#7F8C8D"
COR_OK = "#27AE60"

# Thresholds de severidade para A06 (aderência por escritório) — alinhados
# com os alertas P0 definidos em metrics_adherence.alertas_ativos.
TH_ADESAO_OK = 0.85
TH_ADESAO_ALERTA = 0.70


# ============================================================
# Helpers de formatação
# ============================================================
def fmt_brl(valor: float, casas: int = 2) -> str:
    """Formata número como R$ brasileiro: milhar com '.', decimal com ','."""
    if valor is None or (isinstance(valor, float) and np.isnan(valor)):
        return "—"
    sinal = "-" if valor < 0 else ""
    valor = abs(valor)
    txt = f"{valor:,.{casas}f}"
    # troca separadores: 1,234,567.89 -> 1.234.567,89
    txt = txt.replace(",", "§").replace(".", ",").replace("§", ".")
    return f"{sinal}R$ {txt}"


def fmt_brl_curto(valor: float) -> str:
    """R$ em milhões (1 casa). Usado em KPIs grandes."""
    if valor is None or (isinstance(valor, float) and np.isnan(valor)):
        return "—"
    sinal = "-" if valor < 0 else ""
    v = abs(valor)
    if v >= 1e9:
        return f"{sinal}R$ {v/1e9:.2f}B".replace(".", ",")
    if v >= 1e6:
        return f"{sinal}R$ {v/1e6:.1f}M".replace(".", ",")
    if v >= 1e3:
        return f"{sinal}R$ {v/1e3:.0f}K".replace(".", ",")
    return fmt_brl(valor, casas=0)


def fmt_int_br(valor: int) -> str:
    return f"{int(valor):,}".replace(",", ".")


def fmt_pct(valor: float, casas: int = 1) -> str:
    if valor is None or (isinstance(valor, float) and np.isnan(valor)):
        return "—"
    return f"{valor*100:.{casas}f}%".replace(".", ",")


# ============================================================
# Carregamento (cacheado)
# ============================================================
@st.cache_data(show_spinner=False)
def load_baseline() -> dict:
    with open(BASELINE_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def load_casos() -> pd.DataFrame:
    return pd.read_parquet(CASOS_60K)


@st.cache_data(show_spinner=False)
def load_enriquecidos() -> pd.DataFrame | None:
    path = Path(CASOS_ENRIQUECIDOS)
    if not path.exists():
        return None
    return pd.read_parquet(path)


@st.cache_data(show_spinner=False)
def baseline_mtime_iso() -> str:
    try:
        ts = Path(BASELINE_JSON).stat().st_mtime
        return datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M")
    except OSError:
        return "—"


@st.cache_data(show_spinner=False)
def get_df_com_politica() -> tuple[pd.DataFrame | None, str]:
    """Aplica a política ao casos_enriquecidos. Mock hoje; CSV real quando existir.

    Retorna (df, fonte) onde fonte ∈ {"csv", "mock", "indisponivel"}.
    """
    df_enr = load_enriquecidos()
    if df_enr is None:
        return None, "indisponivel"
    csv_path = DATA_PROCESSED / "politica_output.csv"
    if csv_path.exists():
        politica = pd.read_csv(csv_path)
        merged = df_enr.merge(politica, on="numero_processo", how="left")
        return merged, "csv"
    # Fallback: mock já está nas colunas acao_recomendada e valor_acordo_recomendado
    return df_enr, "mock"


# ============================================================
# Filtros globais
# ============================================================
def aplicar_filtros(
    df: pd.DataFrame,
    ufs: list[str],
    escritorios: list[str],
    sub_assunto: str,
    periodo: tuple[date, date] | None,
) -> pd.DataFrame:
    """Aplica os 4 filtros ao df. Lista vazia = sem filtro."""
    if df is None or df.empty:
        return df
    out = df
    if ufs:
        out = out[out["uf"].isin(ufs)]
    if escritorios and "escritorio_id" in out.columns:
        out = out[out["escritorio_id"].isin(escritorios)]
    if sub_assunto and sub_assunto != "Todos" and "sub_assunto" in out.columns:
        out = out[out["sub_assunto"] == sub_assunto]
    if periodo and "data_decisao" in out.columns and len(periodo) == 2:
        dini, dfim = periodo
        if dini and dfim:
            mask = (out["data_decisao"] >= pd.Timestamp(dini)) & (
                out["data_decisao"] <= pd.Timestamp(dfim) + pd.Timedelta(days=1)
            )
            out = out[mask]
    return out


def _filtros_ativos_badge(
    ufs: list[str],
    escritorios: list[str],
    sub_assunto: str,
    periodo: tuple[date, date] | None,
    data_min: date,
    data_max: date,
) -> None:
    """Mostra badge no topo quando há filtros aplicados, com botão de reset."""
    partes = []
    if ufs:
        partes.append(f"{len(ufs)} UF(s)")
    if escritorios:
        partes.append(f"{len(escritorios)} escritório(s)")
    if sub_assunto and sub_assunto != "Todos":
        partes.append(f"sub-assunto: {sub_assunto}")
    if periodo and (periodo[0] != data_min or periodo[1] != data_max):
        partes.append(
            f"período: {periodo[0].strftime('%d/%m/%Y')} → {periodo[1].strftime('%d/%m/%Y')}"
        )

    if not partes:
        return

    c1, c2 = st.columns([6, 1])
    with c1:
        st.info("📊 Filtros ativos: " + " · ".join(partes), icon="🔍")
    with c2:
        if st.button("↩️ Resetar", use_container_width=True):
            # Limpa keys dos widgets e rerun.
            for k in ["flt_ufs", "flt_escritorios", "flt_subassunto", "flt_periodo"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()


# ============================================================
# Bootstrap (fora de funções para rodar na primeira chamada)
# ============================================================
baseline = load_baseline()
df = load_casos()
df_pol, fonte_politica = get_df_com_politica()
df_enr = df_pol  # alias para retrocompatibilidade da Visão Geral


# ============================================================
# Sidebar
# ============================================================
st.sidebar.title("⚖️ Monitoramento")
st.sidebar.caption("Política de Acordos · Banco UFMG")

view = st.sidebar.radio(
    "Navegação",
    ["Visão Geral", "Aderência", "Efetividade"],
)

st.sidebar.divider()

# ---- Filtros globais (afetam Aderência e Efetividade) ----
flt_ufs: list[str] = []
flt_escritorios: list[str] = []
flt_subassunto: str = "Todos"
flt_periodo: tuple[date, date] | None = None
data_min_global: date = date(2025, 4, 1)
data_max_global: date = date(2026, 3, 31)

if df_pol is not None and view != "Visão Geral":
    with st.sidebar.expander("🔍 Filtros", expanded=False):
        uf_opts = sorted(df_pol["uf"].dropna().unique().tolist())
        esc_opts = sorted(df_pol["escritorio_id"].dropna().unique().tolist())

        flt_ufs = st.multiselect(
            "UF",
            options=uf_opts,
            default=[],
            key="flt_ufs",
            help="Vazio = todas as UFs.",
        )
        flt_escritorios = st.multiselect(
            "Escritório",
            options=esc_opts,
            default=[],
            key="flt_escritorios",
            help="Vazio = todos os escritórios.",
        )
        flt_subassunto = st.select_slider(
            "Sub-assunto",
            options=["Todos", "Golpe", "Genérico"],
            value="Todos",
            key="flt_subassunto",
        )
        # Período: defaults vêm dos próprios dados
        data_min_global = pd.Timestamp(df_pol["data_decisao"].min()).date()
        data_max_global = pd.Timestamp(df_pol["data_decisao"].max()).date()
        flt_periodo = st.date_input(
            "Período",
            value=(data_min_global, data_max_global),
            min_value=data_min_global,
            max_value=data_max_global,
            key="flt_periodo",
            format="DD/MM/YYYY",
        )
        # Streamlit retorna tuple quando há 2 datas, date quando só 1 selecionada
        if isinstance(flt_periodo, tuple) and len(flt_periodo) == 2:
            pass
        else:
            flt_periodo = (data_min_global, data_max_global)

st.sidebar.divider()

# Slider só faz sentido na aba Efetividade — em outras abas seria carga cognitiva.
prob_aceita: float = 0.40
if view == "Efetividade":
    prob_aceita = st.sidebar.slider(
        "Probabilidade de aceitação do acordo",
        min_value=0.10,
        max_value=0.95,
        value=0.40,
        step=0.05,
        help=(
            "H1 do log de decisões: calibração da equipe = 40% dos autores "
            "aceitam o acordo proposto (30% da causa). Impacta E02."
        ),
    )

# Fonte dos dados (transparência para a banca).
if df_pol is None:
    st.sidebar.caption(
        "Fonte: baseline real (60k casos) · dataset enriquecido (sintético) "
        "ainda não gerado."
    )
else:
    fonte_txt = {
        "csv": "CSV do XGBoost (política real)",
        "mock": "mock (H2+H3 do DECISOES.md)",
    }.get(fonte_politica, "indisponível")
    st.sidebar.caption(
        f"Baseline: 60k reais · Enriquecido: sintético (H5) · "
        f"Política: **{fonte_txt}**"
    )


# ============================================================
# Aba 1 · Visão Geral
# ============================================================
if view == "Visão Geral":
    st.title("Banco UFMG · Política de Acordos")
    st.caption("Baseline pré-política · 60.000 casos históricos")

    # ---- 4 KPIs no topo ----
    volumetria = baseline["volumetria"]
    financeiro = baseline["financeiro"]
    pct_acordo_hoje = volumetria["dist_resultado_micro"].get("Acordo", 0.0)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Casos Analisados",
        fmt_int_br(volumetria["total_casos"]),
        help="Total de processos no conjunto histórico usado como baseline.",
    )
    c2.metric(
        "Taxa de Êxito Banco",
        fmt_pct(volumetria["taxa_exito_macro"]),
        help="Proporção de casos onde o banco obteve resultado favorável "
        "(macro: Improcedência + Extinção).",
    )
    c3.metric(
        "Custo Total Estimado",
        fmt_brl_curto(financeiro["custo_total_estimado"]),
        help="Soma das condenações observadas nos 60k casos.",
    )
    c4.metric(
        "% Acordo Hoje",
        fmt_pct(pct_acordo_hoje, casas=2),
        help="Política implícita atual = 'defender sempre'. Acordos são "
        "residuais (<1%).",
    )

    st.divider()

    # ---- Linha 1: 2 gráficos ----
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Distribuição de Resultado Micro")
        dist = volumetria["dist_resultado_micro"]
        df_dist = (
            pd.DataFrame(
                {
                    "resultado": list(dist.keys()),
                    "proporcao": list(dist.values()),
                }
            )
            .sort_values("proporcao", ascending=True)
        )
        df_dist["label"] = df_dist["proporcao"].apply(
            lambda p: f"{p*100:.1f}%".replace(".", ",")
        )
        # Destacamos "Acordo" em âmbar para dar contexto ao 0,47%.
        cores = [
            COR_DESTAQUE if r == "Acordo" else COR_PRIMARIA
            for r in df_dist["resultado"]
        ]
        fig_dist = go.Figure(
            go.Bar(
                x=df_dist["proporcao"],
                y=df_dist["resultado"],
                orientation="h",
                marker_color=cores,
                text=df_dist["label"],
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>Proporção: %{x:.2%}<extra></extra>",
            )
        )
        fig_dist.update_layout(
            xaxis_title="Proporção dos casos",
            yaxis_title=None,
            xaxis_tickformat=".0%",
            margin=dict(l=10, r=40, t=10, b=10),
            height=340,
            showlegend=False,
        )
        st.plotly_chart(fig_dist, use_container_width=True)

    with col2:
        st.subheader("Completude Probatória × Êxito do Banco")
        comp = baseline["completude_vs_exito"]
        df_comp = pd.DataFrame(
            [
                {
                    "subsidios": int(k),
                    "taxa_exito": v["taxa_exito"],
                    "n_casos": v["n_casos"],
                }
                for k, v in comp.items()
            ]
        ).sort_values("subsidios")
        df_comp["label"] = df_comp["taxa_exito"].apply(
            lambda p: f"{p*100:.0f}%"
        )
        fig_comp = go.Figure(
            go.Bar(
                x=df_comp["subsidios"],
                y=df_comp["taxa_exito"],
                marker_color=COR_PRIMARIA,
                text=df_comp["label"],
                textposition="outside",
                customdata=df_comp[["n_casos"]],
                hovertemplate=(
                    "<b>%{x} subsídios</b><br>"
                    "Taxa de êxito: %{y:.1%}<br>"
                    "n casos: %{customdata[0]:,}<extra></extra>"
                ),
            )
        )
        fig_comp.add_hline(
            y=0.5,
            line_dash="dash",
            line_color=COR_ALERTA,
            annotation_text="50%",
            annotation_position="right",
        )
        fig_comp.update_layout(
            xaxis_title="Nº de subsídios (0 a 6)",
            yaxis_title="Taxa de êxito",
            yaxis_tickformat=".0%",
            yaxis_range=[0, 1.1],
            xaxis=dict(tickmode="linear"),
            margin=dict(l=10, r=10, t=10, b=10),
            height=340,
            showlegend=False,
        )
        st.plotly_chart(fig_comp, use_container_width=True)

    st.divider()

    # ---- Linha 2: Financeiro (tabela) + UF (barras) ----
    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Resumo Financeiro")
        tabela_fin = pd.DataFrame(
            [
                ("Valor médio de causa", fmt_brl(financeiro["valor_causa_medio"])),
                (
                    "Condenação média (geral)",
                    fmt_brl(financeiro["condenacao_media_geral"]),
                ),
                (
                    "Valor médio de acordo",
                    fmt_brl(financeiro["valor_medio_acordo"]),
                ),
                (
                    "Custo total estimado",
                    fmt_brl(financeiro["custo_total_estimado"], casas=0),
                ),
            ],
            columns=["Métrica", "Valor"],
        )
        st.dataframe(
            tabela_fin,
            hide_index=True,
            use_container_width=True,
        )
        st.caption(
            "Custo total = soma das condenações efetivas observadas nos 60k "
            "casos. Base de comparação para E02 (Economia vs Baseline)."
        )

    with col4:
        st.subheader("Taxa de Êxito por UF (Top 10 por volume)")
        por_uf = baseline["por_uf"]
        df_uf = pd.DataFrame(
            [
                {
                    "uf": uf,
                    "n_casos": v["n_casos"],
                    "taxa_exito": v["taxa_exito"],
                    "valor_causa_medio": v["valor_causa_medio"],
                }
                for uf, v in por_uf.items()
            ]
        )
        df_uf = df_uf.sort_values("n_casos", ascending=False).head(10)
        df_uf = df_uf.sort_values("taxa_exito", ascending=True)
        df_uf["label"] = df_uf["taxa_exito"].apply(
            lambda p: f"{p*100:.1f}%".replace(".", ",")
        )
        fig_uf = go.Figure(
            go.Bar(
                x=df_uf["taxa_exito"],
                y=df_uf["uf"],
                orientation="h",
                marker_color=COR_SECUNDARIA,
                text=df_uf["label"],
                textposition="outside",
                customdata=df_uf[["n_casos", "valor_causa_medio"]],
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Taxa de êxito: %{x:.1%}<br>"
                    "n casos: %{customdata[0]:,}<br>"
                    "Valor médio de causa: R$ %{customdata[1]:,.2f}"
                    "<extra></extra>"
                ),
            )
        )
        fig_uf.add_vline(
            x=volumetria["taxa_exito_macro"],
            line_dash="dash",
            line_color=COR_NEUTRO,
            annotation_text=(
                f"Média: {volumetria['taxa_exito_macro']:.0%}"
            ),
            annotation_position="top",
        )
        fig_uf.update_layout(
            xaxis_title="Taxa de êxito",
            yaxis_title=None,
            xaxis_tickformat=".0%",
            xaxis_range=[0, 1.0],
            margin=dict(l=10, r=40, t=10, b=10),
            height=360,
            showlegend=False,
        )
        st.plotly_chart(fig_uf, use_container_width=True)

    st.caption(
        f"Baseline atualizado em {baseline_mtime_iso()} · "
        "fonte: `data/processed/baseline.json`"
    )


# ============================================================
# Aba 2 · Aderência
# ============================================================
elif view == "Aderência":
    st.title("Monitoramento de Aderência")
    st.caption("Os advogados estão seguindo a política recomendada?")

    if df_pol is None:
        st.info(
            "Dataset enriquecido ainda não disponível. Execute "
            "`python -m src.monitor.gerar_sintetico` para gerar."
        )
        st.stop()

    # Badge com fonte da política (discreto)
    if fonte_politica == "csv":
        st.info("Fonte da política: CSV do XGBoost", icon="🤖")
    else:
        st.info("Fonte da política: mock (H2+H3 · DECISOES.md)", icon="🧪")

    # Aplica filtros globais
    df_f = aplicar_filtros(
        df_pol, flt_ufs, flt_escritorios, flt_subassunto, flt_periodo
    )
    _filtros_ativos_badge(
        flt_ufs, flt_escritorios, flt_subassunto, flt_periodo,
        data_min_global, data_max_global,
    )

    if len(df_f) == 0:
        st.warning("Nenhum caso após aplicar os filtros. Ajuste a seleção.")
        st.stop()

    # ---- KPIs topo (4 colunas) ----
    tsg = metrics_adherence.taxa_seguimento_global(df_f)
    tov = metrics_adherence.taxa_override(df_f)
    adh_pond = metrics_adherence.aderencia_ponderada_por_valor(df_f)
    gap_pond = adh_pond - tsg  # positivo = R$ mais aderente que N; negativo = viés em caros

    # % overrides justificados: razões que NÃO são "discordancia_score" nem "outro"
    overrides = df_f.loc[df_f["aderente"] == 0, "razao_override"]
    n_over = int(overrides.notna().sum())
    if n_over > 0:
        n_justif = int(
            overrides.isin(["info_nova", "neg_em_andamento", "erro_ferramenta"]).sum()
        )
        pct_justif = n_justif / n_over
    else:
        pct_justif = 0.0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric(
        "Taxa de Seguimento (A01)",
        fmt_pct(tsg),
        help="% de casos onde ação tomada == ação recomendada.",
    )
    k2.metric(
        "Taxa de Override (A02)",
        fmt_pct(tov),
        help="Complemento da A01.",
    )
    k3.metric(
        "Aderência Ponderada R$ (A20)",
        fmt_pct(adh_pond),
        delta=f"{gap_pond*100:+.1f} pp vs A01".replace(".", ","),
        delta_color="normal" if gap_pond >= 0 else "inverse",
        help="R$ seguindo política / R$ total. Se cair abaixo de A01, há "
        "viés de override em casos de alto valor.",
    )
    k4.metric(
        "Overrides Justificados",
        fmt_pct(pct_justif),
        help="Proporção de overrides com razão = info_nova, "
        "neg_em_andamento ou erro_ferramenta. "
        "discordancia_score e outro NÃO contam como justificados.",
    )

    st.divider()

    # ---- Linha 1: drift temporal (A18) + razões override (A13) ----
    l1c1, l1c2 = st.columns(2)

    with l1c1:
        st.subheader("Drift Temporal da Aderência (A18)")
        serie = metrics_adherence.drift_temporal_aderencia(df_f, freq="ME")
        df_drift = serie.reset_index()
        df_drift.columns = ["mes", "aderencia"]
        fig_drift = go.Figure()
        # Banda de referência 70-85% (alerta / saudável)
        fig_drift.add_hrect(
            y0=TH_ADESAO_ALERTA, y1=TH_ADESAO_OK,
            fillcolor=COR_DESTAQUE, opacity=0.12,
            line_width=0,
            annotation_text="zona saudável 70-85%",
            annotation_position="top left",
        )
        fig_drift.add_trace(
            go.Scatter(
                x=df_drift["mes"],
                y=df_drift["aderencia"],
                mode="lines+markers",
                line=dict(color=COR_PRIMARIA, width=3),
                marker=dict(size=8, color=COR_PRIMARIA),
                hovertemplate="<b>%{x|%b/%Y}</b><br>Aderência: %{y:.1%}<extra></extra>",
            )
        )
        fig_drift.add_hline(
            y=TH_ADESAO_ALERTA, line_dash="dot", line_color=COR_ALERTA, opacity=0.5,
        )
        fig_drift.add_hline(
            y=TH_ADESAO_OK, line_dash="dot", line_color=COR_OK, opacity=0.5,
        )
        fig_drift.update_layout(
            xaxis_title=None,
            yaxis_title="Aderência mensal",
            yaxis_tickformat=".0%",
            yaxis_range=[0.5, 1.0],
            margin=dict(l=10, r=10, t=10, b=10),
            height=360,
            showlegend=False,
        )
        st.plotly_chart(fig_drift, use_container_width=True)

    with l1c2:
        st.subheader("Distribuição das Razões de Override (A13)")
        razoes = metrics_adherence.distribuicao_razoes_override(df_f)
        if razoes.empty:
            st.info("Nenhum override no recorte atual.")
        else:
            df_raz = razoes.reset_index()
            df_raz.columns = ["razao", "proporcao"]
            df_raz = df_raz.sort_values("proporcao", ascending=True)
            df_raz["label"] = df_raz["proporcao"].apply(
                lambda p: f"{p*100:.1f}%".replace(".", ",")
            )
            # Destaca "discordancia_score" (não-justificada) em vermelho
            cores_raz = [
                COR_ALERTA if r == "discordancia_score"
                else COR_NEUTRO if r == "outro"
                else COR_PRIMARIA
                for r in df_raz["razao"]
            ]
            fig_raz = go.Figure(
                go.Bar(
                    x=df_raz["proporcao"],
                    y=df_raz["razao"],
                    orientation="h",
                    marker_color=cores_raz,
                    text=df_raz["label"],
                    textposition="outside",
                    hovertemplate="<b>%{y}</b><br>%{x:.1%}<extra></extra>",
                )
            )
            fig_raz.update_layout(
                xaxis_title="Proporção dos overrides",
                yaxis_title=None,
                xaxis_tickformat=".0%",
                margin=dict(l=10, r=40, t=10, b=10),
                height=360,
                showlegend=False,
            )
            st.plotly_chart(fig_raz, use_container_width=True)

    st.divider()

    # ---- Linha 2: ranking advogados (A05) + aderência por escritório (A06) ----
    l2c1, l2c2 = st.columns(2)

    with l2c1:
        st.subheader("Top 10 Advogados com Pior Aderência (A05)")
        por_adv = metrics_adherence.aderencia_por_advogado(df_f)
        top_bad = por_adv.head(10).reset_index()
        top_bad = top_bad.sort_values("aderencia", ascending=True)
        top_bad["label"] = top_bad["aderencia"].apply(
            lambda p: f"{p*100:.1f}%".replace(".", ",")
        )
        fig_adv = go.Figure(
            go.Bar(
                x=top_bad["aderencia"],
                y=top_bad["advogado_id"],
                orientation="h",
                marker_color=COR_ALERTA,
                text=top_bad["label"],
                textposition="outside",
                customdata=top_bad[["escritorio", "n_casos"]],
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Aderência: %{x:.1%}<br>"
                    "Escritório: %{customdata[0]}<br>"
                    "n casos: %{customdata[1]:,}<extra></extra>"
                ),
            )
        )
        fig_adv.add_vline(
            x=0.60, line_dash="dash", line_color=COR_ALERTA,
            annotation_text="Threshold P0 (60%)",
            annotation_position="top",
        )
        fig_adv.update_layout(
            xaxis_title="Aderência",
            yaxis_title=None,
            xaxis_tickformat=".0%",
            xaxis_range=[0, 1.0],
            margin=dict(l=10, r=40, t=10, b=10),
            height=380,
            showlegend=False,
        )
        st.plotly_chart(fig_adv, use_container_width=True)

    with l2c2:
        st.subheader("Aderência por Escritório (A06)")
        por_esc = metrics_adherence.aderencia_por_escritorio(df_f).reset_index()
        por_esc = por_esc.sort_values("aderencia", ascending=True)
        cores_esc = [
            COR_OK if a >= TH_ADESAO_OK
            else COR_DESTAQUE if a >= TH_ADESAO_ALERTA
            else COR_ALERTA
            for a in por_esc["aderencia"]
        ]
        por_esc["label"] = por_esc["aderencia"].apply(
            lambda p: f"{p*100:.0f}%"
        )
        fig_esc = go.Figure(
            go.Bar(
                x=por_esc["escritorio_id"],
                y=por_esc["aderencia"],
                marker_color=cores_esc,
                text=por_esc["label"],
                textposition="outside",
                customdata=por_esc[["n_casos", "n_advogados"]],
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "Aderência: %{y:.1%}<br>"
                    "n casos: %{customdata[0]:,}<br>"
                    "n advogados: %{customdata[1]}<extra></extra>"
                ),
            )
        )
        fig_esc.add_hline(
            y=TH_ADESAO_OK, line_dash="dot", line_color=COR_OK, opacity=0.6,
        )
        fig_esc.add_hline(
            y=TH_ADESAO_ALERTA, line_dash="dot", line_color=COR_ALERTA, opacity=0.6,
        )
        fig_esc.update_layout(
            xaxis_title=None,
            yaxis_title="Aderência",
            yaxis_tickformat=".0%",
            yaxis_range=[0, 1.05],
            margin=dict(l=10, r=10, t=10, b=10),
            height=380,
            showlegend=False,
        )
        st.plotly_chart(fig_esc, use_container_width=True)

    st.divider()

    # ---- Linha 3: segmentação (A08 + A04) ----
    l3c1, l3c2 = st.columns(2)

    with l3c1:
        st.subheader("Aderência por Faixa de Valor (A08) · P0")
        por_fx = metrics_adherence.aderencia_por_faixa_valor(df_f).reset_index()
        por_fx.columns = ["faixa_valor", "aderencia"]
        # Ordem lógica: Baixo, Médio, Alto
        ordem = ["Baixo", "Médio", "Alto"]
        por_fx["faixa_valor"] = pd.Categorical(
            por_fx["faixa_valor"], categories=ordem, ordered=True,
        )
        por_fx = por_fx.sort_values("faixa_valor")
        por_fx["label"] = por_fx["aderencia"].apply(
            lambda p: f"{p*100:.1f}%".replace(".", ",")
        )
        cores_fx = [
            COR_OK if a >= TH_ADESAO_OK
            else COR_DESTAQUE if a >= TH_ADESAO_ALERTA
            else COR_ALERTA
            for a in por_fx["aderencia"]
        ]
        fig_fx = go.Figure(
            go.Bar(
                x=por_fx["faixa_valor"].astype(str),
                y=por_fx["aderencia"],
                marker_color=cores_fx,
                text=por_fx["label"],
                textposition="outside",
            )
        )
        fig_fx.add_hline(
            y=TH_ADESAO_ALERTA, line_dash="dot", line_color=COR_ALERTA, opacity=0.6,
            annotation_text="70% (P0)",
            annotation_position="right",
        )
        fig_fx.update_layout(
            xaxis_title="Faixa de valor da causa",
            yaxis_title="Aderência",
            yaxis_tickformat=".0%",
            yaxis_range=[0, 1.05],
            margin=dict(l=10, r=40, t=10, b=10),
            height=340,
            showlegend=False,
        )
        st.plotly_chart(fig_fx, use_container_width=True)

    with l3c2:
        st.subheader("Aderência por Faixa de Completude (A04)")
        por_cp = metrics_adherence.aderencia_por_faixa_completude(df_f).reset_index()
        por_cp.columns = ["faixa_completude", "aderencia"]
        ordem_cp = ["Frágil", "Parcial", "Sólida"]
        por_cp["faixa_completude"] = pd.Categorical(
            por_cp["faixa_completude"], categories=ordem_cp, ordered=True,
        )
        por_cp = por_cp.sort_values("faixa_completude")
        por_cp["label"] = por_cp["aderencia"].apply(
            lambda p: f"{p*100:.1f}%".replace(".", ",")
        )
        cores_cp = [
            COR_OK if a >= TH_ADESAO_OK
            else COR_DESTAQUE if a >= TH_ADESAO_ALERTA
            else COR_ALERTA
            for a in por_cp["aderencia"]
        ]
        fig_cp = go.Figure(
            go.Bar(
                x=por_cp["faixa_completude"].astype(str),
                y=por_cp["aderencia"],
                marker_color=cores_cp,
                text=por_cp["label"],
                textposition="outside",
            )
        )
        fig_cp.update_layout(
            xaxis_title="Completude probatória",
            yaxis_title="Aderência",
            yaxis_tickformat=".0%",
            yaxis_range=[0, 1.05],
            margin=dict(l=10, r=40, t=10, b=10),
            height=340,
            showlegend=False,
        )
        st.plotly_chart(fig_cp, use_container_width=True)

    st.divider()

    # ---- Painel de alertas P0 ----
    alertas = metrics_adherence.alertas_ativos(df_f)
    n_alertas = len(alertas)
    titulo_exp = (
        f"⚠️ Alertas ativos (P0) — {n_alertas} ativo(s)"
        if n_alertas
        else "✅ Alertas ativos (P0) — nenhum"
    )
    with st.expander(titulo_exp, expanded=n_alertas > 0):
        if not alertas:
            st.success("Nenhum alerta P0 acionado no recorte atual.")
        else:
            linhas = []
            for a in alertas:
                linhas.append({
                    "ID": a["id"],
                    "Severidade": a["severidade"],
                    "Métrica": a["nome"],
                    "Valor": fmt_pct(a["valor"]),
                    "Threshold": fmt_pct(a["threshold"]),
                    "Mensagem": a["mensagem"],
                })
            df_al = pd.DataFrame(linhas)
            st.dataframe(df_al, hide_index=True, use_container_width=True)


# ============================================================
# Aba 3 · Efetividade
# ============================================================
elif view == "Efetividade":
    st.title("Monitoramento de Efetividade")
    st.caption("A política está gerando o resultado financeiro esperado?")

    if df_pol is None:
        st.info(
            "Dataset enriquecido ainda não disponível. Execute "
            "`python -m src.monitor.gerar_sintetico` para gerar."
        )
        st.stop()

    # Badge com fonte da política
    if fonte_politica == "csv":
        st.info("Fonte da política: CSV do XGBoost", icon="🤖")
    else:
        st.info("Fonte da política: mock (H2+H3 · DECISOES.md)", icon="🧪")

    # Aplica filtros globais
    df_f = aplicar_filtros(
        df_pol, flt_ufs, flt_escritorios, flt_subassunto, flt_periodo
    )
    _filtros_ativos_badge(
        flt_ufs, flt_escritorios, flt_subassunto, flt_periodo,
        data_min_global, data_max_global,
    )

    if len(df_f) == 0:
        st.warning("Nenhum caso após aplicar os filtros. Ajuste a seleção.")
        st.stop()

    # ---- Simulação dos 2 cenários ----
    # Potencial: todos seguem a política (acao_recomendada)
    sim_potencial = counterfactual.simular_politica(
        df_f,
        acao_col="acao_recomendada",
        valor_acordo_col="valor_acordo_recomendado",
        prob_aceita=prob_aceita,
    )

    # Realizada: advogados decidiram acao_tomada. Para os que fizeram acordo,
    # o valor proposto é valor_acordo_proposto; para defesa, usa custo observado.
    # Preenche NaN de valor_acordo_proposto com 30% da causa (fallback H2)
    # só para não derrubar a simulação — só é usado quando acao_tomada==acordo.
    df_realizado = df_f.copy()
    if "valor_acordo_proposto" in df_realizado.columns:
        fallback = df_realizado["valor_causa"] * 0.30
        df_realizado["valor_acordo_proposto"] = (
            df_realizado["valor_acordo_proposto"].fillna(fallback)
        )
    sim_realizada = counterfactual.simular_politica(
        df_realizado,
        acao_col="acao_tomada",
        valor_acordo_col="valor_acordo_proposto",
        prob_aceita=prob_aceita,
    )

    # Gap = Potencial - Realizada (em R$ e % do potencial)
    gap_rs = sim_potencial["economia_total"] - sim_realizada["economia_total"]
    gap_pct = (
        gap_rs / sim_potencial["economia_total"]
        if sim_potencial["economia_total"] > 0 else 0.0
    )

    # ---- KPIs topo (3 colunas) ----
    k1, k2, k3 = st.columns(3)
    k1.metric(
        "Economia Potencial",
        fmt_brl_curto(sim_potencial["economia_total"]),
        delta=fmt_pct(sim_potencial["economia_percentual"]) + " do baseline",
        delta_color="off",
        help=f"Cenário: todos seguiram a política. prob_aceita={prob_aceita:.2f}.",
    )
    k2.metric(
        "Economia Realizada",
        fmt_brl_curto(sim_realizada["economia_total"]),
        delta=fmt_pct(sim_realizada["economia_percentual"]) + " do baseline",
        delta_color="off",
        help="Cenário: o que os advogados efetivamente fizeram "
        "(acao_tomada + valor_acordo_proposto).",
    )
    k3.metric(
        "Gap de Aderência",
        fmt_brl_curto(gap_rs),
        delta=f"-{gap_pct*100:.1f}% do potencial".replace(".", ","),
        delta_color="inverse",
        help="Economia que a política entregaria se a aderência fosse total, "
        "mas que foi perdida por overrides. É a justificativa do "
        "monitoramento de aderência.",
    )

    st.divider()

    # ---- Linha 1: sensibilidade + redistribuição micro ----
    l1c1, l1c2 = st.columns(2)

    with l1c1:
        st.subheader("Sensibilidade · prob_aceita × Economia")
        probs_varredura = [round(p, 2) for p in np.arange(0.10, 0.96, 0.05)]
        df_sens = counterfactual.simular_sensibilidade(
            df_f,
            acao_col="acao_recomendada",
            valor_acordo_col="valor_acordo_recomendado",
            probs=probs_varredura,
        )
        fig_sens = go.Figure()
        fig_sens.add_trace(
            go.Scatter(
                x=df_sens["prob_aceita_assumida"],
                y=df_sens["economia_total"],
                mode="lines+markers",
                line=dict(color=COR_PRIMARIA, width=3),
                marker=dict(size=6, color=COR_PRIMARIA),
                name="Economia potencial",
                hovertemplate=(
                    "prob_aceita=%{x:.2f}<br>"
                    "Economia: R$ %{y:,.0f}<extra></extra>"
                ),
            )
        )
        # Marcador destacado no ponto ativo do slider
        mask_slider = np.isclose(df_sens["prob_aceita_assumida"], prob_aceita)
        if mask_slider.any():
            economia_ativa = float(df_sens.loc[mask_slider, "economia_total"].iloc[0])
        else:
            economia_ativa = float(sim_potencial["economia_total"])
        fig_sens.add_trace(
            go.Scatter(
                x=[prob_aceita],
                y=[economia_ativa],
                mode="markers",
                marker=dict(size=18, color=COR_DESTAQUE, symbol="star",
                            line=dict(width=2, color=COR_PRIMARIA)),
                name="Slider atual",
                hovertemplate=(
                    "<b>Slider atual</b><br>"
                    "prob_aceita=%{x:.2f}<br>"
                    "Economia: R$ %{y:,.0f}<extra></extra>"
                ),
            )
        )
        fig_sens.update_layout(
            xaxis_title="Probabilidade de aceitação do acordo",
            yaxis_title="Economia total (R$)",
            margin=dict(l=10, r=10, t=10, b=10),
            height=360,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02,
                        xanchor="right", x=1.0),
        )
        st.plotly_chart(fig_sens, use_container_width=True)

    with l1c2:
        st.subheader("Redistribuição de Resultado Micro (E05)")
        df_redist = metrics_effectiveness.redistribuicao_resultado_micro(
            df_f,
            baseline=baseline,
            acao_col="acao_recomendada",
            prob_aceita=prob_aceita,
        )
        fig_red = go.Figure()
        fig_red.add_trace(
            go.Bar(
                x=df_redist["resultado_micro"],
                y=df_redist["antes_pct"],
                name="Antes (baseline)",
                marker_color=COR_NEUTRO,
                hovertemplate="<b>%{x}</b><br>Antes: %{y:.1%}<extra></extra>",
            )
        )
        fig_red.add_trace(
            go.Bar(
                x=df_redist["resultado_micro"],
                y=df_redist["depois_pct"],
                name="Depois (política)",
                marker_color=COR_PRIMARIA,
                hovertemplate="<b>%{x}</b><br>Depois: %{y:.1%}<extra></extra>",
            )
        )
        fig_red.update_layout(
            barmode="group",
            xaxis_title=None,
            yaxis_title="Proporção",
            yaxis_tickformat=".0%",
            margin=dict(l=10, r=10, t=10, b=10),
            height=360,
            legend=dict(orientation="h", yanchor="bottom", y=1.02,
                        xanchor="right", x=1.0),
        )
        st.plotly_chart(fig_red, use_container_width=True)

    st.divider()

    # ---- Linha 2: E09 temporal + E06 completude ----
    l2c1, l2c2 = st.columns(2)

    with l2c1:
        st.subheader("Economia Acumulada Mês a Mês (E09)")
        df_temp = metrics_effectiveness.economia_acumulada_temporal(
            df_f,
            acao_col="acao_recomendada",
            valor_acordo_col="valor_acordo_recomendado",
            prob_aceita=prob_aceita,
            data_col="data_decisao",
        )
        if df_temp.empty:
            st.info("Sem dados temporais no recorte atual.")
        else:
            fig_temp = go.Figure()
            fig_temp.add_trace(
                go.Scatter(
                    x=df_temp["mes"],
                    y=df_temp["economia_acumulada"],
                    mode="lines",
                    fill="tozeroy",
                    line=dict(color=COR_PRIMARIA, width=3),
                    fillcolor="rgba(31,78,121,0.18)",
                    name="Acumulada",
                    hovertemplate=(
                        "<b>%{x}</b><br>Acumulada: R$ %{y:,.0f}<extra></extra>"
                    ),
                )
            )
            fig_temp.add_trace(
                go.Scatter(
                    x=df_temp["mes"],
                    y=df_temp["economia_mes"],
                    mode="lines+markers",
                    line=dict(color=COR_DESTAQUE, width=2, dash="dot"),
                    marker=dict(size=6),
                    name="Mensal",
                    hovertemplate=(
                        "<b>%{x}</b><br>Mês: R$ %{y:,.0f}<extra></extra>"
                    ),
                )
            )
            fig_temp.update_layout(
                xaxis_title=None,
                yaxis_title="Economia (R$)",
                margin=dict(l=10, r=10, t=10, b=10),
                height=360,
                legend=dict(orientation="h", yanchor="bottom", y=1.02,
                            xanchor="right", x=1.0),
            )
            st.plotly_chart(fig_temp, use_container_width=True)

    with l2c2:
        st.subheader("Custo Médio por Faixa de Completude (E06)")
        df_cp = metrics_effectiveness.custo_por_faixa_completude(
            df_f,
            acao_col="acao_recomendada",
            valor_acordo_col="valor_acordo_recomendado",
            prob_aceita=prob_aceita,
        )
        if df_cp.empty:
            st.info("Sem dados no recorte atual.")
        else:
            # custo médio = custo_politica / n_casos
            df_cp = df_cp.copy()
            df_cp["custo_medio_obs"] = df_cp["custo_observado"] / df_cp["n_casos"]
            df_cp["custo_medio_pol"] = df_cp["custo_politica"] / df_cp["n_casos"]
            # ordem lógica
            ordem_cp = ["Frágil", "Parcial", "Sólida"]
            df_cp["faixa_completude"] = pd.Categorical(
                df_cp["faixa_completude"], categories=ordem_cp, ordered=True,
            )
            df_cp = df_cp.sort_values("faixa_completude")

            fig_e06 = go.Figure()
            fig_e06.add_trace(
                go.Bar(
                    x=df_cp["faixa_completude"].astype(str),
                    y=df_cp["custo_medio_obs"],
                    name="Observado (baseline)",
                    marker_color=COR_NEUTRO,
                    hovertemplate="<b>%{x}</b><br>Observado: R$ %{y:,.0f}<extra></extra>",
                )
            )
            fig_e06.add_trace(
                go.Bar(
                    x=df_cp["faixa_completude"].astype(str),
                    y=df_cp["custo_medio_pol"],
                    name="Sob política",
                    marker_color=COR_PRIMARIA,
                    hovertemplate="<b>%{x}</b><br>Política: R$ %{y:,.0f}<extra></extra>",
                )
            )
            fig_e06.update_layout(
                barmode="group",
                xaxis_title="Completude probatória",
                yaxis_title="Custo médio por caso (R$)",
                margin=dict(l=10, r=10, t=10, b=10),
                height=360,
                legend=dict(orientation="h", yanchor="bottom", y=1.02,
                            xanchor="right", x=1.0),
            )
            st.plotly_chart(fig_e06, use_container_width=True)

    st.caption(
        "Fonte da política: MOCK (subs_total ≤ 3, 30% da causa). Quando CSV "
        "do XGBoost chegar, dashboard recalcula automaticamente."
    )
