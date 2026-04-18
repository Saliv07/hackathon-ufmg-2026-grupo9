"""
Tema Banco UFMG · tokens + CSS override para o Streamlit.

Fonte única da verdade do design: frontend/src/index.css + Dashboard.css
(plataforma do advogado, já integrada no branch principal).

Este módulo expõe:
    - Classes `Colors`, `Fonts`, `Sizes` com tokens hex / px.
    - Dict `SEVERITY_COLORS` para mapear severidade -> cor.
    - Helpers de formatação pt-BR (fmt_brl, fmt_brl_compact, fmt_int_br, fmt_pct).
    - `get_global_css()` e `apply_theme()` para injetar os overrides Streamlit.

Chame `apply_theme()` UMA vez, logo após `st.set_page_config(...)`.
"""
from __future__ import annotations

import numpy as np
import streamlit as st


# ============================================================
# Tokens — fonte da verdade: frontend/src/index.css
# ============================================================
class Colors:
    # Fundos
    BG_MAIN = "#000000"
    BG_PANEL = "#0a0a0a"
    BG_SIDEBAR = "#050505"
    BG_ELEV = "#111111"
    # Texto
    TEXT_MAIN = "#ffffff"
    TEXT_MUTED = "#a1a1a1"
    TEXT_DIM = "#666666"
    # Accent (laranja UFMG — primary em TUDO interativo)
    ACCENT = "#FFAE35"
    ACCENT_HOVER = "#e69d30"
    # Severidade
    SUCCESS = "#4CAF50"
    WARNING = "#ff9800"
    DANGER = "#f44336"
    # Bordas
    BORDER = "#1a1a1a"
    BORDER_STRONG = "#262626"
    # Neutros auxiliares (derivados, para gráficos comparativos)
    NEUTRAL = "#7F8C8D"


class Fonts:
    PRIMARY = "'Inter', 'Segoe UI', system-ui, sans-serif"
    MONO = "'JetBrains Mono', monospace"


class Sizes:
    LABEL_MONO = 11        # px — label/caption mono
    BODY = 14              # px
    H3_CARD = 13           # px 600
    H2_SECTION = 16        # px 600
    H1_TITLE = 26          # px 600
    KPI_BIG = 28           # px 700
    HEADLINE_NUMBER = 52   # px 700 — número da manchete
    HEADLINE_TEXT = 20     # px — insight da manchete
    RADIUS_SM = 6          # px — botões, badges
    RADIUS_MD = 10         # px — cards
    RADIUS_LG = 12         # px — modais


# Mapeamento padronizado para qualquer componente que receba
# `severidade: str`. Fallback = neutral.
SEVERITY_COLORS: dict[str, str] = {
    "critical": Colors.DANGER,
    "danger": Colors.DANGER,
    "warning": Colors.WARNING,
    "attention": Colors.WARNING,
    "ok": Colors.SUCCESS,
    "success": Colors.SUCCESS,
    "accent": Colors.ACCENT,
    "neutral": Colors.TEXT_MUTED,
}


# ============================================================
# Helpers de formatação (movidos de app.py — API preservada)
# ============================================================
def fmt_brl(valor: float, casas: int = 2) -> str:
    """Formata número como R$ brasileiro: milhar com '.', decimal com ','."""
    if valor is None or (isinstance(valor, float) and np.isnan(valor)):
        return "—"
    sinal = "-" if valor < 0 else ""
    valor = abs(valor)
    txt = f"{valor:,.{casas}f}"
    txt = txt.replace(",", "§").replace(".", ",").replace("§", ".")
    return f"{sinal}R$ {txt}"


def fmt_brl_compact(valor: float) -> str:
    """R$ compacto: 1,2B / 17,3M / 850K / 420. Usado em KPIs grandes."""
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


# Alias para retrocompatibilidade com quem chamava fmt_brl_curto.
fmt_brl_curto = fmt_brl_compact


def fmt_int_br(valor: int) -> str:
    if valor is None:
        return "—"
    return f"{int(valor):,}".replace(",", ".")


def fmt_pct(valor: float, casas: int = 1) -> str:
    if valor is None or (isinstance(valor, float) and np.isnan(valor)):
        return "—"
    return f"{valor*100:.{casas}f}%".replace(".", ",")


