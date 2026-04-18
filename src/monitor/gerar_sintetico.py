"""
Gera o Conjunto B (dataset enriquecido) para dashboards de aderência.

Lê `casos_60k.parquet` e adiciona colunas operacionais sintéticas com vieses
controlados (H5 a H8 do DECISOES.md): advogados, escritórios, datas, ações
recomendadas (mock H2/H3) e ações tomadas.

Regra crítica: dataset exclusivo dos dashboards de aderência. Nunca deve ser
usado para treinar o XGBoost (vazamento circular).

Vetorizado com np.where / máscaras; roda em <2s para 60k linhas.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.monitor.paths import CASOS_60K, CASOS_ENRIQUECIDOS, DATA_PROCESSED


SEED = 42

DATA_INICIAL = pd.Timestamp("2025-04-01")
DATA_FINAL = pd.Timestamp("2026-03-31")

# Política mock (H2 do DECISOES.md): valor de acordo = ACORDO_PCT_CAUSA × valor da causa.
# Fonte única da verdade — counterfactual.py importa daqui.
ACORDO_PCT_CAUSA = 0.30


# ---------------------------------------------------------------------------
# Catálogos determinísticos usados para atribuir nomes próprios PT-BR.
# Ordem é parte da API (seed=42 + rng.choice). Mudanças aqui reposicionam
# advogados; manter a lista estável preserva reprodutibilidade.
# ---------------------------------------------------------------------------

NOMES_ESCRITORIOS = [
    "Pereira & Associados",
    "Azevedo, Costa e Silva",
    "Ribeiro Advocacia",
    "Mendonça, Vasconcelos e Carvalho",
    "Andrade Nogueira Sociedade de Advogados",
    "Tavares & Mourão Advogados",
    "Lima, Fontes e Machado",
    "Barros, Rocha e Moura",
    "Siqueira Campos Advocacia",
    "Queiroz, Figueiredo e Bastos",
    "Duarte & Bittencourt Advogados",
    "Castanheira, Almeida e Rezende",
    "Vilas Boas Sociedade de Advogados",
    "Macedo, Fernandes e Gusmão",
    "Coelho, Prado e Teixeira Advogados",
]

# Cidades-sede plausíveis por macrorregião IBGE. rng.choice escolhe uma.
CIDADES_POR_REGIAO = {
    "SE": ["São Paulo - SP", "Rio de Janeiro - RJ", "Belo Horizonte - MG", "Vitória - ES"],
    "S": ["Curitiba - PR", "Porto Alegre - RS", "Florianópolis - SC"],
    "NE": ["Salvador - BA", "Recife - PE", "Fortaleza - CE", "São Luís - MA"],
    "N": ["Manaus - AM", "Belém - PA", "Palmas - TO"],
    "CO": ["Brasília - DF", "Goiânia - GO", "Cuiabá - MT"],
}

# UF predominante por região (para gerar número de OAB condizente).
UF_POR_REGIAO = {
    "SE": ["SP", "RJ", "MG", "ES"],
    "S": ["PR", "RS", "SC"],
    "NE": ["BA", "PE", "CE", "MA"],
    "N": ["AM", "PA", "TO"],
    "CO": ["DF", "GO", "MT"],
}

# Primeiros nomes PT-BR com diversidade de gênero e região.
PRIMEIROS_NOMES = [
    "Mariana", "Carlos Eduardo", "Fernanda", "Rafael", "Juliana",
    "Pedro Henrique", "Camila", "Lucas", "Beatriz", "Thiago",
    "Larissa", "Gustavo", "Patrícia", "Rodrigo", "Amanda",
    "Felipe", "Isabela", "Bruno", "Letícia", "Marcelo",
    "Carolina", "Gabriel", "Renata", "Eduardo", "Natália",
    "Vinícius", "Aline", "Leonardo", "Tatiana", "Diego",
    "Priscila", "Henrique", "Sabrina", "André", "Raquel",
    "Daniel", "Vanessa", "Ricardo", "Bianca", "Matheus",
    "Cláudia", "Fábio", "Simone", "Paulo", "Débora",
    "José Antônio", "Luciana", "Roberto", "Márcia", "Sérgio",
    "Adriana", "Otávio", "Helena", "Alexandre", "Sofia",
    "Vítor", "Elaine", "Joaquim", "Flávia", "Murilo",
]

# Sobrenomes PT-BR comuns. Diversidade de origens (portuguesa, italiana, libanesa).
SOBRENOMES = [
    "Azevedo", "Ribeiro", "Costa", "Oliveira", "Carvalho",
    "Souza", "Rodrigues", "Almeida", "Mendes", "Barbosa",
    "Cavalcanti", "Nogueira", "Cardoso", "Moreira", "Teixeira",
    "Fonseca", "Pinheiro", "Araújo", "Vasconcelos", "Siqueira",
    "Machado", "Coelho", "Duarte", "Bittencourt", "Queiroz",
    "Figueiredo", "Tavares", "Moura", "Rocha", "Nascimento",
]


def _gerar_nomes_advogados(rng: np.random.Generator, n: int) -> np.ndarray:
    """Sorteia N nomes completos únicos combinando primeiro_nome + sobrenome.

    Mantém vetorização (rng.choice em bulk) e garante unicidade via pós-processo
    determinístico: colisões recebem sufixo numérico estável.
    """
    primeiros = rng.choice(np.array(PRIMEIROS_NOMES), size=n)
    sobrenomes_a = rng.choice(np.array(SOBRENOMES), size=n)
    sobrenomes_b = rng.choice(np.array(SOBRENOMES), size=n)
    nomes = [
        f"{p} {sa}" if sa == sb else f"{p} {sa} {sb}"
        for p, sa, sb in zip(primeiros, sobrenomes_a, sobrenomes_b)
    ]
    # Desambigua duplicatas preservando ordem
    vistos: dict[str, int] = {}
    final: list[str] = []
    for nome in nomes:
        c = vistos.get(nome, 0)
        if c == 0:
            final.append(nome)
        else:
            final.append(f"{nome} {_roman(c + 1)}")
        vistos[nome] = c + 1
    return np.array(final, dtype=object)


def _roman(n: int) -> str:
    """Sufixo romano simples (II, III, IV). n <= 10 cobre todos os casos aqui."""
    mapa = {2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII", 8: "VIII", 9: "IX", 10: "X"}
    return mapa.get(n, f"({n})")


def _gerar_oab(rng: np.random.Generator, regioes: np.ndarray) -> np.ndarray:
    """Gera números de OAB formatados 'OAB/UF XXX.XXX' com UF da região do escritório."""
    ufs = np.array([
        rng.choice(np.array(UF_POR_REGIAO[r])) for r in regioes
    ])
    numeros = rng.integers(30_000, 500_000, size=len(regioes))
    return np.array([
        f"OAB/{uf} {num // 1000:03d}.{num % 1000:03d}"
        for uf, num in zip(ufs, numeros)
    ], dtype=object)


def _montar_escritorios(rng: np.random.Generator) -> pd.DataFrame:
    """Constrói o catálogo de 10 escritórios com nome e cidade-sede."""
    aderencia_base = [0.95, 0.93, 0.92, 0.85, 0.83, 0.80, 0.78, 0.68, 0.64, 0.60]
    regioes = ["SE", "SE", "S", "S", "NE", "NE", "N", "CO", "N", "NE"]
    n = len(aderencia_base)

    # Sorteia 10 nomes distintos do catálogo de 15 (reprodutível com seed=42).
    nomes = rng.choice(np.array(NOMES_ESCRITORIOS), size=n, replace=False)
    cidades = np.array([rng.choice(np.array(CIDADES_POR_REGIAO[r])) for r in regioes])

    return pd.DataFrame({
        "escritorio_id": [f"ESC{i:02d}" for i in range(1, n + 1)],
        "escritorio_nome": nomes,
        "aderencia_base": aderencia_base,
        "regiao": regioes,
        "cidade_sede": cidades,
    })


# Catálogo resolvido com seed fixa — mantém a API pública (import ESCRITORIOS)
# compatível com qualquer código externo que leia o DataFrame.
ESCRITORIOS = _montar_escritorios(np.random.default_rng(SEED))

RAZOES_OVERRIDE = ["discordancia_score", "info_nova", "neg_em_andamento", "erro_ferramenta", "outro"]
PROBS_RAZOES = [0.40, 0.25, 0.15, 0.10, 0.10]


def gerar_advogados(rng: np.random.Generator, n: int = 50) -> pd.DataFrame:
    """Distribui N advogados entre os 10 escritórios (H5) com desvio individual ±5pp.

    Além dos campos estruturais (ids e aderência esperada), produz:
      - advogado_nome: nome próprio PT-BR realista
      - numero_oab: OAB/UF condizente com a região do escritório
      - escritorio_nome: nome do escritório (copiado do catálogo)
    """
    esc_idx = np.arange(n) % len(ESCRITORIOS)
    base = ESCRITORIOS["aderencia_base"].to_numpy()[esc_idx]
    ruido = rng.normal(0.0, 0.05, size=n)
    aderencia_indiv = np.clip(base + ruido, 0.40, 0.99)

    regioes = ESCRITORIOS["regiao"].to_numpy()[esc_idx]
    nomes_adv = _gerar_nomes_advogados(rng, n)
    oab = _gerar_oab(rng, regioes)

    return pd.DataFrame({
        "advogado_id": [f"ADV{i+1:03d}" for i in range(n)],
        "advogado_nome": nomes_adv,
        "numero_oab": oab,
        "escritorio_id": ESCRITORIOS["escritorio_id"].to_numpy()[esc_idx],
        "escritorio_nome": ESCRITORIOS["escritorio_nome"].to_numpy()[esc_idx],
        "regiao": regioes,
        "aderencia_esperada": aderencia_indiv,
    })


def gerar_datas(rng: np.random.Generator, n: int) -> tuple[pd.Series, pd.Series, np.ndarray]:
    """Gera data_distribuicao, data_decisao e tempo_decisao_min vetorizados."""
    dias_periodo = (DATA_FINAL - DATA_INICIAL).days
    offsets = rng.integers(0, dias_periodo + 1, size=n)
    data_distribuicao = DATA_INICIAL + pd.to_timedelta(offsets, unit="D")

    tempo_decisao_min = np.clip(
        rng.lognormal(mean=5.0, sigma=1.4, size=n), 5.0, 3000.0,
    )
    data_decisao = data_distribuicao + pd.to_timedelta(tempo_decisao_min, unit="m")
    data_decisao = data_decisao.where(data_decisao <= DATA_FINAL, DATA_FINAL)
    return data_distribuicao, data_decisao, tempo_decisao_min


def gerar_recomendacao_mock(df: pd.DataFrame) -> pd.DataFrame:
    """
    Mock da política (H2 + H3): acordo se subs_total <= 3, valor = ACORDO_PCT_CAUSA da causa.

    Substituir por leitura do CSV do XGBoost quando disponível (Passo 9 do guia).
    """
    df = df.copy()
    df["acao_recomendada"] = np.where(df["subs_total"] <= 3, "acordo", "defesa")
    df["valor_acordo_recomendado"] = np.where(
        df["acao_recomendada"] == "acordo",
        df["valor_causa"] * ACORDO_PCT_CAUSA,
        np.nan,
    )
    return df


def gerar_acao_tomada(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Aplica viés H7 (−8pp em Alto valor) e sorteia aderência caso a caso."""
    df = df.copy()
    ajuste_valor = np.where(df["faixa_valor"].to_numpy() == "Alto", -0.08, 0.0)
    prob_seguir = np.clip(df["aderencia_esperada"].to_numpy() + ajuste_valor, 0.20, 0.99)

    segue = rng.random(len(df)) < prob_seguir
    acao_inversa = np.where(df["acao_recomendada"].to_numpy() == "acordo", "defesa", "acordo")
    df["acao_tomada"] = np.where(segue, df["acao_recomendada"].to_numpy(), acao_inversa)
    df["aderente"] = (df["acao_tomada"] == df["acao_recomendada"]).astype("int8")
    return df


