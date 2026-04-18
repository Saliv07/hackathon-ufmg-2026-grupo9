"""
Componentes reutilizáveis do dashboard Banco UFMG.

Arquitetura de 3 camadas (por aba):
    - Camada 1 · MANCHETE  -> `headline()`           (insight + número grande)
    - Camada 2 · PROVA     -> 2-3 gráficos essenciais (chamados diretamente em app.py)
    - Camada 3 · EXPLORAÇÃO-> `section_divider()` + `st.expander(...)` com tudo

Todos os componentes assumem que `theme_banco_ufmg.apply_theme()` já foi
chamado e as classes CSS (.ufmg-*, .badge-risco-*) estão injetadas.
"""
from __future__ import annotations

from html import escape

import streamlit as st

from src.monitor.dashboards.theme_banco_ufmg import SEVERITY_COLORS


# ============================================================
# Manchete (Camada 1)
# ============================================================
def headline(
    texto_insight: str,
    valor_grande: str,
    subtexto: str | None = None,
) -> None:
    """Renderiza a MANCHETE de uma aba.

    Layout:
        [ insight em 20px branco (1-2 linhas)             ]
        [ ────── (linha sutil 48px)                        ]
        [ valor_grande em 52px 700 laranja                ]
        [ subtexto em 14px muted (opcional)               ]
    """
    sub_html = ""
    if subtexto:
        sub_html = f'<div class="ufmg-headline-sub">{escape(subtexto)}</div>'
    html = (
        '<div class="ufmg-headline">'
        f'<div class="ufmg-headline-insight">{escape(texto_insight)}</div>'
        '<div class="ufmg-headline-rule"></div>'
        f'<div class="ufmg-headline-number">{escape(valor_grande)}</div>'
        f"{sub_html}"
        "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


# ============================================================
# Separador de camadas
# ============================================================
def section_divider(titulo: str) -> None:
    """Separador entre as camadas 2 (prova) e 3 (exploração)."""
    html = (
        '<div class="ufmg-section-divider">'
        f'<span class="ufmg-section-divider-label">{escape(titulo)}</span>'
        '<span class="ufmg-section-divider-line"></span>'
        "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


# ============================================================
# Badge de risco
# ============================================================
_BADGE_CLASS = {
    "critical": "badge-risco-alto",
    "danger": "badge-risco-alto",
    "alto": "badge-risco-alto",
    "warning": "badge-risco-medio",
    "attention": "badge-risco-medio",
    "medio": "badge-risco-medio",
    "ok": "badge-risco-baixo",
    "success": "badge-risco-baixo",
    "baixo": "badge-risco-baixo",
    "accent": "badge-risco-accent",
    "neutral": "badge-risco-neutral",
}


def badge(texto: str, severidade: str = "neutral") -> str:
    """Retorna o HTML do badge (para concatenar em outros markdowns)."""
    cls = _BADGE_CLASS.get(severidade.lower(), "badge-risco-neutral")
    return f'<span class="{cls}">{escape(texto)}</span>'


def render_badge(texto: str, severidade: str = "neutral") -> None:
    """Renderiza o badge diretamente com st.markdown."""
    st.markdown(badge(texto, severidade), unsafe_allow_html=True)


# ============================================================
# KPI card customizado
# ============================================================
_KPI_VALUE_CLASS = {
    "critical": "danger",
    "danger": "danger",
    "warning": "warning",
    "attention": "warning",
    "ok": "success",
    "success": "success",
    "accent": "accent",
    "neutral": "",
}


def kpi_card(
    label: str,
    valor: str,
    delta: str | None = None,
    severidade: str = "neutral",
) -> None:
    """Card KPI com controle total de cor de valor e delta.

    Usa as classes .ufmg-kpi-card do tema. Use quando `st.metric` não
    permitir a ênfase visual desejada (ex: destacar valor em laranja).
    """
    value_cls = _KPI_VALUE_CLASS.get(severidade.lower(), "")
    delta_html = f'<div class="delta">{escape(delta)}</div>' if delta else ""
    html = (
        '<div class="ufmg-kpi-card">'
        f'<div class="label">{escape(label)}</div>'
        f'<div class="value {value_cls}">{escape(valor)}</div>'
        f"{delta_html}"
        "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


# Re-exporta o dict em caso de alguém querer a cor bruta
__all__ = [
    "headline",
    "section_divider",
    "badge",
    "render_badge",
    "kpi_card",
    "SEVERITY_COLORS",
]
