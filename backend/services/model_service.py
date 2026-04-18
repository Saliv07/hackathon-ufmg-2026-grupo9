"""
model_service.py — Carrega o modelo XGBoost e fornece predições.

O modelo retorna a probabilidade de que um caso deveria ser ACORDO.
Essa probabilidade é passada como contexto ao agente LLM, que decide
com base na Política de Acordos.
"""
import os
import json
import joblib
import numpy as np

# Caminhos dos artefatos
_ARTEFATOS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "artefatos"
)
_MODEL_PATH = os.path.join(_ARTEFATOS_DIR, "modelo_xgboost.pkl")
_FEATURES_PATH = os.path.join(_ARTEFATOS_DIR, "features.json")

# Estado global
_model = None
_features = None


def load_model() -> bool:
    """Carrega modelo XGBoost e lista de features. Retorna True se ok."""
    global _model, _features
    try:
        _model = joblib.load(_MODEL_PATH)
        with open(_FEATURES_PATH, 'r', encoding='utf-8') as f:
            _features = json.load(f)
        print(f"DEBUG: Modelo XGBoost carregado de {_MODEL_PATH}")
        print(f"DEBUG: Features: {_features}")
        return True
    except Exception as e:
        print(f"WARNING: Falha ao carregar modelo XGBoost: {e}")
        _model = None
        _features = None
        return False


def is_loaded() -> bool:
    return _model is not None


# ── Mapeamento de evidence do caso para features do modelo ────────────────────

# Mapa: id da evidence no frontend → nome da feature no modelo
_EVIDENCE_TO_FEATURE = {
    'contract': 'Contrato',
    'ted': 'Extrato',                    # TED/titularidade → Extrato bancário
    'biometry': 'Dossiê',                # Biometria/Dossiê Veritas
    'usage': 'Demonstrativo de evolução da dívida',
    'payments': 'Demonstrativo de evolução da dívida',
}

# UFs de alto risco (êxito < 60%)
_UF_ALTO = {'AM', 'AP'}
_UF_MEDIO = {'MA', 'PI', 'TO', 'PA', 'RR', 'AC', 'RO'}


def _extract_features(case_data: dict) -> dict:
    """Extrai as 9 features do modelo a partir dos dados do caso."""
    features = {f: 0 for f in _features}

    # Mapeia evidence → features de subsídios
    evidence = case_data.get('evidence', [])
    for ev in evidence:
        ev_id = ev.get('id', '')
        ev_status = ev.get('status', '')
        feature_name = _EVIDENCE_TO_FEATURE.get(ev_id)
        if feature_name and ev_status == 'valid' and feature_name in features:
            features[feature_name] = 1

    # Documentos com "Comprovante" ou "BACEN"
    documents = case_data.get('documents', [])
    for doc in documents:
        doc_name = (doc.get('name', '') + doc.get('content', '')).lower()
        if 'bacen' in doc_name or 'comprovante de cr' in doc_name:
            features['Comprovante de crédito'] = 1
        if 'laudo' in doc_name:
            features['Laudo referenciado'] = 1

    # Sub-assunto golpe
    case_type = case_data.get('type', '').lower()
    summary = case_data.get('summary', '').lower()
    if 'golpe' in case_type or 'golpe' in summary:
        features['is_golpe'] = 1

    # UF
    location = ''
    profile = case_data.get('profile', {})
    if profile:
        location = profile.get('location', '')
    if not location:
        location = case_data.get('location', '')

    uf = ''
    if ' - ' in location:
        uf = location.split(' - ')[-1].strip().upper()

    if uf in _UF_ALTO:
        features['uf_alto'] = 1
    elif uf in _UF_MEDIO:
        features['uf_medio'] = 1

    return features


def predict(case_data: dict) -> dict:
    """
    Faz predição do modelo para os dados do caso.

    Retorna:
        {
            "model_loaded": True/False,
            "probability": float (0-1),
            "recommendation": "ACORDO" | "DEFESA",
            "confidence": "ALTA" | "MEDIA" | "BAIXA",
            "features": dict com as 9 features extraídas,
        }
    """
    if _model is None:
        return {"model_loaded": False}

    features = _extract_features(case_data)

    # Monta array na ordem correta das features
    X = np.array([[features[f] for f in _features]])
    prob = float(_model.predict_proba(X)[0][1])

    # Recomendação e confiança
    if prob >= 0.6:
        recommendation = 'ACORDO'
    elif prob <= 0.4:
        recommendation = 'DEFESA'
    else:
        recommendation = 'ACORDO' if prob >= 0.5 else 'DEFESA'

    if prob >= 0.75 or prob <= 0.25:
        confidence = 'ALTA'
    elif prob >= 0.65 or prob <= 0.35:
        confidence = 'MEDIA'
    else:
        confidence = 'BAIXA'

    return {
        "model_loaded": True,
        "probability": round(prob, 4),
        "recommendation": recommendation,
        "confidence": confidence,
        "features": features,
    }