def gerar_razao_override(df: pd.DataFrame, rng: np.random.Generator) -> pd.Series:
    """Atribui razão de override apenas quando aderente == 0."""
    razoes = rng.choice(RAZOES_OVERRIDE, size=len(df), p=PROBS_RAZOES)
    return pd.Series(
        np.where(df["aderente"].to_numpy() == 0, razoes, None),
        index=df.index,
        dtype="object",
    )


def gerar_valor_proposto(df: pd.DataFrame, rng: np.random.Generator) -> np.ndarray:
    """Valor proposto = valor recomendado × ruído normal (~±15%). NaN se não houve acordo."""
    ruido = rng.normal(1.0, 0.15, size=len(df))
    base_recomendado = df["valor_acordo_recomendado"].to_numpy()
    fallback = df["valor_causa"].to_numpy() * ACORDO_PCT_CAUSA
    base = np.where(np.isnan(base_recomendado), fallback, base_recomendado)
    proposto = base * ruido
    mask_acordo = df["acao_tomada"].to_numpy() == "acordo"
    return np.where(mask_acordo, np.round(proposto, 2), np.nan)


def gerar_resultado_negociacao(df: pd.DataFrame, rng: np.random.Generator) -> np.ndarray:
    """Resultado categorizado por ratio proposto/causa, vetorizado via pd.cut."""
    proposto = df["valor_acordo_proposto"].to_numpy()
    causa = df["valor_causa"].to_numpy()
    ratio = np.where(np.isnan(proposto), np.nan, proposto / causa)

    faixa = pd.cut(
        pd.Series(ratio),
        bins=[-np.inf, 0.25, 0.40, np.inf],
        labels=["baixo", "medio", "alto"],
    )

    probs_por_faixa = {
        "baixo": [0.35, 0.35, 0.30],
        "medio": [0.65, 0.25, 0.10],
        "alto": [0.80, 0.15, 0.05],
    }
    resultados = np.array(["aceito", "contraproposta", "rejeitado"])

    out = np.full(len(df), None, dtype=object)
    for label, probs in probs_por_faixa.items():
        mask = (faixa == label).to_numpy()
        k = int(mask.sum())
        if k:
            out[mask] = rng.choice(resultados, size=k, p=probs)
    return out


