from __future__ import annotations

import sys
from pathlib import Path


TOTAL_CASES_DEFAULT = 60000
RESULTS_SHEET_NAME = "Resultados dos processos"
SUBSIDIES_SHEET_NAME = "Subsídios disponibilizados"
WORKBOOK_NAME = "Hackaton_Enter_Base_Candidatos.xlsx"
REPO_ROOT = Path(__file__).resolve().parents[2]


def calculate_macro_stats(raw_data, *, policy_projection=None):
    """
    Calcula as taxas macro de sucesso e derrota baseadas nos dados detalhados.
    """
    success_rate = sum(item["value"] for item in raw_data if item["macro"] == "Exito")
    loss_rate = sum(item["value"] for item in raw_data if item["macro"] == "Não Êxito")

    success_rate = round(success_rate, 1)
    loss_rate = round(loss_rate, 1)

    return {
        "total_cases": TOTAL_CASES_DEFAULT,
        "success_rate": success_rate,
        "loss_rate": loss_rate,
        "agreement_rate": 0.5,
        "detailed": raw_data,
        "policy_projection": policy_projection,
    }


def load_historical_snapshot():
    """
    Carrega a base histórica para a API e calcula a projeção de custo
    caso a política de acordos fosse aplicada na carteira.
    """
    workbook_path = _resolve_workbook_path()
    if workbook_path is None:
        return None, [], None

    results_rows = _load_rows_from_xlsx(workbook_path, RESULTS_SHEET_NAME)
    subsidy_rows = _load_rows_from_xlsx(workbook_path, SUBSIDIES_SHEET_NAME)
    headers = list(results_rows[0].keys()) if results_rows else None
    projection = calculate_policy_projection(results_rows, subsidy_rows, source="xlsx")
    return headers, results_rows, projection