# ============================================================
# CSS global — overrides do Streamlit + classes utilitárias
# ============================================================
def get_global_css() -> str:
    """Retorna um bloco <style>...</style> pronto para `st.markdown`."""
    return f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

  /* ─── App base ─────────────────────────────────────────── */
  html, body, [data-testid="stAppViewContainer"], .stApp {{
    background-color: {Colors.BG_MAIN} !important;
    color: {Colors.TEXT_MAIN} !important;
    font-family: {Fonts.PRIMARY} !important;
    -webkit-font-smoothing: antialiased;
  }}

  /* Conteúdo principal respira um pouco mais */
  .main .block-container {{
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1400px;
  }}

  /* ─── Tipografia ───────────────────────────────────────── */
  h1, .stMarkdown h1 {{
    font-family: {Fonts.PRIMARY} !important;
    font-size: {Sizes.H1_TITLE}px !important;
    font-weight: 600 !important;
    letter-spacing: -0.02em;
    color: {Colors.TEXT_MAIN} !important;
    margin-bottom: 6px;
  }}
  h2, .stMarkdown h2 {{
    font-family: {Fonts.PRIMARY} !important;
    font-size: {Sizes.H2_SECTION}px !important;
    font-weight: 600 !important;
    color: {Colors.TEXT_MAIN} !important;
    letter-spacing: -0.01em;
  }}
  h3, .stMarkdown h3 {{
    font-family: {Fonts.PRIMARY} !important;
    font-size: {Sizes.H3_CARD}px !important;
    font-weight: 600 !important;
    color: {Colors.TEXT_MAIN} !important;
  }}
  p, li, span, label, .stMarkdown, .stCaption {{
    font-family: {Fonts.PRIMARY};
    color: {Colors.TEXT_MAIN};
  }}
  .stCaption, [data-testid="stCaptionContainer"] {{
    color: {Colors.TEXT_MUTED} !important;
    font-size: 12px !important;
  }}

  /* ─── Sidebar ──────────────────────────────────────────── */
  section[data-testid="stSidebar"] {{
    background-color: {Colors.BG_SIDEBAR} !important;
    border-right: 1px solid {Colors.BORDER};
  }}
  section[data-testid="stSidebar"] * {{
    color: {Colors.TEXT_MAIN};
  }}
  section[data-testid="stSidebar"] .stMarkdown h1,
  section[data-testid="stSidebar"] .stMarkdown h2 {{
    font-size: 15px !important;
    letter-spacing: 0.02em;
  }}
  section[data-testid="stSidebar"] hr {{
    border-color: {Colors.BORDER} !important;
  }}

  /* Título "Monitoramento" — força uma linha só (sem wrap) */
  section[data-testid="stSidebar"] .ufmg-sidebar-title {{
    font-family: {Fonts.PRIMARY} !important;
    font-size: 19px !important;
    font-weight: 700 !important;
    letter-spacing: -0.01em;
    color: {Colors.TEXT_MAIN} !important;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin: 4px 0 14px 0;
  }}

  /* ─── Radio de navegação como "pills" ──────────────────── */
  /* Esconde os círculos nativos e transforma os labels em botões */
  section[data-testid="stSidebar"] .ufmg-nav-radio + div [role="radiogroup"] {{
    display: flex;
    flex-direction: row;
    gap: 6px;
    background: {Colors.BG_PANEL};
    border: 1px solid {Colors.BORDER};
    border-radius: {Sizes.RADIUS_MD}px;
    padding: 4px;
  }}
  section[data-testid="stSidebar"] .ufmg-nav-radio + div [role="radiogroup"] label {{
    flex: 1;
    margin: 0 !important;
    padding: 8px 12px;
    border-radius: {Sizes.RADIUS_SM}px;
    cursor: pointer;
    text-align: center;
    transition: all 0.15s ease;
    color: {Colors.TEXT_MUTED} !important;
    font-family: {Fonts.PRIMARY};
    font-size: 13px;
    font-weight: 500;
  }}
  /* Esconde o círculo nativo mantendo o label clicável */
  section[data-testid="stSidebar"] .ufmg-nav-radio + div [role="radiogroup"] label > div:first-child {{
    display: none !important;
  }}
  section[data-testid="stSidebar"] .ufmg-nav-radio + div [role="radiogroup"] label:hover {{
    background: {Colors.BG_ELEV};
    color: {Colors.ACCENT} !important;
  }}
  section[data-testid="stSidebar"] .ufmg-nav-radio + div [role="radiogroup"] label:has(input:checked) {{
    background: {Colors.BG_ELEV};
    color: {Colors.ACCENT} !important;
    border: 1px solid rgba(255, 174, 53, 0.35);
  }}

  /* ─── KPI / metric ─────────────────────────────────────── */
  [data-testid="stMetric"] {{
    background: {Colors.BG_PANEL};
    border: 1px solid {Colors.BORDER};
    border-radius: {Sizes.RADIUS_MD}px;
    padding: 16px 18px;
  }}
  [data-testid="stMetricLabel"] {{
    font-family: {Fonts.MONO} !important;
    font-size: {Sizes.LABEL_MONO}px !important;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: {Colors.TEXT_DIM} !important;
    font-weight: 500;
  }}
  [data-testid="stMetricValue"] {{
    font-family: {Fonts.PRIMARY} !important;
    font-size: {Sizes.KPI_BIG}px !important;
    font-weight: 700 !important;
    color: {Colors.TEXT_MAIN} !important;
    letter-spacing: -0.02em;
  }}
  [data-testid="stMetricDelta"] {{
    font-family: {Fonts.MONO} !important;
    font-size: 11px !important;
  }}

  /* ─── Tabs ─────────────────────────────────────────────── */
  .stTabs [data-baseweb="tab-list"] {{
    gap: 2px;
    background: {Colors.BG_PANEL};
    border: 1px solid {Colors.BORDER};
    border-radius: {Sizes.RADIUS_MD}px;
    padding: 4px;
  }}
  .stTabs [data-baseweb="tab"] {{
    background: transparent;
    color: {Colors.TEXT_MUTED};
    border-radius: {Sizes.RADIUS_SM}px;
    padding: 8px 16px;
    font-family: {Fonts.PRIMARY};
    font-weight: 500;
  }}
  .stTabs [aria-selected="true"] {{
    background: {Colors.BG_ELEV} !important;
    color: {Colors.ACCENT} !important;
    border-bottom: 2px solid {Colors.ACCENT} !important;
  }}

  /* ─── Botões / inputs / selects ────────────────────────── */
  .stButton > button {{
    background: {Colors.BG_ELEV};
    color: {Colors.TEXT_MAIN};
    border: 1px solid {Colors.BORDER_STRONG};
    border-radius: {Sizes.RADIUS_SM}px;
    font-family: {Fonts.PRIMARY};
    font-weight: 500;
    transition: all 0.15s ease;
  }}
  .stButton > button:hover {{
    border-color: {Colors.ACCENT};
    color: {Colors.ACCENT};
  }}
  .stSelectbox > div > div, .stMultiSelect > div > div,
  [data-baseweb="select"] > div {{
    background-color: {Colors.BG_ELEV} !important;
    border-color: {Colors.BORDER_STRONG} !important;
    color: {Colors.TEXT_MAIN} !important;
  }}
  .stSlider [data-baseweb="slider"] > div > div {{
    background-color: {Colors.ACCENT} !important;
  }}
  .stSlider [role="slider"] {{
    background-color: {Colors.ACCENT} !important;
    border: 2px solid {Colors.ACCENT_HOVER} !important;
  }}
  .stRadio label, .stCheckbox label {{
    color: {Colors.TEXT_MAIN} !important;
  }}

  /* ─── Expander ─────────────────────────────────────────── */
  [data-testid="stExpander"] {{
    background: {Colors.BG_PANEL};
    border: 1px solid {Colors.BORDER};
    border-radius: {Sizes.RADIUS_MD}px;
  }}
  [data-testid="stExpander"] summary {{
    color: {Colors.TEXT_MAIN} !important;
    font-family: {Fonts.PRIMARY};
    font-weight: 500;
  }}
  [data-testid="stExpander"] summary:hover {{
    color: {Colors.ACCENT} !important;
  }}

  /* ─── Alert boxes (info/warning/success/error) ─────────── */
  [data-testid="stAlert"] {{
    border-radius: {Sizes.RADIUS_MD}px;
    border-left-width: 3px;
    background: {Colors.BG_PANEL} !important;
  }}

  /* ─── Divider ──────────────────────────────────────────── */
  hr {{
    border-color: {Colors.BORDER} !important;
    margin: 1.5rem 0 !important;
  }}

  /* ─── DataFrame / table ────────────────────────────────── */
  [data-testid="stDataFrame"] {{
    background: {Colors.BG_PANEL};
    border: 1px solid {Colors.BORDER};
    border-radius: {Sizes.RADIUS_MD}px;
    overflow: hidden;
  }}
  [data-testid="stDataFrame"] * {{
    font-family: {Fonts.MONO} !important;
    font-size: 12px !important;
  }}

  /* ─── Plotly herda a fonte ─────────────────────────────── */
  .js-plotly-plot .plotly text {{
    font-family: {Fonts.PRIMARY} !important;
    fill: {Colors.TEXT_MAIN} !important;
  }}

  /* ─── Badges de risco (usados pelo componente ui.badge) ── */
  .badge-risco-alto, .badge-risco-medio, .badge-risco-baixo,
  .badge-risco-accent, .badge-risco-neutral {{
    display: inline-block;
    font-family: {Fonts.MONO};
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding: 3px 9px;
    border-radius: 10px;
    vertical-align: middle;
  }}
  .badge-risco-alto {{
    background: rgba(244,67,54,0.10);
    border: 1px solid rgba(244,67,54,0.30);
    color: #ff6b5f;
  }}
  .badge-risco-medio {{
    background: rgba(255,152,0,0.10);
    border: 1px solid rgba(255,152,0,0.30);
    color: #ffb74d;
  }}
  .badge-risco-baixo {{
    background: rgba(76,175,80,0.10);
    border: 1px solid rgba(76,175,80,0.30);
    color: #6dd070;
  }}
  .badge-risco-accent {{
    background: rgba(255,174,53,0.10);
    border: 1px solid rgba(255,174,53,0.30);
    color: {Colors.ACCENT};
  }}
  .badge-risco-neutral {{
    background: rgba(161,161,161,0.08);
    border: 1px solid rgba(161,161,161,0.25);
    color: {Colors.TEXT_MUTED};
  }}

  /* ─── Headline (manchete) ──────────────────────────────── */
  .ufmg-headline {{
    background: {Colors.BG_PANEL};
    border: 1px solid {Colors.BORDER};
    border-left: 4px solid {Colors.ACCENT};
    border-radius: {Sizes.RADIUS_MD}px;
    padding: 28px 32px;
    margin: 8px 0 24px 0;
  }}
  .ufmg-headline-insight {{
    font-size: {Sizes.HEADLINE_TEXT}px;
    font-weight: 500;
    color: {Colors.TEXT_MAIN};
    line-height: 1.45;
    margin-bottom: 18px;
  }}
  .ufmg-headline-rule {{
    width: 48px;
    height: 2px;
    background: {Colors.BORDER_STRONG};
    margin-bottom: 16px;
  }}
  .ufmg-headline-number {{
    font-family: {Fonts.PRIMARY};
    font-size: {Sizes.HEADLINE_NUMBER}px;
    font-weight: 700;
    color: {Colors.ACCENT};
    letter-spacing: -0.03em;
    line-height: 1.0;
    margin-bottom: 8px;
  }}
  .ufmg-headline-sub {{
    font-size: 14px;
    color: {Colors.TEXT_MUTED};
    line-height: 1.55;
  }}

  /* ─── Section divider (camadas 2/3) ────────────────────── */
  .ufmg-section-divider {{
    display: flex;
    align-items: center;
    gap: 14px;
    margin: 26px 0 16px 0;
  }}
  .ufmg-section-divider-label {{
    font-family: {Fonts.MONO};
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: {Colors.TEXT_DIM};
    white-space: nowrap;
  }}
  .ufmg-section-divider-line {{
    flex: 1;
    height: 1px;
    background: {Colors.BORDER};
  }}

  /* ─── KPI card custom (ui.kpi_card) ────────────────────── */
  .ufmg-kpi-card {{
    background: {Colors.BG_PANEL};
    border: 1px solid {Colors.BORDER};
    border-radius: {Sizes.RADIUS_MD}px;
    padding: 16px 18px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    height: 100%;
  }}
  .ufmg-kpi-card .label {{
    font-family: {Fonts.MONO};
    font-size: 10px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: {Colors.TEXT_DIM};
  }}
  .ufmg-kpi-card .value {{
    font-family: {Fonts.PRIMARY};
    font-size: {Sizes.KPI_BIG}px;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: {Colors.TEXT_MAIN};
  }}
  .ufmg-kpi-card .value.accent {{ color: {Colors.ACCENT}; }}
  .ufmg-kpi-card .value.danger {{ color: {Colors.DANGER}; }}
  .ufmg-kpi-card .value.success {{ color: {Colors.SUCCESS}; }}
  .ufmg-kpi-card .value.warning {{ color: {Colors.WARNING}; }}
  .ufmg-kpi-card .delta {{
    font-family: {Fonts.MONO};
    font-size: 11px;
    color: {Colors.TEXT_MUTED};
  }}
</style>
"""


# Plotly layout base — use com fig.update_layout(**get_plotly_layout())
def get_plotly_layout() -> dict:
    return dict(
        template="plotly_dark",
        paper_bgcolor=Colors.BG_PANEL,
        plot_bgcolor=Colors.BG_PANEL,
        font=dict(family="Inter, sans-serif", color=Colors.TEXT_MAIN, size=12),
        colorway=[
            Colors.ACCENT,
            Colors.SUCCESS,
            Colors.WARNING,
            Colors.DANGER,
            Colors.TEXT_MUTED,
        ],
        xaxis=dict(gridcolor=Colors.BORDER, zerolinecolor=Colors.BORDER),
        yaxis=dict(gridcolor=Colors.BORDER, zerolinecolor=Colors.BORDER),
    )


def apply_theme() -> None:
    """Injeta o CSS global. Chame UMA vez após `st.set_page_config`."""
    st.markdown(get_global_css(), unsafe_allow_html=True)
