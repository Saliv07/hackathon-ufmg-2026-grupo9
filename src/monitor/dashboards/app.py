"""
Dashboard de Monitoramento — Política de Acordos · Banco UFMG
Requisitos 4 (Aderência) e 5 (Efetividade) do Hackathon UFMG / Enter 2026.

Frente: monitoramento (Matheus / Nekark Data Intelligence).
Branch: vilas.

Arquitetura visual (após merge com a plataforma do advogado):
    - Tema dark unificado (tokens em `theme_banco_ufmg`, fonte Inter/JetBrains Mono,
      accent laranja #FFAE35).
    - Cada aba em 3 camadas de leitura:
        Camada 1 · MANCHETE    -> `ui.headline(...)` (o insight em uma frase)
        Camada 2 · PROVA       -> 2-3 gráficos essenciais que sustentam a manchete
        Camada 3 · EXPLORAÇÃO  -> `st.expander(...)` com detalhes, rankings,
                                   segmentações, alertas completos

Abas:
    - Aderência    -> KPIs A01/A02/A20 + drift temporal + rankings + alertas.
    - Efetividade  -> Potencial vs Realizada vs Gap + sensibilidade + redistribuição.

A visão executiva macro (baseline pré-política) vive na plataforma React em
`frontend/src/components/Dashboard.jsx`. Este dashboard foca exclusivamente nos
requisitos 4 e 5 para evitar duplicação de escopo.

Filtros globais (sidebar): UF, escritório, sub-assunto e período aplicam-se a
ambas as abas.
"""
from __future__ import annotations

import json
import sys
from datetime import date
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
from src.monitor.dashboards import components as ui
from src.monitor.dashboards.theme_banco_ufmg import (
    Colors,
    apply_theme,
    fmt_brl,
    fmt_brl_compact,
    fmt_int_br,
    fmt_pct,
    get_plotly_layout,
)
from src.monitor.paths import (
    BASELINE_JSON,
    CASOS_60K,
    CASOS_ENRIQUECIDOS,
    DATA_PROCESSED,
)


# ============================================================
# Configuração global + tema
# ============================================================
st.set_page_config(
    page_title="Monitoramento UFMG",
    layout="wide",
    page_icon="⚖️",  # favicon do browser — não aparece dentro do app
)
apply_theme()


# Thresholds de severidade para A06 (aderência por escritório) — alinhados
# com os alertas P0 definidos em metrics_adherence.alertas_ativos.
TH_ADESAO_OK = 0.85
TH_ADESAO_ALERTA = 0.70