def build() -> pd.DataFrame:
    """Pipeline completo: carrega 60k e encadeia as etapas vetorizadas."""
    rng = np.random.default_rng(SEED)

    df = pd.read_parquet(CASOS_60K).copy()

    advogados = gerar_advogados(rng)
    idx_adv = rng.integers(0, len(advogados), size=len(df))
    df["advogado_id"] = advogados["advogado_id"].to_numpy()[idx_adv]
    df["advogado_nome"] = advogados["advogado_nome"].to_numpy()[idx_adv]
    df["numero_oab"] = advogados["numero_oab"].to_numpy()[idx_adv]
    df["escritorio_id"] = advogados["escritorio_id"].to_numpy()[idx_adv]
    df["escritorio_nome"] = advogados["escritorio_nome"].to_numpy()[idx_adv]
    df["regiao"] = advogados["regiao"].to_numpy()[idx_adv]
    df["aderencia_esperada"] = advogados["aderencia_esperada"].to_numpy()[idx_adv]

    # Cidade-sede vem do catálogo de escritórios (1-para-1 com escritorio_id).
    cidade_map = dict(zip(ESCRITORIOS["escritorio_id"], ESCRITORIOS["cidade_sede"]))
    df["cidade_sede_escritorio"] = df["escritorio_id"].map(cidade_map)

    data_distribuicao, data_decisao, tempo_min = gerar_datas(rng, len(df))
    df["data_distribuicao"] = data_distribuicao.to_numpy()
    df["data_decisao"] = data_decisao.to_numpy()
    df["tempo_decisao_min"] = tempo_min

    df = gerar_recomendacao_mock(df)
    df = gerar_acao_tomada(df, rng)
    df["razao_override"] = gerar_razao_override(df, rng)
    df["valor_acordo_proposto"] = gerar_valor_proposto(df, rng)
    df["resultado_negociacao"] = gerar_resultado_negociacao(df, rng)

    return df