def calculate_policy_projection(result_rows, subsidy_rows, *, source="historical"):
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

    import joblib
    import pandas
    from src.policy.constants import DEFAULT_MODEL_THRESHOLD, FEATURE_COLUMNS, MODEL_GRAY_ZONE
    from src.policy.normalization import cluster_for_uf, is_golpe_sub_assunto
    from src.policy.pricing import calculate_agreement_pricing

    subsidy_by_case = {}
    for row in subsidy_rows:
        case_number = str(
            row.get("Número do processo") or row.get("Número do processos") or ""
        ).strip()
        if case_number:
            subsidy_by_case[case_number] = row

    if not subsidy_by_case:
        return None

    model_path = REPO_ROOT / "artefatos" / "modelo_xgboost.pkl"
    model = joblib.load(model_path) if model_path.exists() else None
    actual_total_cost = 0.0
    projected_total_cost = 0.0
    projected_agreement_total = 0.0
    projected_agreement_cases = 0
    current_agreement_cases = 0
    matched_cases = 0
    rule_decision_cases = 0
    model_decision_cases = 0
    gray_zone_cases = 0
    model_records = []

    for row in result_rows:
        case_number = str(row.get("Número do processo", "")).strip()
        if not case_number:
            continue

        subsidy_row = subsidy_by_case.get(case_number)
        if subsidy_row is None:
            continue

        matched_cases += 1
        claim_value = _parse_brazilian_money(row.get("Valor da causa"))
        actual_cost = _parse_brazilian_money(row.get("Valor da condenação/indenização"))
        actual_total_cost += actual_cost

        if _normalize_text(row.get("Resultado micro")) == "acordo":
            current_agreement_cases += 1

        critical_count = sum(
            _parse_binary_flag(subsidy_row.get(column))
            for column in ("Contrato", "Extrato", "Comprovante de crédito")
        )
        uf = row.get("UF")
        uf_cluster = cluster_for_uf(uf)

        if critical_count <= 1 or (uf_cluster == "ALTO" and critical_count <= 2):
            rule_decision_cases += 1
            agreement_value = calculate_agreement_pricing(
                claim_value,
                critical_count,
                uf=uf,
            ).target_value if claim_value > 0 else 0.0
            projected_agreement_cases += 1
            projected_agreement_total += agreement_value
            projected_total_cost += agreement_value
            continue

        if critical_count >= 3 or model is None:
            rule_decision_cases += 1
            projected_total_cost += actual_cost
            continue

        model_records.append(
            {
                "actual_cost": actual_cost,
                "claim_value": claim_value,
                "critical_count": critical_count,
                "uf": uf,
                "feature_row": {
                    "Contrato": _parse_binary_flag(subsidy_row.get("Contrato")),
                    "Extrato": _parse_binary_flag(subsidy_row.get("Extrato")),
                    "Comprovante de crédito": _parse_binary_flag(subsidy_row.get("Comprovante de crédito")),
                    "Dossiê": _parse_binary_flag(subsidy_row.get("Dossiê")),
                    "Demonstrativo de evolução da dívida": _parse_binary_flag(
                        subsidy_row.get("Demonstrativo de evolução da dívida")
                    ),
                    "Laudo referenciado": _parse_binary_flag(subsidy_row.get("Laudo referenciado")),
                    "is_golpe": int(is_golpe_sub_assunto(row.get("Sub-assunto"))),
                    "uf_alto": int(uf_cluster == "ALTO"),
                    "uf_medio": int(uf_cluster == "MEDIO"),
                },
            }
        )

    if model_records:
        frame = pandas.DataFrame(
            [record["feature_row"] for record in model_records],
            columns=list(FEATURE_COLUMNS),
        )
        probabilities = model.predict_proba(frame)[:, 1]
        model_decision_cases = len(model_records)

        for record, probability in zip(model_records, probabilities):
            gray_zone_cases += int(MODEL_GRAY_ZONE[0] <= probability <= MODEL_GRAY_ZONE[1])
            if probability >= DEFAULT_MODEL_THRESHOLD:
                agreement_value = calculate_agreement_pricing(
                    record["claim_value"],
                    record["critical_count"],
                    uf=record["uf"],
                ).target_value if record["claim_value"] > 0 else 0.0
                projected_agreement_cases += 1
                projected_agreement_total += agreement_value
                projected_total_cost += agreement_value
            else:
                projected_total_cost += record["actual_cost"]

    if matched_cases == 0:
        return None

    projected_defense_cases = matched_cases - projected_agreement_cases
    estimated_savings = actual_total_cost - projected_total_cost
    estimated_savings_rate = (estimated_savings / actual_total_cost * 100.0) if actual_total_cost else 0.0
    projected_agreement_rate = projected_agreement_cases / matched_cases * 100.0
    current_agreement_rate = current_agreement_cases / matched_cases * 100.0
    projected_agreement_average = (
        projected_agreement_total / projected_agreement_cases if projected_agreement_cases else 0.0
    )

    return {
        "source": source,
        "projection_type": "hybrid_policy_engine_v2_1",
        "actual_total_cost": round(actual_total_cost, 2),
        "projected_total_cost": round(projected_total_cost, 2),
        "estimated_savings": round(estimated_savings, 2),
        "estimated_savings_rate": round(estimated_savings_rate, 1),
        "current_average_cost": round(actual_total_cost / matched_cases, 2),
        "projected_average_cost": round(projected_total_cost / matched_cases, 2),
        "current_agreement_cases": current_agreement_cases,
        "projected_agreement_cases": projected_agreement_cases,
        "projected_defense_cases": projected_defense_cases,
        "current_agreement_rate": round(current_agreement_rate, 1),
        "projected_agreement_rate": round(projected_agreement_rate, 1),
        "projected_agreement_average": round(projected_agreement_average, 2),
        "matched_cases": matched_cases,
        "rule_decision_cases": rule_decision_cases,
        "model_decision_cases": model_decision_cases,
        "gray_zone_cases": gray_zone_cases,
        "assumptions": [
            "A simulacao usa o PolicyEngine real: regras fixas + XGBoost para os casos intermediarios.",
            "Casos enviados a acordo usam o valor-alvo calculado pelo pricing da politica.",
            "Casos mantidos em defesa preservam o resultado historico observado na base.",
        ],
    }


def _resolve_workbook_path():
    candidates = [
        REPO_ROOT / "data" / WORKBOOK_NAME,
        REPO_ROOT.parent / "Grupo-9-Hackathon" / "data" / WORKBOOK_NAME,
        REPO_ROOT.parent / "Docs Hackkaton" / "drive-dowload" / WORKBOOK_NAME,
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def _load_rows_from_xlsx(path, sheet_name):
    import openpyxl

    workbook = openpyxl.load_workbook(path, read_only=True)
    worksheet = workbook[sheet_name]

    rows = []
    headers = None
    for index, row in enumerate(worksheet.iter_rows(values_only=True)):
        # A aba de subsídios vem com uma linha de legenda antes do cabecalho real.
        header_row_index = 1 if sheet_name == SUBSIDIES_SHEET_NAME else 0
        if index < header_row_index:
            continue
        if index == header_row_index:
            headers = [str(cell) for cell in row]
            continue
        rows.append(
            {
                headers[column_index]: (value if value is not None else "")
                for column_index, value in enumerate(row)
            }
        )

    workbook.close()
    return rows


def _parse_binary_flag(value):
    return 1 if str(value).strip() in {"1", "true", "True", "SIM", "sim"} else 0


def _parse_brazilian_money(value):
    if value in (None, ""):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    normalized = str(value).strip()
    if not normalized:
        return 0.0
    normalized = normalized.replace("R$", "").replace(" ", "")
    normalized = normalized.replace(".", "").replace(",", ".")
    try:
        return float(normalized)
    except ValueError:
        return 0.0


def _normalize_text(value):
    return str(value or "").strip().lower()
