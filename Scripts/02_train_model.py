"""
===============================================================
PIPELINE 02 — TREINO DO XGBOOST CLASSIFIER
===============================================================
Treina o classificador binário ACORDO vs DEFESA, avalia,
e salva o modelo + artefatos de métricas.

USO:
    python 02_train_model.py --input artefatos/
===============================================================
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
import joblib

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import (
    roc_auc_score, classification_report, confusion_matrix,
    precision_recall_curve, roc_curve
)


# ---------- HIPERPARÂMETROS ----------
# Valores recomendados para dataset desse porte (60k, binário)
XGBOOST_PARAMS = {
    'n_estimators': 300,
    'max_depth': 6,                # 6-8 é bom para datasets tabulares
    'learning_rate': 0.08,
    'subsample': 0.85,             # ajuda a reduzir overfitting
    'colsample_bytree': 0.85,
    'min_child_weight': 5,         # regularização: folha precisa ter >= 5 amostras
    'reg_alpha': 0.1,              # L1
    'reg_lambda': 1.0,             # L2
    'objective': 'binary:logistic',
    'eval_metric': 'logloss',
    'random_state': 42,
    'n_jobs': -1,
}

# Se a classe ACORDO está desbalanceada (~30%), podemos balancear
USE_CLASS_WEIGHT = True


# ---------- FUNÇÕES ----------

def carregar_dados(pasta: Path):
    X = pd.read_pickle(pasta / 'X.pkl')
    y = pd.read_pickle(pasta / 'y.pkl')['y']
    print(f"[carregar] X: {X.shape} | y: {y.shape} | ACORDO: {y.mean()*100:.1f}%")
    return X, y


def treinar(X_train, y_train, params: dict):
    """Treina XGBoost com class weight se necessário."""
    params = params.copy()
    if USE_CLASS_WEIGHT:
        # scale_pos_weight = n_neg / n_pos
        ratio = (y_train == 0).sum() / (y_train == 1).sum()
        params['scale_pos_weight'] = ratio
        print(f"[treinar] scale_pos_weight = {ratio:.2f}")

    model = xgb.XGBClassifier(**params)
    model.fit(
        X_train, y_train,
        eval_set=[(X_train, y_train)],
        verbose=False
    )
    return model


def avaliar(model, X_test, y_test) -> dict:
    """Avaliação completa no teste."""
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    auc = roc_auc_score(y_test, y_proba)
    acc = (y_pred == y_test).mean()
    cm = confusion_matrix(y_test, y_pred)

    print(f"\n{'='*60}")
    print(f"AVALIAÇÃO NO CONJUNTO DE TESTE")
    print(f"{'='*60}")
    print(f"AUC:       {auc:.4f}")
    print(f"Accuracy:  {acc:.4f}")
    print(f"\nMatriz de confusão:")
    print(f"                    Prev DEFESA   Prev ACORDO")
    print(f"  Real DEFESA       {cm[0,0]:>10}    {cm[0,1]:>10}")
    print(f"  Real ACORDO       {cm[1,0]:>10}    {cm[1,1]:>10}")
    print(f"\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['DEFESA', 'ACORDO']))

    return {
        'auc': float(auc),
        'accuracy': float(acc),
        'confusion_matrix': cm.tolist(),
    }


def calibracao(model, X_test, y_test):
    """Verifica se as probabilidades do modelo batem com a taxa real."""
    y_proba = model.predict_proba(X_test)[:, 1]
    df = pd.DataFrame({'proba': y_proba, 'real': y_test.values})
    df['bin'] = pd.cut(df['proba'], bins=[0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0])
    calib = df.groupby('bin', observed=True).agg(
        n=('real', 'count'),
        proba_media=('proba', 'mean'),
        taxa_real=('real', 'mean'),
    ).round(3)
    print(f"\nCALIBRAÇÃO (P(ACORDO) predita vs taxa real):")
    print(calib)
    return calib


def feature_importance(model, feature_names, top=20):
    fi = pd.DataFrame({
        'feature': feature_names,
        'importance': model.feature_importances_,
    }).sort_values('importance', ascending=False).head(top)
    print(f"\nTOP {top} FEATURES:")
    print(fi.to_string(index=False))
    return fi


def cross_validation(X, y, params: dict, n_splits=5):
    """CV robusta para validar generalização."""
    print(f"\n{'='*60}")
    print(f"CROSS-VALIDATION ({n_splits} folds)")
    print(f"{'='*60}")

    params_cv = params.copy()
    if USE_CLASS_WEIGHT:
        ratio = (y == 0).sum() / (y == 1).sum()
        params_cv['scale_pos_weight'] = ratio

    model = xgb.XGBClassifier(**params_cv)
    scores = cross_val_score(
        model, X, y, cv=StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42),
        scoring='roc_auc', n_jobs=-1
    )
    print(f"AUC por fold: {[f'{s:.4f}' for s in scores]}")
    print(f"AUC médio:    {scores.mean():.4f} (± {scores.std():.4f})")
    return scores


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default='artefatos', help='Pasta com X.parquet, y.parquet')
    args = parser.parse_args()

    pasta = Path(args.input)
    X, y = carregar_dados(pasta)

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"[split] train: {X_train.shape[0]} | test: {X_test.shape[0]}")

    # Cross-validation primeiro (sanidade)
    cv_scores = cross_validation(X, y, XGBOOST_PARAMS)

    # Treino final
    print(f"\n{'='*60}")
    print(f"TREINO FINAL")
    print(f"{'='*60}")
    model = treinar(X_train, y_train, XGBOOST_PARAMS)

    # Avaliação
    metricas = avaliar(model, X_test, y_test)
    calib = calibracao(model, X_test, y_test)
    fi = feature_importance(model, X.columns.tolist())

    # Salvar
    joblib.dump(model, pasta / 'modelo_xgboost.pkl')

    with open(pasta / 'metricas.json', 'w') as f:
        json.dump({
            'cv_auc_mean': float(cv_scores.mean()),
            'cv_auc_std': float(cv_scores.std()),
            **metricas,
            'hyperparams': XGBOOST_PARAMS,
        }, f, indent=2)

    fi.to_csv(pasta / 'feature_importance.csv', index=False)

    print(f"\n✓ Modelo salvo em {pasta}/modelo_xgboost.pkl")
    print(f"✓ Métricas em {pasta}/metricas.json")
    print(f"✓ Feature importance em {pasta}/feature_importance.csv")


if __name__ == '__main__':
    main()