def build_and_save(out_path=CASOS_ENRIQUECIDOS) -> pd.DataFrame:
    df = build()
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False)
    return df


if __name__ == "__main__":
    df = build_and_save()
    print(f"Salvo: {CASOS_ENRIQUECIDOS}")
    print(f"Shape: {df.shape}")
    print(f"Colunas ({len(df.columns)}): {df.columns.tolist()}")
    print(f"\nTaxa de aderência geral: {df['aderente'].mean():.2%}")
    print("\nEscritórios (id, nome, cidade, aderência base):")
    print(ESCRITORIOS[["escritorio_id", "escritorio_nome", "cidade_sede", "aderencia_base"]])
    print("\nAmostra de advogados sorteados no dataset:")
    print(
        df[["advogado_id", "advogado_nome", "numero_oab", "escritorio_nome"]]
        .drop_duplicates("advogado_id")
        .sort_values("advogado_id")
        .head(10)
        .to_string(index=False)
    )
    print("\nAderência por escritório:")
    print(
        df.groupby(["escritorio_id", "escritorio_nome"])["aderente"]
        .agg(["mean", "count"])
        .sort_values("mean")
    )
    print("\nDistribuição de razões de override:")
    print(df.loc[df["aderente"] == 0, "razao_override"].value_counts(normalize=True))
    print("\nDistribuição de resultado_negociacao:")
    print(df["resultado_negociacao"].value_counts(dropna=False))