def _plotly(fig: go.Figure, height: int | None = None) -> go.Figure:
    """Aplica o layout padrão do tema (dark, fontes, paleta)."""
    layout = get_plotly_layout()
    if height is not None:
        layout["height"] = height
    fig.update_layout(**layout)
    return fig


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
        # CSV do XGBoost prevalece sobre o mock do gerador sintético.
        # Remove as colunas de política do enriquecido para evitar colisão
        # (_x / _y) no merge — a `acao_tomada` e `valor_acordo_proposto`
        # continuam vindo do enriquecido (são a ação efetiva do advogado).
        colunas_mock = [
            c for c in ("acao_recomendada", "valor_acordo_recomendado",
                        "score_confianca")
            if c in df_enr.columns
        ]
        df_enr = df_enr.drop(columns=colunas_mock)
        merged = df_enr.merge(politica, on="numero_processo", how="left")
        return merged, "csv"
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
        st.info("Filtros ativos: " + " · ".join(partes))
    with c2:
        if st.button("Resetar", use_container_width=True):
            for k in ["flt_ufs", "flt_escritorios", "flt_subassunto", "flt_periodo"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()


# ============================================================
# Bootstrap (primeira chamada)
# ============================================================
baseline = load_baseline()
df = load_casos()
df_pol, fonte_politica = get_df_com_politica()
df_enr = df_pol  # alias


# ============================================================
# Sidebar
# ============================================================
# Título compacto + pills de navegação (CSS em theme_banco_ufmg).
st.sidebar.markdown(
    '<h1 class="ufmg-sidebar-title">Monitoramento</h1>',
    unsafe_allow_html=True,
)

# Radio nativo com CSS custom — visual de "pills" (círculos escondidos,
# labels estilizados). Ver regras `.ufmg-nav-radio` em theme_banco_ufmg.
st.sidebar.markdown('<div class="ufmg-nav-radio">', unsafe_allow_html=True)
view = st.sidebar.radio(
    "Navegação",
    ["Aderência", "Efetividade"],
    label_visibility="collapsed",
)
st.sidebar.markdown('</div>', unsafe_allow_html=True)

st.sidebar.divider()

flt_ufs: list[str] = []
flt_escritorios: list[str] = []
flt_subassunto: str = "Todos"
flt_periodo: tuple[date, date] | None = None
data_min_global: date = date(2025, 4, 1)
data_max_global: date = date(2026, 3, 31)

if df_pol is not None:
    with st.sidebar.expander("Filtros", expanded=False):
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

# ============================================================
# Aba 1 · Aderência
# ============================================================
if view == "Aderência":
    st.title("Monitoramento de aderência")
    st.caption("Os advogados estão seguindo a política recomendada?")

    if df_pol is None:
        st.info(
            "Dataset enriquecido ainda não disponível. Execute "
            "`python -m src.monitor.gerar_sintetico` para gerar."
        )
        st.stop()

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

    # ────────────────────────────────────────────────────────
    # Métricas-base (usadas na manchete e nos KPIs)
    # ────────────────────────────────────────────────────────
    tsg = metrics_adherence.taxa_seguimento_global(df_f)
    tov = metrics_adherence.taxa_override(df_f)
    adh_pond = metrics_adherence.aderencia_ponderada_por_valor(df_f)
    gap_pond = adh_pond - tsg

    por_adv = metrics_adherence.aderencia_por_advogado(df_f)
    criticos = por_adv[por_adv["aderencia"] < 0.60]
    n_criticos = int(len(criticos))
    n_escr_criticos = int(criticos["escritorio"].nunique()) if n_criticos else 0

    # Concentração de risco: quanto do R$ em causa os críticos respondem
    if n_criticos > 0:
        ids_crit = criticos.index.tolist()
        valor_crit = float(df_f.loc[df_f["advogado_id"].isin(ids_crit), "valor_causa"].sum())
        valor_tot = float(df_f["valor_causa"].sum())
        pct_risco_concentrado = valor_crit / valor_tot if valor_tot > 0 else 0.0
    else:
        pct_risco_concentrado = 0.0

    # Overrides justificados
    overrides = df_f.loc[df_f["aderente"] == 0, "razao_override"]
    n_over = int(overrides.notna().sum())
    if n_over > 0:
        n_justif = int(
            overrides.isin(["info_nova", "neg_em_andamento", "erro_ferramenta"]).sum()
        )
        pct_justif = n_justif / n_over
    else:
        pct_justif = 0.0

    # ────────────────────────────────────────────────────────
    # Camada 1 · MANCHETE (dinâmica)
    # ────────────────────────────────────────────────────────
    if n_criticos > 0 and n_escr_criticos > 0:
        insight = (
            f"{n_criticos} advogado(s) concentrado(s) em {n_escr_criticos} "
            f"escritório(s) respondem por {pct_risco_concentrado*100:.0f}% "
            "do risco financeiro"
        )
        subtxt = (
            f"Taxa global de aderência à política — meta mínima 85%. "
            f"{fmt_int_br(n_over)} override(s) no recorte, "
            f"{pct_justif*100:.0f}% justificados."
        )
    else:
        insight = "Nenhum advogado crítico (<60%) no recorte atual"
        subtxt = "Taxa global de aderência à política — meta mínima 85%"

    ui.headline(
        texto_insight=insight,
        valor_grande=fmt_pct(tsg),
        subtexto=subtxt,
    )

    # KPIs-suporte (sem emojis; cor no delta quando faz sentido)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(
        "Taxa de seguimento",
        fmt_pct(tsg),
        help="A01 · % de casos onde ação tomada == ação recomendada.",
    )
    k2.metric(
        "Taxa de override",
        fmt_pct(tov),
        help="A02 · complemento da taxa de seguimento.",
    )
    k3.metric(
        "Aderência ponderada pelo risco financeiro",
        fmt_pct(adh_pond),
        delta=f"{gap_pond*100:+.1f} pp vs seguimento".replace(".", ","),
        delta_color="normal" if gap_pond >= 0 else "inverse",
        help="A20 · R$ seguindo política / R$ total. Abaixo do seguimento = "
        "viés de override em casos caros.",
    )
    k4.metric(
        "Overrides justificados",
        fmt_pct(pct_justif),
        help="Razões válidas: info_nova, neg_em_andamento, erro_ferramenta. "
        "discordancia_score e outro NÃO contam.",
    )

    # ────────────────────────────────────────────────────────
    # Camada 2 · PROVA — 3 gráficos essenciais
    # ────────────────────────────────────────────────────────
    ui.section_divider("Prova · o que sustenta o número")

    # Prova 1: evolução ao longo do tempo (era "drift temporal A18")
    st.subheader("Evolução ao longo do tempo")
    serie = metrics_adherence.drift_temporal_aderencia(df_f, freq="ME")
    df_drift = serie.reset_index()
    df_drift.columns = ["mes", "aderencia"]
    fig_drift = go.Figure()
    fig_drift.add_hrect(
        y0=TH_ADESAO_ALERTA, y1=TH_ADESAO_OK,
        fillcolor=Colors.ACCENT, opacity=0.08,
        line_width=0,
        annotation_text="Zona de atenção 70-85%",
        annotation_position="top left",
    )
    fig_drift.add_trace(
        go.Scatter(
            x=df_drift["mes"],
            y=df_drift["aderencia"],
            mode="lines+markers",
            line=dict(color=Colors.ACCENT, width=3),
            marker=dict(size=8, color=Colors.ACCENT),
            hovertemplate="<b>%{x|%b/%Y}</b><br>Aderência: %{y:.1%}<extra></extra>",
        )
    )
    fig_drift.add_hline(
        y=TH_ADESAO_ALERTA, line_dash="dot", line_color=Colors.DANGER, opacity=0.6,
    )
    fig_drift.add_hline(
        y=TH_ADESAO_OK, line_dash="dot", line_color=Colors.SUCCESS, opacity=0.6,
    )
    fig_drift.update_layout(
        xaxis_title=None,
        yaxis_title="Aderência mensal",
        yaxis_tickformat=".0%",
        yaxis_range=[0.5, 1.0],
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False,
    )
    st.plotly_chart(_plotly(fig_drift, height=340), use_container_width=True)

    # Prova 2 & 3 · lado a lado: ranking pior + aderência por escritório
    p1, p2 = st.columns(2)

    with p1:
        st.subheader("Top 10 advogados com pior aderência")
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
                marker_color=Colors.DANGER,
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
            x=0.60, line_dash="dash", line_color=Colors.DANGER,
            annotation_text="Limite urgente (60%)",
            annotation_position="top",
        )
        fig_adv.update_layout(
            xaxis_title="Aderência",
            yaxis_title=None,
            xaxis_tickformat=".0%",
            xaxis_range=[0, 1.0],
            margin=dict(l=10, r=40, t=10, b=10),
            showlegend=False,
        )
        st.plotly_chart(_plotly(fig_adv, height=380), use_container_width=True)

    with p2:
        st.subheader("Aderência por escritório")
        por_esc = metrics_adherence.aderencia_por_escritorio(df_f).reset_index()
        por_esc = por_esc.sort_values("aderencia", ascending=True)
        cores_esc = [
            Colors.SUCCESS if a >= TH_ADESAO_OK
            else Colors.WARNING if a >= TH_ADESAO_ALERTA
            else Colors.DANGER
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
            y=TH_ADESAO_OK, line_dash="dot", line_color=Colors.SUCCESS, opacity=0.6,
        )
        fig_esc.add_hline(
            y=TH_ADESAO_ALERTA, line_dash="dot", line_color=Colors.DANGER, opacity=0.6,
        )
        fig_esc.update_layout(
            xaxis_title=None,
            yaxis_title="Aderência",
            yaxis_tickformat=".0%",
            yaxis_range=[0, 1.05],
            margin=dict(l=10, r=10, t=10, b=10),
            showlegend=False,
        )
        st.plotly_chart(_plotly(fig_esc, height=380), use_container_width=True)

    # ────────────────────────────────────────────────────────
    # Camada 3 · EXPLORAÇÃO (expander)
    # ────────────────────────────────────────────────────────
    ui.section_divider("Exploração · segmentações e alertas completos")

    alertas = metrics_adherence.alertas_ativos(df_f)
    n_alertas = len(alertas)
    label_alertas = (
        f"Alertas urgentes — {n_alertas} ativo(s)"
        if n_alertas
        else "Alertas urgentes — nenhum"
    )

    with st.expander("Análises detalhadas", expanded=n_alertas > 0):
        tabs_exp = st.tabs([
            "Razões de override",
            "Aderência por faixa de valor",
            "Aderência por completude",
            "Aderência por UF",
            label_alertas,
        ])

        # Razões de override (antiga A13)
        with tabs_exp[0]:
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
                cores_raz = [
                    Colors.DANGER if r == "discordancia_score"
                    else Colors.TEXT_MUTED if r == "outro"
                    else Colors.ACCENT
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
                    showlegend=False,
                )
                st.plotly_chart(_plotly(fig_raz, height=340), use_container_width=True)

        # A08 — faixa de valor
        with tabs_exp[1]:
            por_fx = metrics_adherence.aderencia_por_faixa_valor(df_f).reset_index()
            por_fx.columns = ["faixa_valor", "aderencia"]
            ordem = ["Baixo", "Médio", "Alto"]
            por_fx["faixa_valor"] = pd.Categorical(
                por_fx["faixa_valor"], categories=ordem, ordered=True,
            )
            por_fx = por_fx.sort_values("faixa_valor")
            por_fx["label"] = por_fx["aderencia"].apply(
                lambda p: f"{p*100:.1f}%".replace(".", ",")
            )
            cores_fx = [
                Colors.SUCCESS if a >= TH_ADESAO_OK
                else Colors.WARNING if a >= TH_ADESAO_ALERTA
                else Colors.DANGER
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
                y=TH_ADESAO_ALERTA, line_dash="dot",
                line_color=Colors.DANGER, opacity=0.6,
                annotation_text="Limite urgente (70%)",
                annotation_position="right",
            )
            fig_fx.update_layout(
                xaxis_title="Faixa de valor da causa",
                yaxis_title="Aderência",
                yaxis_tickformat=".0%",
                yaxis_range=[0, 1.05],
                margin=dict(l=10, r=40, t=10, b=10),
                showlegend=False,
            )
            st.plotly_chart(_plotly(fig_fx, height=320), use_container_width=True)

        # A04 — faixa de completude
        with tabs_exp[2]:
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
                Colors.SUCCESS if a >= TH_ADESAO_OK
                else Colors.WARNING if a >= TH_ADESAO_ALERTA
                else Colors.DANGER
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
                showlegend=False,
            )
            st.plotly_chart(_plotly(fig_cp, height=320), use_container_width=True)

        # A07 — por UF
        with tabs_exp[3]:
            por_uf_ad = metrics_adherence.aderencia_por_uf(df_f).reset_index()
            por_uf_ad.columns = ["uf", "aderencia"]
            por_uf_ad = por_uf_ad.sort_values("aderencia")
            por_uf_ad["label"] = por_uf_ad["aderencia"].apply(
                lambda p: f"{p*100:.1f}%".replace(".", ",")
            )
            cores_uf = [
                Colors.SUCCESS if a >= TH_ADESAO_OK
                else Colors.WARNING if a >= TH_ADESAO_ALERTA
                else Colors.DANGER
                for a in por_uf_ad["aderencia"]
            ]
            fig_uf_ad = go.Figure(
                go.Bar(
                    x=por_uf_ad["aderencia"],
                    y=por_uf_ad["uf"],
                    orientation="h",
                    marker_color=cores_uf,
                    text=por_uf_ad["label"],
                    textposition="outside",
                )
            )
            fig_uf_ad.update_layout(
                xaxis_title="Aderência",
                yaxis_title=None,
                xaxis_tickformat=".0%",
                xaxis_range=[0, 1.0],
                margin=dict(l=10, r=40, t=10, b=10),
                showlegend=False,
            )
            st.plotly_chart(_plotly(fig_uf_ad, height=360), use_container_width=True)

        # Alertas urgentes (antigo P0)
        with tabs_exp[4]:
            if not alertas:
                st.success("Nenhum alerta urgente acionado no recorte atual.")
            else:
                linhas = []
                for a in alertas:
                    linhas.append({
                        "ID": a["id"],
                        "Severidade": "Urgente",
                        "Métrica": a["nome"],
                        "Valor": fmt_pct(a["valor"]),
                        "Threshold": fmt_pct(a["threshold"]),
                        "Mensagem": a["mensagem"],
                    })
                df_al = pd.DataFrame(linhas)
                st.dataframe(df_al, hide_index=True, use_container_width=True)


