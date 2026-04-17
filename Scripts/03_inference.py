"""
===============================================================
PIPELINE 03 — INFERÊNCIA (USADO EM PRODUÇÃO PELO AGENTE)
===============================================================
Função simples que recebe os dados de um caso novo e retorna
a recomendação ACORDO ou DEFESA com a probabilidade.

USO PROGRAMÁTICO:
    from inference import recomendar

    resultado = recomendar({
        'uf': 'AM',
        'valor_causa': 20000.0,
        'sub_assunto': 'Golpe',
        'subsidios': {
            'Contrato': 1,
            'Extrato': 0,
            'Comprovante de crédito': 0,
            'Dossiê': 1,
            'Demonstrativo de evolução da dívida': 0,
            'Laudo referenciado': 1,
        }
    })
    # -> {'decisao': 'ACORDO', 'probabilidade_acordo': 0.87, ...}
===============================================================
"""
import json
from pathlib import Path
from typing import Dict

import pandas as pd
import joblib


# Espelho das constantes do pipeline 01 (mantenha em sync!)
SUBSIDIOS = [
    'Contrato',
    'Extrato',
    'Comprovante de crédito',
    'Dossiê',
    'Demonstrativo de evolução da dívida',
    'Laudo referenciado',
]
SUBSIDIOS_CRITICOS = ['Contrato', 'Extrato', 'Comprovante de crédito']

CLUSTER_UF = {
    'AM': 'ALTO', 'AP': 'ALTO',
    'GO': 'MEDIO', 'RS': 'MEDIO', 'BA': 'MEDIO', 'RJ': 'MEDIO',
    'ES': 'MEDIO', 'DF': 'MEDIO', 'AL': 'MEDIO', 'SP': 'MEDIO',
    'PE': 'MEDIO',
    'MG': 'BAIXO', 'SE': 'BAIXO', 'PB': 'BAIXO', 'CE': 'BAIXO',
    'PA': 'BAIXO', 'AC': 'BAIXO', 'SC': 'BAIXO', 'RO': 'BAIXO',
    'PR': 'BAIXO', 'MS': 'BAIXO', 'TO': 'BAIXO', 'RN': 'BAIXO',
    'MT': 'BAIXO', 'PI': 'BAIXO', 'MA': 'BAIXO',
}


class RecomendadorAcordo:
    """Wrapper que encapsula modelo + feature engineering em produção."""

    def __init__(self, pasta_artefatos: str = 'artefatos'):
        pasta = Path(pasta_artefatos)
        self.model = joblib.load(pasta / 'modelo_xgboost.pkl')
        with open(pasta / 'features.json') as f:
            self.feature_order = json.load(f)

    def _montar_features(self, caso: Dict) -> pd.DataFrame:
        """Transforma um dict de caso no vetor de features esperado pelo modelo."""
        subs = caso['subsidios']
        valor_causa = float(caso['valor_causa'])
        uf = caso['uf']
        sub_assunto = caso['sub_assunto']

        # Features numéricas diretas
        row = {s: int(subs.get(s, 0)) for s in SUBSIDIOS}
        row['Valor da causa'] = valor_causa

        # Derivadas
        row['qtd_subsidios_total'] = sum(row[s] for s in SUBSIDIOS)
        row['qtd_subsidios_criticos'] = sum(row[s] for s in SUBSIDIOS_CRITICOS)
        row['tem_contrato_e_extrato'] = int(row['Contrato'] == 1 and row['Extrato'] == 1)
        row['tem_todos_criticos'] = int(row['qtd_subsidios_criticos'] == 3)
        row['sem_criticos'] = int(row['qtd_subsidios_criticos'] == 0)
        row['tem_docs_regulatorios'] = int(
            row['Comprovante de crédito'] == 1 and
            row['Demonstrativo de evolução da dívida'] == 1
        )
        row['is_golpe'] = int(sub_assunto == 'Golpe')

        # Categóricas (one-hot)
        cluster = CLUSTER_UF.get(uf, 'MEDIO')
        for c in ['ALTO', 'MEDIO', 'BAIXO']:
            row[f'cluster_uf_{c}'] = int(cluster == c)

        # Faixa de causa
        if valor_causa <= 8000:
            faixa = 'ate_8k'
        elif valor_causa <= 15000:
            faixa = '8a15k'
        elif valor_causa <= 22000:
            faixa = '15a22k'
        else:
            faixa = 'acima_22k'
        for f in ['ate_8k', '8a15k', '15a22k', 'acima_22k']:
            row[f'faixa_causa_{f}'] = int(faixa == f)

        # Garantir que o vetor tem exatamente as mesmas colunas na mesma ordem do treino
        df = pd.DataFrame([row])
        for col in self.feature_order:
            if col not in df.columns:
                df[col] = 0
        df = df[self.feature_order]
        return df

    def recomendar(self, caso: Dict, threshold: float = 0.5) -> Dict:
        """
        Retorna:
          decisao: 'ACORDO' ou 'DEFESA'
          probabilidade_acordo: float 0-1
          confianca: 'ALTA' | 'MEDIA' | 'BAIXA'
          features_chave: lista das principais features do caso
        """
        X = self._montar_features(caso)
        prob = float(self.model.predict_proba(X)[0, 1])
        decisao = 'ACORDO' if prob >= threshold else 'DEFESA'

        if prob >= 0.8 or prob <= 0.2:
            confianca = 'ALTA'
        elif prob >= 0.65 or prob <= 0.35:
            confianca = 'MEDIA'
        else:
            confianca = 'BAIXA'

        # Resumo acionável das features do caso (para o agente explicar)
        subs = caso['subsidios']
        presentes = [s for s in SUBSIDIOS if subs.get(s, 0) == 1]
        ausentes = [s for s in SUBSIDIOS if subs.get(s, 0) == 0]
        criticos_presentes = [s for s in SUBSIDIOS_CRITICOS if subs.get(s, 0) == 1]
        criticos_ausentes = [s for s in SUBSIDIOS_CRITICOS if subs.get(s, 0) == 0]

        return {
            'decisao': decisao,
            'probabilidade_acordo': round(prob, 4),
            'probabilidade_defesa': round(1 - prob, 4),
            'confianca': confianca,
            'resumo_caso': {
                'uf': caso['uf'],
                'cluster_risco_uf': CLUSTER_UF.get(caso['uf'], 'MEDIO'),
                'valor_causa': caso['valor_causa'],
                'sub_assunto': caso['sub_assunto'],
                'subsidios_presentes': presentes,
                'subsidios_ausentes': ausentes,
                'criticos_presentes': criticos_presentes,
                'criticos_ausentes': criticos_ausentes,
            }
        }


# Execução direta para teste rápido
if __name__ == '__main__':
    rec = RecomendadorAcordo('artefatos')

    caso_exemplo = {
        'uf': 'AM',
        'valor_causa': 20000.0,
        'sub_assunto': 'Golpe',
        'subsidios': {
            'Contrato': 1,
            'Extrato': 0,
            'Comprovante de crédito': 0,
            'Dossiê': 1,
            'Demonstrativo de evolução da dívida': 0,
            'Laudo referenciado': 1,
        }
    }
    resultado = rec.recomendar(caso_exemplo)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
