"""
===============================================================
PIPELINE 01 — PREPARAÇÃO DOS DADOS
===============================================================
Carrega a base, faz merge, rotula, cria features, e salva
um parquet pronto para treino.

USO:
    python 01_prepare_data.py --input base.xlsx --output artefatos/
===============================================================
"""
import argparse
import pandas as pd
import numpy as np
from pathlib import Path

# ---------- CONFIGURAÇÃO CENTRAL (ajustável) ----------

SUBSIDIOS = [
    'Contrato',
    'Extrato',
    'Comprovante de crédito',
    'Dossiê',
    'Demonstrativo de evolução da dívida',
    'Laudo referenciado',
]
SUBSIDIOS_CRITICOS = ['Contrato', 'Extrato', 'Comprovante de crédito']

# Clusters de UF por taxa de êxito histórica
# (derivado da análise: AM/AP ~52%, MA ~79%)
CLUSTER_UF = {
    # Alto risco (êxito < 60%)
    'AM': 'ALTO', 'AP': 'ALTO',
    # Risco médio (60-70%)
    'GO': 'MEDIO', 'RS': 'MEDIO', 'BA': 'MEDIO', 'RJ': 'MEDIO',
    'ES': 'MEDIO', 'DF': 'MEDIO', 'AL': 'MEDIO', 'SP': 'MEDIO',
    'PE': 'MEDIO',
    # Baixo risco (>= 70%)
    'MG': 'BAIXO', 'SE': 'BAIXO', 'PB': 'BAIXO', 'CE': 'BAIXO',
    'PA': 'BAIXO', 'AC': 'BAIXO', 'SC': 'BAIXO', 'RO': 'BAIXO',
    'PR': 'BAIXO', 'MS': 'BAIXO', 'TO': 'BAIXO', 'RN': 'BAIXO',
    'MT': 'BAIXO', 'PI': 'BAIXO', 'MA': 'BAIXO',
}

# Threshold do rotulamento econômico
# "Se o banco pagou mais do que 30% da causa, teria sido melhor acordar"
THRESHOLD_ACORDO_PCT_CAUSA = 0.30


# ---------- FUNÇÕES ----------

def carregar_base(caminho_xlsx: str) -> pd.DataFrame:
    """Lê as duas abas e faz o merge pelo número do processo."""
    resultados = pd.read_excel(caminho_xlsx, sheet_name='Resultados dos processos')
    subsidios = pd.read_excel(caminho_xlsx, sheet_name='Subsídios disponibilizados', header=1)
    subsidios = subsidios.rename(columns={subsidios.columns[0]: 'Número do processo'})
    df = resultados.merge(subsidios, on='Número do processo', how='left')
    print(f"[carregar_base] Base unificada: {df.shape[0]} processos")
    return df


def rotular(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rotulamento econômico:
      ACORDO = banco pagou mais do que pagaria num acordo médio (30% da causa)
      DEFESA = banco ganhou ou pagou pouco, defesa foi a escolha certa
    """
    custo_acordo_hipotetico = THRESHOLD_ACORDO_PCT_CAUSA * df['Valor da causa']
    df['label'] = np.where(
        df['Valor da condenação/indenização'] > custo_acordo_hipotetico,
        'ACORDO',
        'DEFESA'
    )
    # versão numérica (1 = ACORDO, 0 = DEFESA)
    df['y'] = (df['label'] == 'ACORDO').astype(int)
    dist = df['label'].value_counts(normalize=True).round(3) * 100
    print(f"[rotular] Distribuição: DEFESA={dist.get('DEFESA', 0):.1f}% | ACORDO={dist.get('ACORDO', 0):.1f}%")
    return df


def criar_features(df: pd.DataFrame) -> pd.DataFrame:
    """Feature engineering — cria variáveis derivadas."""

    # 1. Contagens de subsídios
    df['qtd_subsidios_total'] = df[SUBSIDIOS].sum(axis=1)
    df['qtd_subsidios_criticos'] = df[SUBSIDIOS_CRITICOS].sum(axis=1)

    # 2. Interações binárias de subsídios críticos
    df['tem_contrato_e_extrato'] = (
        (df['Contrato'] == 1) & (df['Extrato'] == 1)
    ).astype(int)

    df['tem_todos_criticos'] = (df['qtd_subsidios_criticos'] == 3).astype(int)
    df['sem_criticos'] = (df['qtd_subsidios_criticos'] == 0).astype(int)

    # 3. Docs regulatórios (BACEN + Demonstrativo)
    df['tem_docs_regulatorios'] = (
        (df['Comprovante de crédito'] == 1) &
        (df['Demonstrativo de evolução da dívida'] == 1)
    ).astype(int)

    # 4. Cluster de UF
    df['cluster_uf'] = df['UF'].map(CLUSTER_UF).fillna('MEDIO')

    # 5. Sub-assunto como flag binária
    df['is_golpe'] = (df['Sub-assunto'] == 'Golpe').astype(int)

    # 6. Faixa de valor da causa (pode capturar padrões de juiz)
    df['faixa_causa'] = pd.cut(
        df['Valor da causa'],
        bins=[0, 8000, 15000, 22000, 50000],
        labels=['ate_8k', '8a15k', '15a22k', 'acima_22k']
    ).astype(str)

    print(f"[criar_features] {df.shape[1]} colunas totais após FE")
    return df


def selecionar_features_modelo(df: pd.DataFrame) -> tuple:
    """Retorna X (features) e y (target) prontos para o modelo."""

    # Features numéricas diretas
    num_feats = SUBSIDIOS + [
        'Valor da causa',
        'qtd_subsidios_total',
        'qtd_subsidios_criticos',
        'tem_contrato_e_extrato',
        'tem_todos_criticos',
        'sem_criticos',
        'tem_docs_regulatorios',
        'is_golpe',
    ]

    # Features categóricas (one-hot)
    cat_feats = ['cluster_uf', 'faixa_causa']
    cat_dummies = pd.get_dummies(df[cat_feats], drop_first=False).astype(int)

    X = pd.concat([df[num_feats], cat_dummies], axis=1)
    y = df['y']

    print(f"[selecionar_features] X.shape = {X.shape} | y.shape = {y.shape}")
    return X, y


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default='base.xlsx', help='Caminho do xlsx')
    parser.add_argument('--output', default='artefatos', help='Pasta de saída')
    args = parser.parse_args()

    outdir = Path(args.output)
    outdir.mkdir(exist_ok=True)

    # Pipeline
    df = carregar_base(args.input)
    df = rotular(df)
    df = criar_features(df)
    X, y = selecionar_features_modelo(df)

    # Salvar (pickle evita dependência de pyarrow)
    X.to_pickle(outdir / 'X.pkl')
    y.to_frame('y').to_pickle(outdir / 'y.pkl')
    df.to_pickle(outdir / 'dataset_completo.pkl')

    # Salvar lista de features para uso em produção
    import json
    with open(outdir / 'features.json', 'w') as f:
        json.dump(list(X.columns), f, indent=2)

    print(f"\n✓ Artefatos salvos em {outdir}/")
    print(f"  - X.pkl                  ({X.shape})")
    print(f"  - y.pkl                  ({y.shape})")
    print(f"  - dataset_completo.pkl")
    print(f"  - features.json          ({len(X.columns)} features)")


if __name__ == '__main__':
    main()