# ============================================================
# Aba 2 · Efetividade
# ============================================================
elif view == "Efetividade":
    st.title("Monitoramento de efetividade")
    st.caption("A política está gerando o resultado financeiro esperado?")

    if df_pol is None:
        st.info(
            "Dataset enriquecido ainda não disponível. Execute "
            "`python -m src.monitor.gerar_sintetico` para gerar."
        )
        st.stop()

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

    # ────────────────────────────────────────────────────────
    # Simulação dos 2 cenários
    # ────────────────────────────────────────────────────────
    sim_potencial = counterfactual.simular_politica(
        df_f,
        acao_col="acao_recomendada",
        valor_acordo_col="valor_acordo_recomendado",
        prob_aceita=prob_aceita,
    )
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

    gap_rs = sim_potencial["economia_total"] - sim_realizada["economia_total"]
    gap_pct = (
        gap_rs / sim_potencial["economia_total"]
        if sim_potencial["economia_total"] > 0 else 0.0
    )
    economia_potencial = sim_potencial["economia_total"]

    # ────────────────────────────────────────────────────────
    # Camada 1 · MANCHETE (dinâmica)
    # ────────────────────────────────────────────────────────
    ui.headline(
        texto_insight=(
            f"Política em curso deixa {gap_pct*100:.0f}% da economia potencial "
            "sobre a mesa"
        ),
        valor_grande=fmt_brl_compact(economia_potencial),
        subtexto=(
            "Economia potencial anual se aderência = 100% "
            f"(probabilidade de aceitação atual: {prob_aceita:.0%})"
        ),
    )

    # KPIs de contexto — cores conforme severidade do valor
    k1, k2, k3 = st.columns(3)
    k1.metric(
        "Economia potencial",
        fmt_brl_compact(sim_potencial["economia_total"]),
        delta=fmt_pct(sim_potencial["economia_percentual"]) + " do baseline",
        delta_color="off",
        help=f"Cenário: todos seguiram a política. prob_aceita={prob_aceita:.2f}.",
    )
    k2.metric(
        "Economia realizada",
        fmt_brl_compact(sim_realizada["economia_total"]),
        delta=fmt_pct(sim_realizada["economia_percentual"]) + " do baseline",
        delta_color="off",
        help="Cenário: o que os advogados efetivamente fizeram "
        "(acao_tomada + valor_acordo_proposto).",
    )
    k3.metric(
        "Gap de aderência",
        fmt_brl_compact(gap_rs),
        delta=f"-{gap_pct*100:.1f}% do potencial".replace(".", ","),
        delta_color="inverse",
        help="Economia que a política entregaria se a aderência fosse total, "
        "mas que foi perdida por overrides.",
    )

    # ────────────────────────────────────────────────────────
    # Camada 2 · PROVA — 3 gráficos essenciais
    # ────────────────────────────────────────────────────────
    ui.section_divider("Prova · o que sustenta o número")

    # Prova 1: sensibilidade (curva + marcador do slider)
    st.subheader("Curva de sensibilidade · probabilidade × economia")
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
            line=dict(color=Colors.ACCENT, width=3),
            marker=dict(size=6, color=Colors.ACCENT),
            name="Economia potencial",
            hovertemplate=(
                "prob_aceita=%{x:.2f}<br>"
                "Economia: R$ %{y:,.0f}<extra></extra>"
            ),
        )
    )
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
            marker=dict(
                size=18, color=Colors.ACCENT, symbol="star",
                line=dict(width=2, color=Colors.ACCENT_HOVER),
            ),
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
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1.0),
    )
    st.plotly_chart(_plotly(fig_sens, height=340), use_container_width=True)

    p1, p2 = st.columns(2)

    # Prova 2: economia acumulada mês a mês (antigo E09)
    with p1:
        st.subheader("Economia acumulada mês a mês")
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
                    line=dict(color=Colors.ACCENT, width=3),
                    fillcolor="rgba(255,174,53,0.18)",
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
                    line=dict(color=Colors.SUCCESS, width=2, dash="dot"),
                    marker=dict(size=6, color=Colors.SUCCESS),
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
                legend=dict(orientation="h", yanchor="bottom", y=1.02,
                            xanchor="right", x=1.0),
            )
            st.plotly_chart(_plotly(fig_temp, height=340), use_container_width=True)

    # Prova 3: redistribuição de resultado micro antes/depois (antigo E05)
    with p2:
        st.subheader("Redistribuição de resultado micro · antes × depois")
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
                marker_color=Colors.TEXT_MUTED,
                hovertemplate="<b>%{x}</b><br>Antes: %{y:.1%}<extra></extra>",
            )
        )
        fig_red.add_trace(
            go.Bar(
                x=df_redist["resultado_micro"],
                y=df_redist["depois_pct"],
                name="Depois (política)",
                marker_color=Colors.ACCENT,
                hovertemplate="<b>%{x}</b><br>Depois: %{y:.1%}<extra></extra>",
            )
        )
        fig_red.update_layout(
            barmode="group",
            xaxis_title=None,
            yaxis_title="Proporção",
            yaxis_tickformat=".0%",
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02,
                        xanchor="right", x=1.0),
        )
        st.plotly_chart(_plotly(fig_red, height=340), use_container_width=True)

    # ────────────────────────────────────────────────────────
    # Camada 3 · EXPLORAÇÃO
    # ────────────────────────────────────────────────────────
    ui.section_divider("Exploração · custos, recall e precision")

    with st.expander("Análises detalhadas", expanded=False):
        tabs_ef = st.tabs([
            "Custo por completude probatória",
            "Distribuição dos valores de acordo",
            "Detalhes dos cenários",
        ])

        with tabs_ef[0]:
            df_cp = metrics_effectiveness.custo_por_faixa_completude(
                df_f,
                acao_col="acao_recomendada",
                valor_acordo_col="valor_acordo_recomendado",
                prob_aceita=prob_aceita,
            )
            if df_cp.empty:
                st.info("Sem dados no recorte atual.")
            else:
                df_cp = df_cp.copy()
                df_cp["custo_medio_obs"] = df_cp["custo_observado"] / df_cp["n_casos"]
                df_cp["custo_medio_pol"] = df_cp["custo_politica"] / df_cp["n_casos"]
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
                        marker_color=Colors.TEXT_MUTED,
                        hovertemplate="<b>%{x}</b><br>Observado: R$ %{y:,.0f}<extra></extra>",
                    )
                )
                fig_e06.add_trace(
                    go.Bar(
                        x=df_cp["faixa_completude"].astype(str),
                        y=df_cp["custo_medio_pol"],
                        name="Sob política",
                        marker_color=Colors.ACCENT,
                        hovertemplate="<b>%{x}</b><br>Política: R$ %{y:,.0f}<extra></extra>",
                    )
                )
                fig_e06.update_layout(
                    barmode="group",
                    xaxis_title="Completude probatória",
                    yaxis_title="Custo médio por caso (R$)",
                    margin=dict(l=10, r=10, t=10, b=10),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02,
                                xanchor="right", x=1.0),
                )
                st.plotly_chart(_plotly(fig_e06, height=340), use_container_width=True)

        with tabs_ef[1]:
            st.caption(
                "Distribuição dos valores propostos em acordos realizados "
                "(quando havia valor_acordo_proposto preenchido)."
            )
            acordos_feitos = df_f[
                (df_f["acao_tomada"] == "acordo")
                & df_f["valor_acordo_proposto"].notna()
            ].copy()
            if acordos_feitos.empty:
                st.info("Sem acordos realizados no recorte atual.")
            else:
                acordos_feitos["ratio"] = (
                    acordos_feitos["valor_acordo_proposto"]
                    / acordos_feitos["valor_causa"]
                )
                fig_hist = go.Figure(
                    go.Histogram(
                        x=acordos_feitos["ratio"],
                        nbinsx=30,
                        marker_color=Colors.ACCENT,
                        hovertemplate="Ratio: %{x:.2f}<br>n: %{y}<extra></extra>",
                    )
                )
                fig_hist.add_vline(
                    x=0.30, line_dash="dash", line_color=Colors.SUCCESS,
                    annotation_text="30% (política)",
                    annotation_position="top",
                )
                fig_hist.update_layout(
                    xaxis_title="Valor do acordo / valor da causa",
                    yaxis_title="Número de acordos",
                    margin=dict(l=10, r=10, t=10, b=10),
                    showlegend=False,
                )
                st.plotly_chart(_plotly(fig_hist, height=320), use_container_width=True)

        with tabs_ef[2]:
            linhas_det = [
                ("Casos no recorte", fmt_int_br(len(df_f))),
                ("Economia potencial", fmt_brl(sim_potencial["economia_total"], casas=0)),
                ("Economia realizada", fmt_brl(sim_realizada["economia_total"], casas=0)),
                ("Gap (R$)", fmt_brl(gap_rs, casas=0)),
                ("Gap (%)", fmt_pct(gap_pct)),
                ("prob_aceita assumida", f"{prob_aceita:.0%}"),
            ]
            df_det = pd.DataFrame(linhas_det, columns=["Métrica", "Valor"])
            st.dataframe(df_det, hide_index=True, use_container_width=True)

    st.caption(
        "Fonte da política: MOCK (subs_total ≤ 3, 30% da causa). Quando CSV "
        "do XGBoost chegar, dashboard recalcula automaticamente."
    )
