"""
policy_service.py — Fornece o texto da política de acordos como contexto para o agente LLM.

NÃO calcula decisões. Apenas estrutura os dados do caso para que o LLM
possa aplicar a política com base na probabilidade do XGBoost.
"""
import os

# Carrega o texto da política uma vez
_POLICY_TEXT = None
_POLICY_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "docs", "politica_acordo.md"
)


def load_policy() -> str:
    """Carrega o texto da política de acordos do arquivo markdown."""
    global _POLICY_TEXT
    if _POLICY_TEXT is not None:
        return _POLICY_TEXT

    try:
        with open(_POLICY_PATH, 'r', encoding='utf-8') as f:
            _POLICY_TEXT = f.read()
        print(f"DEBUG: Política de acordos carregada de {_POLICY_PATH}")
    except FileNotFoundError:
        print(f"WARNING: Política de acordos não encontrada em {_POLICY_PATH}")
        _POLICY_TEXT = "(Política de acordos não disponível)"
    
    return _POLICY_TEXT


def get_policy_text() -> str:
    """Retorna o texto da política (carrega se necessário)."""
    if _POLICY_TEXT is None:
        return load_policy()
    return _POLICY_TEXT
