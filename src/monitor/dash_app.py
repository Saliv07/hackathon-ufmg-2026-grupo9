"""
Dashboard de Monitoramento — Política de Acordos · Banco UFMG (Plotly Dash).

Migração do Streamlit original (src/monitor/dashboards/app.py). Montado como
sub-app Dash dentro do Flask server da plataforma — rota `/monitoramento/`.

Filtros globais (UF, escritório, sub-assunto, período, prob_aceita) vêm da
URL query string; o React controla essas querystrings para que os filtros
sejam acionáveis do chrome da plataforma sem duplicar UI na sidebar do Dash.

Exemplos:
    /monitoramento/?tab=efetividade&uf=SP,MG&prob=0.50
    /monitoramento/?sub=Golpe&from=2025-06-01&to=2026-03-31

Reusa intacto:
    - src.monitor.metrics_adherence
    - src.monitor.metrics_effectiveness
    - src.monitor.counterfactual

Tema dark replica theme_banco_ufmg (Inter + JetBrains Mono, #FFAE35).
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from dash import Dash, Input, Output, dcc, html, no_update
from flask_caching import Cache

from src.monitor import counterfactual, metrics_adherence, metrics_effectiveness
from src.monitor.paths import (
    BASELINE_JSON,
    CASOS_ENRIQUECIDOS,
    DATA_PROCESSED,
)


# ============================================================
# Tokens de design (espelho de theme_banco_ufmg, sem dependência de Streamlit)
# ============================================================
class Colors:
    BG_MAIN = "#000000"
    BG_PANEL = "#0a0a0a"
    BG_SIDEBAR = "#050505"
    BG_ELEV = "#111111"
    TEXT_MAIN = "#ffffff"
    TEXT_MUTED = "#a1a1a1"
    TEXT_DIM = "#666666"
    ACCENT = "#FFAE35"
    ACCENT_HOVER = "#e69d30"
    SUCCESS = "#4CAF50"
    WARNING = "#ff9800"
    DANGER = "#f44336"
    BORDER = "#1a1a1a"
    BORDER_STRONG = "#262626"
    NEUTRAL = "#7F8C8D"


FONT_PRIMARY = "'Inter', 'Segoe UI', system-ui, sans-serif"
FONT_MONO = "'JetBrains Mono', monospace"

TH_ADESAO_OK = 0.85
TH_ADESAO_ALERTA = 0.70


# ============================================================
# Formatadores pt-BR (copiados de theme_banco_ufmg, sem streamlit)
# ============================================================
def fmt_brl(valor, casas: int = 2) -> str:
    if valor is None or (isinstance(valor, float) and np.isnan(valor)):
        return "—"
    sinal = "-" if valor < 0 else ""
    valor = abs(valor)
    txt = f"{valor:,.{casas}f}"
    txt = txt.replace(",", "§").replace(".", ",").replace("§", ".")
    return f"{sinal}R$ {txt}"


def fmt_brl_compact(valor) -> str:
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


def fmt_int_br(valor) -> str:
    if valor is None:
        return "—"
    return f"{int(valor):,}".replace(",", ".")


def fmt_pct(valor, casas: int = 1) -> str:
    if valor is None or (isinstance(valor, float) and np.isnan(valor)):
        return "—"
    return f"{valor*100:.{casas}f}%".replace(".", ",")


# ============================================================
# Plotly layout base
# ============================================================
def get_plotly_layout() -> dict:
    return dict(
        template="plotly_dark",
        paper_bgcolor=Colors.BG_PANEL,
        plot_bgcolor=Colors.BG_PANEL,
        font=dict(family="Inter, sans-serif", color=Colors.TEXT_MAIN, size=12),
        colorway=[
            Colors.ACCENT, Colors.SUCCESS, Colors.WARNING,
            Colors.DANGER, Colors.TEXT_MUTED,
        ],
        xaxis=dict(gridcolor=Colors.BORDER, zerolinecolor=Colors.BORDER),
        yaxis=dict(gridcolor=Colors.BORDER, zerolinecolor=Colors.BORDER),
    )


def _apply_layout(fig: go.Figure, height: int | None = None) -> go.Figure:
    layout = get_plotly_layout()
    if height is not None:
        layout["height"] = height
    fig.update_layout(**layout)
    return fig


# ============================================================
# CSS global (injetado via app.index_string)
# ============================================================
GLOBAL_CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body {{
  margin: 0;
  padding: 0;
  background-color: {Colors.BG_MAIN};
  color: {Colors.TEXT_MAIN};
  font-family: {FONT_PRIMARY};
  -webkit-font-smoothing: antialiased;
}}

#react-entry-point, .dash-root, ._dash-undo-redo, #_dash-app-content {{
  background-color: {Colors.BG_MAIN} !important;
}}

.monitor-root {{
  padding: 16px 24px 32px 24px;
  max-width: 1400px;
  margin: 0 auto;
  font-size: 13px;
}}

.monitor-title {{
  font-size: 20px;
  font-weight: 600;
  letter-spacing: -0.02em;
  color: {Colors.TEXT_MAIN};
  margin: 0 0 4px 0;
}}

.monitor-caption {{
  font-size: 12px;
  color: {Colors.TEXT_MUTED};
  margin-bottom: 16px;
}}

/* --- Tabs --- */
.monitor-tabs .tab {{
  background: transparent !important;
  color: {Colors.TEXT_MUTED} !important;
  border: none !important;
  border-radius: 6px !important;
  padding: 6px 14px !important;
  font-family: {FONT_PRIMARY} !important;
  font-weight: 500 !important;
  font-size: 12px !important;
}}
.monitor-tabs .tab--selected {{
  background: {Colors.BG_ELEV} !important;
  color: {Colors.ACCENT} !important;
  border-bottom: 2px solid {Colors.ACCENT} !important;
}}
.monitor-tabs-container {{
  background: {Colors.BG_PANEL};
  border: 1px solid {Colors.BORDER};
  border-radius: 10px;
  padding: 4px;
  display: inline-flex;
  gap: 2px;
  margin-bottom: 18px;
}}

/* --- Headline (manchete) --- */
.ufmg-headline {{
  background: {Colors.BG_PANEL};
  border: 1px solid {Colors.BORDER};
  border-left: 3px solid {Colors.ACCENT};
  border-radius: 10px;
  padding: 20px 24px;
  margin: 6px 0 20px 0;
}}
.ufmg-headline-insight {{
  font-size: 16px;
  font-weight: 500;
  color: {Colors.TEXT_MAIN};
  line-height: 1.45;
  margin-bottom: 14px;
}}
.ufmg-headline-rule {{
  width: 40px;
  height: 2px;
  background: {Colors.BORDER_STRONG};
  margin-bottom: 12px;
}}
.ufmg-headline-number {{
  font-family: {FONT_PRIMARY};
  font-size: 40px;
  font-weight: 700;
  color: {Colors.ACCENT};
  letter-spacing: -0.03em;
  line-height: 1.0;
  margin-bottom: 6px;
}}
.ufmg-headline-sub {{
  font-size: 12px;
  color: {Colors.TEXT_MAIN};
  line-height: 1.5;
  opacity: 0.85;
}}

/* --- KPIs --- */
.kpi-row {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
  margin-bottom: 18px;
}}
.kpi-card {{
  background: {Colors.BG_PANEL};
  border: 1px solid {Colors.BORDER};
  border-radius: 10px;
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}}
.kpi-card .kpi-label {{
  font-family: {FONT_MONO};
  font-size: 10px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: {Colors.TEXT_DIM};
  font-weight: 500;
}}
.kpi-card .kpi-value {{
  font-family: {FONT_PRIMARY};
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: {Colors.TEXT_MAIN};
}}
.kpi-card .kpi-value.accent {{ color: {Colors.ACCENT}; }}
.kpi-card .kpi-value.danger {{ color: {Colors.DANGER}; }}
.kpi-card .kpi-value.success {{ color: {Colors.SUCCESS}; }}
.kpi-card .kpi-value.warning {{ color: {Colors.WARNING}; }}
.kpi-card .kpi-delta {{
  font-family: {FONT_MONO};
  font-size: 11px;
  color: {Colors.TEXT_MUTED};
}}

/* --- Section divider --- */
.section-divider {{
  display: flex;
  align-items: center;
  gap: 14px;
  margin: 26px 0 14px 0;
}}
.section-divider-label {{
  font-family: {FONT_MONO};
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: {Colors.TEXT_DIM};
  white-space: nowrap;
}}
.section-divider-line {{
  flex: 1;
  height: 1px;
  background: {Colors.BORDER};
}}

/* --- Grid 2 colunas --- */
.grid-2 {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}}
@media (max-width: 900px) {{
  .grid-2 {{ grid-template-columns: 1fr; }}
}}

/* --- Chart wrapper --- */
.chart-wrap {{
  background: {Colors.BG_PANEL};
  border: 1px solid {Colors.BORDER};
  border-radius: 10px;
  padding: 16px;
}}
.chart-title {{
  font-size: 14px;
  font-weight: 600;
  color: {Colors.TEXT_MAIN};
  margin: 0 0 10px 0;
}}

/* --- Slider --- */
.prob-slider-wrap {{
  background: {Colors.BG_PANEL};
  border: 1px solid {Colors.BORDER};
  border-radius: 10px;
  padding: 14px 20px;
  margin-bottom: 18px;
}}
.prob-slider-wrap .prob-label {{
  font-family: {FONT_MONO};
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: {Colors.TEXT_DIM};
  font-weight: 500;
  margin-bottom: 6px;
}}
.rc-slider {{ margin: 4px 8px 24px; }}
.rc-slider-track,
.rc-slider-tracks {{ background-color: {Colors.ACCENT} !important; height: 4px !important; }}
.rc-slider-rail {{ background-color: {Colors.BORDER_STRONG} !important; height: 4px !important; }}
.rc-slider-handle,
.rc-slider-handle-1,
.rc-slider-handle-dragging {{
  background-color: {Colors.ACCENT} !important;
  border: 2px solid {Colors.BG_MAIN} !important;
  box-shadow: 0 0 0 3px {Colors.ACCENT} !important;
  opacity: 1 !important;
  width: 14px !important;
  height: 14px !important;
  margin-top: -5px !important;
}}
.rc-slider-mark {{ top: 14px !important; }}
.rc-slider-mark-text {{
  color: {Colors.TEXT_MAIN} !important;
  font-family: {FONT_MONO} !important;
  font-size: 10px !important;
  font-weight: 500 !important;
  letter-spacing: 0.04em;
}}
.rc-slider-mark-text-active {{ color: {Colors.ACCENT} !important; font-weight: 700 !important; }}
.rc-slider-dot {{
  background-color: {Colors.BG_PANEL} !important;
  border-color: {Colors.BORDER_STRONG} !important;
  width: 6px !important; height: 6px !important;
  bottom: -1px !important;
}}
.rc-slider-dot-active {{ border-color: {Colors.ACCENT} !important; }}
.rc-slider-tooltip-inner {{
  background-color: {Colors.BG_ELEV} !important;
  color: {Colors.ACCENT} !important;
  font-family: {FONT_MONO} !important;
  font-size: 11px !important;
  border: 1px solid {Colors.ACCENT} !important;
  box-shadow: none !important;
  padding: 2px 8px !important;
}}
.rc-slider-tooltip-arrow {{ border-bottom-color: {Colors.ACCENT} !important; }}

/* --- Table --- */
.monitor-table {{
  width: 100%;
  border-collapse: collapse;
  font-family: {FONT_MONO};
  font-size: 12px;
}}
.monitor-table th, .monitor-table td {{
  padding: 8px 10px;
  border-bottom: 1px solid {Colors.BORDER};
  text-align: left;
}}
.monitor-table th {{
  color: {Colors.TEXT_DIM};
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}}
.monitor-table td {{
  color: {Colors.TEXT_MAIN};
}}

/* --- Info boxes --- */
.info-box {{
  background: {Colors.BG_PANEL};
  border: 1px solid {Colors.BORDER};
  border-left: 3px solid {Colors.ACCENT};
  border-radius: 10px;
  padding: 14px 18px;
  color: {Colors.TEXT_MUTED};
  font-size: 13px;
  margin: 16px 0;
}}
.warning-box {{
  border-left-color: {Colors.WARNING};
  color: {Colors.WARNING};
}}

/* --- Filtros ativos badge --- */
.active-filters {{
  background: {Colors.BG_PANEL};
  border: 1px solid {Colors.BORDER};
  border-left: 3px solid {Colors.ACCENT};
  border-radius: 8px;
  padding: 8px 14px;
  font-family: {FONT_MONO};
  font-size: 11px;
  color: {Colors.TEXT_MUTED};
  margin-bottom: 14px;
  display: inline-block;
}}

/* --- Caption footer --- */
.monitor-footer-caption {{
  font-size: 12px;
  color: {Colors.TEXT_DIM};
  margin-top: 20px;
  padding-top: 12px;
  border-top: 1px solid {Colors.BORDER};
}}
"""

INDEX_STRING = """<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>""" + GLOBAL_CSS + """</style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""


# ============================================================
# Parse de filtros da URL (sem cache — tem que recomputar por request)
# ============================================================
def _parse_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]


def _parse_date(raw: str | None) -> date | None:
    if not raw:
        return None
    try:
        return pd.Timestamp(raw).date()
    except Exception:
        return None


def parse_filtros_da_url(search: str) -> dict:
    """Parse da query string do dcc.Location.search (ex: '?uf=SP,MG&sub=Golpe')."""
    if not search:
        return {}
    q = parse_qs(search.lstrip("?"), keep_blank_values=False)
    return {
        "ufs": _parse_list(q.get("uf", [None])[0]),
        "escritorios": _parse_list(q.get("esc", [None])[0]),
        "sub_assunto": (q.get("sub", [None])[0] or "Todos"),
        "periodo_from": _parse_date(q.get("from", [None])[0]),
        "periodo_to": _parse_date(q.get("to", [None])[0]),
        "tab": (q.get("tab", [None])[0] or "aderencia"),
        "prob_aceita": float(q.get("prob", ["0.40"])[0] or "0.40"),
    }


# ============================================================
# Factory
# ============================================================
def create_dash_app(flask_server):
    """Monta o Dash app dentro do Flask server recebido.

    Retorna a instância Dash (chamada opcional para debug).
    """
    app = Dash(
        __name__,
        server=flask_server,
        url_base_pathname="/monitoramento/",
        suppress_callback_exceptions=True,
        title="Monitoramento UFMG",
        update_title=None,
    )
    app.index_string = INDEX_STRING

    # Cache em memória (timeout 5min) para leitura pesada dos parquets.
    cache = Cache(app.server, config={
        "CACHE_TYPE": "SimpleCache",
        "CACHE_DEFAULT_TIMEOUT": 300,
    })

    # ------------------------------------------------------------
    # Loaders cacheados
    # ------------------------------------------------------------
    @cache.memoize(timeout=600)
    def load_baseline() -> dict | None:
        try:
            with open(BASELINE_JSON, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    @cache.memoize(timeout=600)
    def load_enriquecidos() -> pd.DataFrame | None:
        path = Path(CASOS_ENRIQUECIDOS)
        if not path.exists():
            return None
        return pd.read_parquet(path)

    @cache.memoize(timeout=600)
    def get_df_com_politica() -> tuple[pd.DataFrame | None, str]:
        df_enr = load_enriquecidos()
        if df_enr is None:
            return None, "indisponivel"
        csv_path = DATA_PROCESSED / "politica_output.csv"
        if csv_path.exists():
            politica = pd.read_csv(csv_path)
            colunas_mock = [
                c for c in ("acao_recomendada", "valor_acordo_recomendado",
                            "score_confianca")
                if c in df_enr.columns
            ]
            df_enr = df_enr.drop(columns=colunas_mock)
            merged = df_enr.merge(politica, on="numero_processo", how="left")
            return merged, "csv"
        return df_enr, "mock"

    # ------------------------------------------------------------
    # Aplicação de filtros
    # ------------------------------------------------------------
    def aplicar_filtros(
        df: pd.DataFrame,
        ufs: list[str],
        escritorios: list[str],
        sub_assunto: str,
        pfrom: date | None,
        pto: date | None,
    ) -> pd.DataFrame:
        if df is None or df.empty:
            return df
        out = df
        if ufs:
            out = out[out["uf"].isin(ufs)]
        if escritorios and "escritorio_id" in out.columns:
            out = out[out["escritorio_id"].isin(escritorios)]
        if sub_assunto and sub_assunto != "Todos" and "sub_assunto" in out.columns:
            out = out[out["sub_assunto"] == sub_assunto]
        if "data_decisao" in out.columns and (pfrom or pto):
            if pfrom:
                out = out[out["data_decisao"] >= pd.Timestamp(pfrom)]
            if pto:
                out = out[
                    out["data_decisao"] <= pd.Timestamp(pto) + pd.Timedelta(days=1)
                ]
        return out

    def _filtros_ativos_str(f: dict) -> str | None:
        partes = []
        if f.get("ufs"):
            partes.append(f"{len(f['ufs'])} UF(s)")
        if f.get("escritorios"):
            partes.append(f"{len(f['escritorios'])} escritório(s)")
        if f.get("sub_assunto") and f["sub_assunto"] != "Todos":
            partes.append(f"sub-assunto: {f['sub_assunto']}")
        if f.get("periodo_from") or f.get("periodo_to"):
            pf = f.get("periodo_from").strftime("%d/%m/%Y") if f.get("periodo_from") else "inicio"
            pt = f.get("periodo_to").strftime("%d/%m/%Y") if f.get("periodo_to") else "hoje"
            partes.append(f"período: {pf} → {pt}")
        if not partes:
            return None
        return "Filtros ativos: " + " · ".join(partes)

    # ============================================================
    # Componentes auxiliares (server-side HTML)
    # ============================================================
    def headline(texto_insight: str, valor_grande: str, subtexto: str | None = None):
        children = [
            html.Div(texto_insight, className="ufmg-headline-insight"),
            html.Div(className="ufmg-headline-rule"),
            html.Div(valor_grande, className="ufmg-headline-number"),
        ]
        if subtexto:
            children.append(html.Div(subtexto, className="ufmg-headline-sub"))
        return html.Div(children, className="ufmg-headline")

    def kpi_card(label: str, valor: str, delta: str | None = None,
                 severidade: str = "neutral"):
        value_cls_map = {
            "critical": "danger", "danger": "danger",
            "warning": "warning", "ok": "success", "success": "success",
            "accent": "accent", "neutral": "",
        }
        cls = value_cls_map.get(severidade, "")
        children = [
            html.Div(label, className="kpi-label"),
            html.Div(valor, className=f"kpi-value {cls}".strip()),
        ]
        if delta:
            children.append(html.Div(delta, className="kpi-delta"))
        return html.Div(children, className="kpi-card")

    def section_divider(titulo: str):
        return html.Div(
            [
                html.Span(titulo, className="section-divider-label"),
                html.Span(className="section-divider-line"),
            ],
            className="section-divider",
        )

    def chart_wrap(titulo: str, fig: go.Figure, graph_id: str | None = None):
        return html.Div(
            [
                html.H3(titulo, className="chart-title"),
                dcc.Graph(
                    id=graph_id or f"g-{abs(hash(titulo)) % 10**8}",
                    figure=fig,
                    config={"displayModeBar": False},
                ),
            ],
            className="chart-wrap",
        )

    def info_box(msg: str, variant: str = ""):
        cls = "info-box" + (f" {variant}" if variant else "")
        return html.Div(msg, className=cls)

    # ============================================================
    # Construtores de gráficos (puros — usam as métricas já existentes)
    # ============================================================
    def _build_drift_fig(df_f: pd.DataFrame) -> go.Figure:
        serie = metrics_adherence.drift_temporal_aderencia(df_f, freq="ME")
        df_drift = serie.reset_index()
        df_drift.columns = ["mes", "aderencia"]
        fig = go.Figure()
        fig.add_hrect(
            y0=TH_ADESAO_ALERTA, y1=TH_ADESAO_OK,
            fillcolor=Colors.ACCENT, opacity=0.08, line_width=0,
            annotation_text="Zona de atenção 70-85%",
            annotation_position="top left",
        )
        fig.add_trace(go.Scatter(
            x=df_drift["mes"], y=df_drift["aderencia"],
            mode="lines+markers",
            line=dict(color=Colors.ACCENT, width=3),
            marker=dict(size=8, color=Colors.ACCENT),
            hovertemplate="<b>%{x|%b/%Y}</b><br>Aderência: %{y:.1%}<extra></extra>",
        ))
        fig.add_hline(y=TH_ADESAO_ALERTA, line_dash="dot",
                      line_color=Colors.DANGER, opacity=0.6)
        fig.add_hline(y=TH_ADESAO_OK, line_dash="dot",
                      line_color=Colors.SUCCESS, opacity=0.6)
        fig.update_layout(
            xaxis_title=None, yaxis_title="Aderência mensal",
            yaxis_tickformat=".0%", yaxis_range=[0.5, 1.0],
            margin=dict(l=10, r=10, t=10, b=10), showlegend=False,
        )
        return _apply_layout(fig, height=340)

    def _build_top_advogados_fig(por_adv: pd.DataFrame) -> go.Figure:
        top_bad = por_adv.head(10).reset_index()
        top_bad = top_bad.sort_values("aderencia", ascending=True)
        top_bad["label"] = top_bad["aderencia"].apply(
            lambda p: f"{p*100:.1f}%".replace(".", ",")
        )
        label_y = (
            top_bad["advogado_nome"] if "advogado_nome" in top_bad.columns
            else top_bad["advogado_id"]
        )
        escritorio_hover = (
            top_bad["escritorio_nome"]
            if "escritorio_nome" in top_bad.columns else top_bad["escritorio"]
        )
        customdata_cols = [escritorio_hover, top_bad["n_casos"]]
        if "numero_oab" in top_bad.columns:
            customdata_cols.append(top_bad["numero_oab"])
            hover_template = (
                "<b>%{y}</b><br>Aderência: %{x:.1%}<br>"
                "Escritório: %{customdata[0]}<br>"
                "OAB: %{customdata[2]}<br>"
                "n casos: %{customdata[1]:,}<extra></extra>"
            )
        else:
            hover_template = (
                "<b>%{y}</b><br>Aderência: %{x:.1%}<br>"
                "Escritório: %{customdata[0]}<br>"
                "n casos: %{customdata[1]:,}<extra></extra>"
            )
        fig = go.Figure(go.Bar(
            x=top_bad["aderencia"], y=label_y, orientation="h",
            marker_color=Colors.DANGER,
            text=top_bad["label"], textposition="outside",
            customdata=list(zip(*customdata_cols)),
            hovertemplate=hover_template,
        ))
        fig.add_vline(
            x=0.60, line_dash="dash", line_color=Colors.DANGER,
            annotation_text="Limite urgente (60%)",
            annotation_position="top right",
            annotation=dict(
                font=dict(size=11, color=Colors.DANGER),
                bgcolor=Colors.BG_PANEL,
                bordercolor=Colors.DANGER,
                borderwidth=1,
                borderpad=3,
                yanchor="bottom",
            ),
        )
        fig.update_layout(
            xaxis_title="Aderência", yaxis_title=None,
            xaxis_tickformat=".0%", xaxis_range=[0, 1.0],
            margin=dict(l=10, r=40, t=28, b=10), showlegend=False,
        )
        return _apply_layout(fig, height=380)

    def _build_escritorio_fig(df_f: pd.DataFrame) -> go.Figure:
        por_esc = metrics_adherence.aderencia_por_escritorio(df_f).reset_index()
        por_esc = por_esc.sort_values("aderencia", ascending=True)
        cores = [
            Colors.SUCCESS if a >= TH_ADESAO_OK
            else Colors.WARNING if a >= TH_ADESAO_ALERTA
            else Colors.DANGER
            for a in por_esc["aderencia"]
        ]
        por_esc["label"] = por_esc["aderencia"].apply(lambda p: f"{p*100:.0f}%")
        label_x = (
            por_esc["escritorio_nome"]
            if "escritorio_nome" in por_esc.columns else por_esc["escritorio_id"]
        )
        customdata_cols = [por_esc["n_casos"], por_esc["n_advogados"]]
        if "cidade_sede" in por_esc.columns:
            customdata_cols.append(por_esc["cidade_sede"])
            hover = (
                "<b>%{x}</b><br>Aderência: %{y:.1%}<br>"
                "Sede: %{customdata[2]}<br>"
                "n casos: %{customdata[0]:,}<br>"
                "n advogados: %{customdata[1]}<extra></extra>"
            )
        else:
            hover = (
                "<b>%{x}</b><br>Aderência: %{y:.1%}<br>"
                "n casos: %{customdata[0]:,}<br>"
                "n advogados: %{customdata[1]}<extra></extra>"
            )
        fig = go.Figure(go.Bar(
            x=label_x, y=por_esc["aderencia"], marker_color=cores,
            text=por_esc["label"], textposition="outside",
            customdata=list(zip(*customdata_cols)), hovertemplate=hover,
        ))
        fig.add_hline(y=TH_ADESAO_OK, line_dash="dot",
                      line_color=Colors.SUCCESS, opacity=0.6)
        fig.add_hline(y=TH_ADESAO_ALERTA, line_dash="dot",
                      line_color=Colors.DANGER, opacity=0.6)
        fig.update_layout(
            xaxis_title=None, yaxis_title="Aderência",
            yaxis_tickformat=".0%", yaxis_range=[0, 1.05],
            margin=dict(l=10, r=10, t=10, b=10), showlegend=False,
        )
        return _apply_layout(fig, height=380)

    # Labels humanizados para razao_override (snake_case -> PT-BR)
    LABEL_RAZOES = {
        "discordancia_score": "Discordância do score",
        "info_nova": "Nova informação do caso",
        "neg_em_andamento": "Negociação em andamento",
        "erro_ferramenta": "Erro da ferramenta",
        "outro": "Outro",
    }

    def _build_razoes_fig(df_f: pd.DataFrame) -> go.Figure | None:
        razoes = metrics_adherence.distribuicao_razoes_override(df_f)
        if razoes.empty:
            return None
        df_raz = razoes.reset_index()
        df_raz.columns = ["razao", "proporcao"]
        df_raz = df_raz.sort_values("proporcao", ascending=True)
        df_raz["label"] = df_raz["proporcao"].apply(
            lambda p: f"{p*100:.1f}%".replace(".", ",")
        )
        # Humaniza nomes mantendo a categoria "discordancia_score" em destaque
        df_raz["razao_label"] = df_raz["razao"].map(LABEL_RAZOES).fillna(df_raz["razao"])
        cores = [
            Colors.DANGER if r == "discordancia_score"
            else Colors.TEXT_MUTED if r == "outro"
            else Colors.ACCENT
            for r in df_raz["razao"]
        ]
        fig = go.Figure(go.Bar(
            x=df_raz["proporcao"], y=df_raz["razao_label"], orientation="h",
            marker_color=cores,
            text=df_raz["label"], textposition="outside",
            hovertemplate="<b>%{y}</b><br>%{x:.1%}<extra></extra>",
        ))
        fig.update_layout(
            xaxis_title="Proporção dos overrides", yaxis_title=None,
            xaxis_tickformat=".0%",
            margin=dict(l=10, r=40, t=10, b=10), showlegend=False,
        )
        return _apply_layout(fig, height=340)

    def _build_faixa_valor_fig(df_f: pd.DataFrame) -> go.Figure:
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
        cores = [
            Colors.SUCCESS if a >= TH_ADESAO_OK
            else Colors.WARNING if a >= TH_ADESAO_ALERTA
            else Colors.DANGER
            for a in por_fx["aderencia"]
        ]
        fig = go.Figure(go.Bar(
            x=por_fx["faixa_valor"].astype(str),
            y=por_fx["aderencia"], marker_color=cores,
            text=por_fx["label"], textposition="outside",
        ))
        fig.add_hline(
            y=TH_ADESAO_ALERTA, line_dash="dot",
            line_color=Colors.DANGER, opacity=0.6,
            annotation_text="Limite urgente (70%)", annotation_position="right",
        )
        fig.update_layout(
            xaxis_title="Faixa de valor da causa", yaxis_title="Aderência",
            yaxis_tickformat=".0%", yaxis_range=[0, 1.05],
            margin=dict(l=10, r=40, t=10, b=10), showlegend=False,
        )
        return _apply_layout(fig, height=320)

    def _build_faixa_completude_fig(df_f: pd.DataFrame) -> go.Figure:
        por_cp = metrics_adherence.aderencia_por_faixa_completude(df_f).reset_index()
        por_cp.columns = ["faixa_completude", "aderencia"]
        ordem = ["Frágil", "Parcial", "Sólida"]
        por_cp["faixa_completude"] = pd.Categorical(
            por_cp["faixa_completude"], categories=ordem, ordered=True,
        )
        por_cp = por_cp.sort_values("faixa_completude")
        por_cp["label"] = por_cp["aderencia"].apply(
            lambda p: f"{p*100:.1f}%".replace(".", ",")
        )
        cores = [
            Colors.SUCCESS if a >= TH_ADESAO_OK
            else Colors.WARNING if a >= TH_ADESAO_ALERTA
            else Colors.DANGER
            for a in por_cp["aderencia"]
        ]
        fig = go.Figure(go.Bar(
            x=por_cp["faixa_completude"].astype(str), y=por_cp["aderencia"],
            marker_color=cores, text=por_cp["label"], textposition="outside",
        ))
        fig.update_layout(
            xaxis_title="Completude probatória", yaxis_title="Aderência",
            yaxis_tickformat=".0%", yaxis_range=[0, 1.05],
            margin=dict(l=10, r=40, t=10, b=10), showlegend=False,
        )
        return _apply_layout(fig, height=320)

    def _build_uf_fig(df_f: pd.DataFrame) -> go.Figure:
        por_uf = metrics_adherence.aderencia_por_uf(df_f).reset_index()
        por_uf.columns = ["uf", "aderencia"]
        por_uf = por_uf.sort_values("aderencia")
        por_uf["label"] = por_uf["aderencia"].apply(
            lambda p: f"{p*100:.1f}%".replace(".", ",")
        )
        cores = [
            Colors.SUCCESS if a >= TH_ADESAO_OK
            else Colors.WARNING if a >= TH_ADESAO_ALERTA
            else Colors.DANGER
            for a in por_uf["aderencia"]
        ]
        fig = go.Figure(go.Bar(
            x=por_uf["aderencia"], y=por_uf["uf"], orientation="h",
            marker_color=cores, text=por_uf["label"], textposition="outside",
        ))
        fig.update_layout(
            xaxis_title="Aderência", yaxis_title=None,
            xaxis_tickformat=".0%", xaxis_range=[0, 1.0],
            margin=dict(l=10, r=40, t=10, b=10), showlegend=False,
        )
        return _apply_layout(fig, height=360)

    def _build_sensibilidade_fig(df_f: pd.DataFrame, prob_aceita: float,
                                 sim_potencial: dict) -> go.Figure:
        probs_varredura = [round(p, 2) for p in np.arange(0.10, 0.96, 0.05)]
        df_sens = counterfactual.simular_sensibilidade(
            df_f,
            acao_col="acao_recomendada",
            valor_acordo_col="valor_acordo_recomendado",
            probs=probs_varredura,
        )
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_sens["prob_aceita_assumida"], y=df_sens["economia_total"],
            mode="lines+markers",
            line=dict(color=Colors.ACCENT, width=3),
            marker=dict(size=6, color=Colors.ACCENT),
            name="Economia potencial",
            hovertemplate="prob_aceita=%{x:.2f}<br>Economia: R$ %{y:,.0f}<extra></extra>",
        ))
        mask_slider = np.isclose(df_sens["prob_aceita_assumida"], prob_aceita)
        if mask_slider.any():
            economia_ativa = float(df_sens.loc[mask_slider, "economia_total"].iloc[0])
        else:
            economia_ativa = float(sim_potencial["economia_total"])
        fig.add_trace(go.Scatter(
            x=[prob_aceita], y=[economia_ativa],
            mode="markers",
            marker=dict(size=18, color=Colors.ACCENT, symbol="star",
                        line=dict(width=2, color=Colors.ACCENT_HOVER)),
            name="Slider atual",
            hovertemplate=(
                "<b>Slider atual</b><br>"
                "prob_aceita=%{x:.2f}<br>"
                "Economia: R$ %{y:,.0f}<extra></extra>"
            ),
        ))
        fig.update_layout(
            xaxis_title="Probabilidade de aceitação do acordo",
            yaxis_title="Economia total (R$)",
            margin=dict(l=10, r=10, t=10, b=10),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02,
                        xanchor="right", x=1.0),
        )
        return _apply_layout(fig, height=340)

    def _build_economia_temporal_fig(df_f: pd.DataFrame,
                                     prob_aceita: float) -> go.Figure | None:
        df_temp = metrics_effectiveness.economia_acumulada_temporal(
            df_f,
            acao_col="acao_recomendada",
            valor_acordo_col="valor_acordo_recomendado",
            prob_aceita=prob_aceita,
            data_col="data_decisao",
        )
        if df_temp.empty:
            return None
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_temp["mes"], y=df_temp["economia_acumulada"],
            mode="lines", fill="tozeroy",
            line=dict(color=Colors.ACCENT, width=3),
            fillcolor="rgba(255,174,53,0.18)", name="Acumulada",
            hovertemplate="<b>%{x}</b><br>Acumulada: R$ %{y:,.0f}<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=df_temp["mes"], y=df_temp["economia_mes"],
            mode="lines+markers",
            line=dict(color=Colors.SUCCESS, width=2, dash="dot"),
            marker=dict(size=6, color=Colors.SUCCESS), name="Mensal",
            hovertemplate="<b>%{x}</b><br>Mês: R$ %{y:,.0f}<extra></extra>",
        ))
        fig.update_layout(
            xaxis_title=None, yaxis_title="Economia (R$)",
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02,
                        xanchor="right", x=1.0),
        )
        return _apply_layout(fig, height=340)

    def _build_redistribuicao_fig(df_f: pd.DataFrame, baseline: dict | None,
                                  prob_aceita: float) -> go.Figure:
        df_redist = metrics_effectiveness.redistribuicao_resultado_micro(
            df_f,
            baseline=baseline,
            acao_col="acao_recomendada",
            prob_aceita=prob_aceita,
        )
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_redist["resultado_micro"], y=df_redist["antes_pct"],
            name="Antes (baseline)", marker_color=Colors.TEXT_MUTED,
            hovertemplate="<b>%{x}</b><br>Antes: %{y:.1%}<extra></extra>",
        ))
        fig.add_trace(go.Bar(
            x=df_redist["resultado_micro"], y=df_redist["depois_pct"],
            name="Depois (política)", marker_color=Colors.ACCENT,
            hovertemplate="<b>%{x}</b><br>Depois: %{y:.1%}<extra></extra>",
        ))
        fig.update_layout(
            barmode="group", xaxis_title=None, yaxis_title="Proporção",
            yaxis_tickformat=".0%",
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02,
                        xanchor="right", x=1.0),
        )
        return _apply_layout(fig, height=340)

    def _build_custo_completude_fig(df_f: pd.DataFrame, prob_aceita: float) -> go.Figure | None:
        df_cp = metrics_effectiveness.custo_por_faixa_completude(
            df_f,
            acao_col="acao_recomendada",
            valor_acordo_col="valor_acordo_recomendado",
            prob_aceita=prob_aceita,
        )
        if df_cp.empty:
            return None
        df_cp = df_cp.copy()
        df_cp["custo_medio_obs"] = df_cp["custo_observado"] / df_cp["n_casos"]
        df_cp["custo_medio_pol"] = df_cp["custo_politica"] / df_cp["n_casos"]
        ordem = ["Frágil", "Parcial", "Sólida"]
        df_cp["faixa_completude"] = pd.Categorical(
            df_cp["faixa_completude"], categories=ordem, ordered=True,
        )
        df_cp = df_cp.sort_values("faixa_completude")

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_cp["faixa_completude"].astype(str),
            y=df_cp["custo_medio_obs"], name="Observado (baseline)",
            marker_color=Colors.TEXT_MUTED,
            hovertemplate="<b>%{x}</b><br>Observado: R$ %{y:,.0f}<extra></extra>",
        ))
        fig.add_trace(go.Bar(
            x=df_cp["faixa_completude"].astype(str),
            y=df_cp["custo_medio_pol"], name="Sob política",
            marker_color=Colors.ACCENT,
            hovertemplate="<b>%{x}</b><br>Política: R$ %{y:,.0f}<extra></extra>",
        ))
        fig.update_layout(
            barmode="group",
            xaxis_title="Completude probatória",
            yaxis_title="Custo médio por caso (R$)",
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02,
                        xanchor="right", x=1.0),
        )
        return _apply_layout(fig, height=340)

    def _build_histograma_acordos_fig(df_f: pd.DataFrame) -> go.Figure | None:
        acordos_feitos = df_f[
            (df_f["acao_tomada"] == "acordo")
            & df_f["valor_acordo_proposto"].notna()
        ].copy()
        if acordos_feitos.empty:
            return None
        acordos_feitos["ratio"] = (
            acordos_feitos["valor_acordo_proposto"] / acordos_feitos["valor_causa"]
        )
        fig = go.Figure(go.Histogram(
            x=acordos_feitos["ratio"], nbinsx=30,
            marker_color=Colors.ACCENT,
            hovertemplate="Ratio: %{x:.2f}<br>n: %{y}<extra></extra>",
        ))
        fig.add_vline(
            x=0.30, line_dash="dash", line_color=Colors.SUCCESS,
            annotation_text="30% (política)",
            annotation_position="top right",
            annotation=dict(
                font=dict(size=11, color=Colors.SUCCESS),
                bgcolor=Colors.BG_PANEL,
                bordercolor=Colors.SUCCESS,
                borderwidth=1,
                borderpad=3,
                yanchor="bottom",
            ),
        )
        fig.update_layout(
            xaxis_title="Valor do acordo / valor da causa",
            yaxis_title="Número de acordos",
            margin=dict(l=10, r=10, t=28, b=10), showlegend=False,
        )
        return _apply_layout(fig, height=320)

    # ============================================================
    # Render · Aba Aderência
    # ============================================================
    def render_aderencia(filtros: dict) -> list:
        df_pol, fonte = get_df_com_politica()
        if df_pol is None:
            return [info_box(
                "Dataset enriquecido ainda não disponível. "
                "Execute `python -m src.monitor.gerar_sintetico` para gerar.",
                variant="warning-box",
            )]

        df_f = aplicar_filtros(
            df_pol, filtros.get("ufs", []), filtros.get("escritorios", []),
            filtros.get("sub_assunto", "Todos"),
            filtros.get("periodo_from"), filtros.get("periodo_to"),
        )

        # Banner "Filtros ativos" removido — o React (sidebar da plataforma)
        # já mostra os filtros ativos de forma centralizada.
        filtros_row: list = []

        if df_f is None or len(df_f) == 0:
            return filtros_row + [info_box(
                "Nenhum caso após aplicar os filtros. Ajuste a seleção.",
                variant="warning-box",
            )]

        # métricas base
        tsg = metrics_adherence.taxa_seguimento_global(df_f)
        tov = metrics_adherence.taxa_override(df_f)
        adh_pond = metrics_adherence.aderencia_ponderada_por_valor(df_f)
        gap_pond = adh_pond - tsg

        por_adv = metrics_adherence.aderencia_por_advogado(df_f)
        criticos = por_adv[por_adv["aderencia"] < 0.60]
        n_criticos = int(len(criticos))
        n_escr_criticos = int(criticos["escritorio"].nunique()) if n_criticos else 0

        if n_criticos > 0:
            ids_crit = criticos.index.tolist()
            valor_crit = float(
                df_f.loc[df_f["advogado_id"].isin(ids_crit), "valor_causa"].sum()
            )
            valor_tot = float(df_f["valor_causa"].sum())
            pct_risco = valor_crit / valor_tot if valor_tot > 0 else 0.0
        else:
            pct_risco = 0.0

        overrides = df_f.loc[df_f["aderente"] == 0, "razao_override"]
        n_over = int(overrides.notna().sum())
        if n_over > 0:
            n_justif = int(
                overrides.isin(
                    ["info_nova", "neg_em_andamento", "erro_ferramenta"]
                ).sum()
            )
            pct_justif = n_justif / n_over
        else:
            pct_justif = 0.0

        # HERO — título técnico objetivo (padrão catálogo)
        insight = "A01 · Taxa de Seguimento Global"
        if n_criticos > 0 and n_escr_criticos > 0:
            subtxt = (
                f"{n_criticos} advogado(s) crítico(s) em {n_escr_criticos} "
                f"escritório(s) · {pct_risco*100:.0f}% do risco financeiro · "
                f"{fmt_int_br(n_over)} override(s) ({pct_justif*100:.0f}% justificados)"
            )
        else:
            subtxt = f"{fmt_int_br(n_over)} override(s) · nenhum advogado crítico (<60%)"

        # KPIs
        gap_delta = f"{gap_pond*100:+.1f} pp vs seguimento".replace(".", ",")

        # Subtexto descritivo cru: "N de M casos seguiram a política"
        n_aderente = int(df_f["aderente"].sum())
        n_total = int(len(df_f))
        n_override = int(n_total - n_aderente)

        kpi_row = html.Div([
            kpi_card(
                "A01 · Taxa de Seguimento",
                fmt_pct(tsg),
                delta=f"{fmt_int_br(n_aderente)} de {fmt_int_br(n_total)} casos seguiram a recomendação",
                severidade="accent",
            ),
            kpi_card(
                "A02 · Taxa de Override",
                fmt_pct(tov),
                delta=f"{fmt_int_br(n_override)} casos em que o advogado desviou da política",
            ),
            kpi_card(
                "A13 · Overrides Justificados",
                fmt_pct(pct_justif),
                delta="info nova, negociação ou erro da ferramenta",
            ),
        ], className="kpi-row")

        # gráficos principais
        fig_drift = _build_drift_fig(df_f)
        fig_adv = _build_top_advogados_fig(por_adv)
        fig_esc = _build_escritorio_fig(df_f)

        charts_prova = html.Div([
            chart_wrap("A18 · Drift Temporal de Aderência", fig_drift, "fig-drift"),
            html.Div([
                chart_wrap("A05 · Aderência por Advogado (bottom 10)", fig_adv, "fig-adv"),
                chart_wrap("A06 · Aderência por Escritório", fig_esc, "fig-esc"),
            ], className="grid-2"),
        ])

        # exploração
        fig_razoes = _build_razoes_fig(df_f)
        razoes_section = (
            chart_wrap("A13 · Distribuição de Razões de Override", fig_razoes, "fig-razoes")
            if fig_razoes is not None
            else info_box("Nenhum override no recorte atual.")
        )

        fig_faixa = _build_faixa_valor_fig(df_f)
        fig_compl = _build_faixa_completude_fig(df_f)
        fig_uf = _build_uf_fig(df_f)

        alertas = metrics_adherence.alertas_ativos(df_f)
        if alertas:
            linhas_al = [
                html.Tr([
                    html.Th("ID"), html.Th("Métrica"),
                    html.Th("Valor"), html.Th("Threshold"), html.Th("Mensagem"),
                ])
            ]
            for a in alertas:
                linhas_al.append(html.Tr([
                    html.Td(a["id"]), html.Td(a["nome"]),
                    html.Td(fmt_pct(a["valor"])),
                    html.Td(fmt_pct(a["threshold"])),
                    html.Td(a["mensagem"]),
                ]))
            alertas_section = html.Div([
                html.H3(
                    f"Alertas urgentes — {len(alertas)} ativo(s)",
                    className="chart-title",
                ),
                html.Table(linhas_al, className="monitor-table"),
            ], className="chart-wrap")
        else:
            alertas_section = info_box("Nenhum alerta urgente no recorte atual.")

        return filtros_row + [
            headline(insight, fmt_pct(tsg), subtxt),
            kpi_row,
            section_divider("Métricas principais"),
            charts_prova,
            section_divider("Segmentações e alertas"),
            razoes_section,
            html.Div([
                chart_wrap("A08 · Aderência por Faixa de Valor", fig_faixa, "fig-faixa"),
                chart_wrap("A04 · Aderência por Completude", fig_compl, "fig-compl"),
            ], className="grid-2"),
            chart_wrap("A07 · Aderência por UF", fig_uf, "fig-uf"),
            alertas_section,
            html.Div(
                f"Fonte: {fonte.upper()}",
                className="monitor-footer-caption",
            ),
        ]

    # ============================================================
    # Render · Aba Efetividade
    # ============================================================
    def render_efetividade(filtros: dict, prob_aceita: float) -> list:
        baseline = load_baseline()
        df_pol, fonte = get_df_com_politica()
        if df_pol is None:
            return [info_box(
                "Dataset enriquecido ainda não disponível. "
                "Execute `python -m src.monitor.gerar_sintetico` para gerar.",
                variant="warning-box",
            )]

        df_f = aplicar_filtros(
            df_pol, filtros.get("ufs", []), filtros.get("escritorios", []),
            filtros.get("sub_assunto", "Todos"),
            filtros.get("periodo_from"), filtros.get("periodo_to"),
        )

        # Banner "Filtros ativos" removido — o React (sidebar da plataforma)
        # já mostra os filtros ativos de forma centralizada.
        filtros_row: list = []

        if df_f is None or len(df_f) == 0:
            return filtros_row + [info_box(
                "Nenhum caso após aplicar os filtros. Ajuste a seleção.",
                variant="warning-box",
            )]

        # Simulação dos cenários
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

        # HERO — explícito: o valor grande É a economia MÁXIMA possível
        # se todos seguissem a política. Texto cru, sem ambiguidade.
        custo_obs = sim_potencial["custo_observado_total"]
        insight = "E02 · Teto de economia anual vs custo atual"
        subtxt = (
            f"Se 100% dos advogados seguirem a política "
            f"(acordo aceito por {prob_aceita:.0%} dos autores), "
            f"o banco deixa de pagar este valor dos "
            f"{fmt_brl_compact(custo_obs)} gastos hoje."
        )

        # KPIs com descrição do que cada número É
        k1 = kpi_card(
            "E02 · Teto de economia (aderência 100%)",
            fmt_brl_compact(sim_potencial["economia_total"]),
            delta=f"{fmt_pct(sim_potencial['economia_percentual'])} dos {fmt_brl_compact(custo_obs)} gastos hoje",
            severidade="accent",
        )
        k2 = kpi_card(
            "E03 · Economia realizada no recorte",
            fmt_brl_compact(sim_realizada["economia_total"]),
            delta=f"resultado se os advogados agirem como agiram na amostra",
        )
        k3 = kpi_card(
            "Δ · Perda por não-aderência",
            fmt_brl_compact(gap_rs),
            delta=f"{gap_pct*100:.0f}% do teto deixado sobre a mesa pelos overrides".replace(".", ","),
            severidade="danger",
        )
        kpi_row = html.Div([k1, k2, k3], className="kpi-row")

        # Gráficos
        fig_sens = _build_sensibilidade_fig(df_f, prob_aceita, sim_potencial)
        fig_temp = _build_economia_temporal_fig(df_f, prob_aceita)
        fig_red = _build_redistribuicao_fig(df_f, baseline, prob_aceita)

        temp_section = (
            chart_wrap("E10 · Economia Acumulada Temporal", fig_temp, "fig-temp")
            if fig_temp is not None
            else info_box("Sem dados temporais no recorte atual.")
        )

        # Exploração
        fig_cp = _build_custo_completude_fig(df_f, prob_aceita)
        fig_hist = _build_histograma_acordos_fig(df_f)

        cp_section = (
            chart_wrap("E06 · Custo Médio por Completude", fig_cp, "fig-cp")
            if fig_cp is not None
            else info_box("Sem dados no recorte atual.")
        )
        hist_section = (
            chart_wrap("E11 · Distribuição de Valores de Acordo",
                       fig_hist, "fig-hist")
            if fig_hist is not None
            else info_box("Sem acordos realizados no recorte atual.")
        )

        # Tabela de detalhes
        linhas_det = [
            ("Casos no recorte", fmt_int_br(len(df_f))),
            ("Economia potencial", fmt_brl(sim_potencial["economia_total"], casas=0)),
            ("Economia realizada", fmt_brl(sim_realizada["economia_total"], casas=0)),
            ("Gap (R$)", fmt_brl(gap_rs, casas=0)),
            ("Gap (%)", fmt_pct(gap_pct)),
            ("prob_aceita assumida", f"{prob_aceita:.0%}"),
        ]
        det_rows = [html.Tr([html.Th("Métrica"), html.Th("Valor")])]
        for k, v in linhas_det:
            det_rows.append(html.Tr([html.Td(k), html.Td(v)]))
        det_section = html.Div([
            html.H3("Detalhes dos cenários", className="chart-title"),
            html.Table(det_rows, className="monitor-table"),
        ], className="chart-wrap")

        # Slider vive no React (sidebar da plataforma) — aqui só consumimos
        # o valor via URL query string.
        return filtros_row + [
            headline(insight, fmt_brl_compact(economia_potencial), subtxt),
            kpi_row,
            section_divider("Métricas principais"),
            chart_wrap("E02 · Sensibilidade × prob_aceita",
                       fig_sens, "fig-sens"),
            html.Div([
                temp_section,
                chart_wrap("E09 · Distribuição de Resultado Micro",
                           fig_red, "fig-red"),
            ], className="grid-2"),
            section_divider("Drill-down"),
            html.Div([cp_section, hist_section], className="grid-2"),
            det_section,
            html.Div(
                f"Fonte: {fonte.upper()} · prob_aceita: {prob_aceita:.0%}",
                className="monitor-footer-caption",
            ),
        ]

    # ============================================================
    # Layout (casca minima) — só o container; conteudo via callback.
    # Header, tabs e filtros ficam na plataforma React (sidebar).
    # O Dash recebe tab + filtros via URL query string.
    # ============================================================
    app.layout = html.Div([
        dcc.Location(id="monitor-url", refresh=False),
        html.Div(id="monitor-content", className="monitor-root"),
    ])

    # ============================================================
    # Callbacks — a tab vem da URL (?tab=...), controlada pelo React
    # ============================================================
    @app.callback(
        Output("monitor-content", "children"),
        Input("monitor-url", "search"),
    )
    def _render_tab(search: str):
        filtros = parse_filtros_da_url(search or "")
        tab_value = filtros.get("tab", "aderencia")
        if tab_value == "efetividade":
            return render_efetividade(filtros, filtros.get("prob_aceita", 0.40))
        return render_aderencia(filtros)

    # Slider, tabs e filtros são controlados exclusivamente pelo React
    # via URL query string — o Dash observa dcc.Location apenas.
    return app
