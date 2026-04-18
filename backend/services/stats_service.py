from __future__ import annotations

import csv
import sys
from pathlib import Path


TOTAL_CASES_DEFAULT = 60000
RESULTS_SHEET_NAME = "Resultados dos processos"
SUBSIDIES_SHEET_NAME = "Subsídios disponibilizados"
RESULTS_CSV_NAME = "Hackaton_Enter_Base_Candidatos.xlsx - Resultados dos processos.csv"
SUBSIDIES_CSV_NAME = "Hackaton_Enter_Base_Candidatos.xlsx - Subsídios disponibilizados.csv"
WORKBOOK_NAME = "Hackaton_Enter_Base_Candidatos.xlsx"

HIGH_RISK_UFS = frozenset({"AM", "AP"})
MEDIUM_RISK_UFS = frozenset({"GO", "RS", "BA", "RJ", "ES", "DF", "AL", "SP", "PE"})
CRITICAL_SUBSIDY_COLUMNS = ("Contrato", "Extrato", "Comprovante de crédito")

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
    Carrega a base histórica para a API e, quando possível, calcula a projeção
    de custo caso a política de acordos fosse seguida em toda a carteira.
    """
    csv_pair = _resolve_csv_pair()
    if csv_pair is not None:
        results_rows = _load_rows_from_csv(csv_pair[0])
        subsidy_rows = _load_rows_from_csv(csv_pair[1])
        headers = list(results_rows[0].keys()) if results_rows else None
        projection = calculate_policy_projection(results_rows, subsidy_rows, source="csv")
        return headers, results_rows, projection

    workbook_path = _resolve_workbook_path()
    if workbook_path is not None:
        results_rows = _load_rows_from_xlsx(workbook_path, RESULTS_SHEET_NAME)
        subsidy_rows = _load_rows_from_xlsx(workbook_path, SUBSIDIES_SHEET_NAME)
        headers = list(results_rows[0].keys()) if results_rows else None
        projection = calculate_policy_projection(results_rows, subsidy_rows, source="xlsx")
        return headers, results_rows, projection

    return None, [], None


def calculate_policy_projection(result_rows, subsidy_rows, *, source="historical", engine=None):
    subsidy_by_case = {}
    for row in subsidy_rows:
        case_number = str(
            row.get("Número do processo") or row.get("Número do processos") or ""
        ).strip()
        if case_number:
            subsidy_by_case[case_number] = row

    if not subsidy_by_case:
        return None

    if engine is not None:
        return _calculate_projection_with_engine_object(result_rows, subsidy_by_case, source, engine)

    runtime, runtime_error = _build_policy_runtime()
    if runtime is not None:
        return _calculate_projection_with_runtime(result_rows, subsidy_by_case, source, runtime)

    return _calculate_projection_rule_only(result_rows, subsidy_by_case, source, runtime_error)


def _calculate_projection_with_runtime(result_rows, subsidy_by_case, source, runtime):
    actual_total_cost = 0.0
    projected_total_cost = 0.0
    projected_agreement_total = 0.0
    projected_agreement_cases = 0
    current_agreement_cases = 0
    matched_cases = 0
    rule_decision_cases = 0
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

        critical_count = sum(_parse_binary_flag(subsidy_row.get(column)) for column in CRITICAL_SUBSIDY_COLUMNS)
        uf_cluster = _cluster_for_uf(row.get("UF"))

        if critical_count <= 1:
            rule_decision_cases += 1
            agreement_value = _pricing_target_value(runtime, claim_value, critical_count, row.get("UF"))
            projected_agreement_cases += 1
            projected_agreement_total += agreement_value
            projected_total_cost += agreement_value
            continue

        if uf_cluster == "ALTO" and critical_count <= 2:
            rule_decision_cases += 1
            agreement_value = _pricing_target_value(runtime, claim_value, critical_count, row.get("UF"))
            projected_agreement_cases += 1
            projected_agreement_total += agreement_value
            projected_total_cost += agreement_value
            continue

        if critical_count >= 3:
            rule_decision_cases += 1
            projected_total_cost += actual_cost
            continue

        model_records.append(
            {
                "claim_value": claim_value,
                "actual_cost": actual_cost,
                "critical_count": critical_count,
                "uf": row.get("UF"),
                "feature_row": _build_feature_row(runtime, row, subsidy_row, uf_cluster),
            }
        )

    if model_records:
        frame = runtime["pandas"].DataFrame(
            [record["feature_row"] for record in model_records],
            columns=list(runtime["feature_columns"]),
        )
        probabilities = runtime["model"].predict_proba(frame)[:, 1]

        for record, probability in zip(model_records, probabilities):
            gray_zone_cases += int(runtime["gray_zone"][0] <= probability <= runtime["gray_zone"][1])
            if probability >= runtime["threshold"]:
                agreement_value = _pricing_target_value(
                    runtime,
                    record["claim_value"],
                    record["critical_count"],
                    record["uf"],
                )
                projected_agreement_cases += 1
                projected_agreement_total += agreement_value
                projected_total_cost += agreement_value
            else:
                projected_total_cost += record["actual_cost"]

    model_decision_cases = len(model_records)
    return _finalize_projection(
        source=source,
        projection_type="hybrid_policy_engine_v2_1",
        actual_total_cost=actual_total_cost,
        projected_total_cost=projected_total_cost,
        projected_agreement_total=projected_agreement_total,
        projected_agreement_cases=projected_agreement_cases,
        current_agreement_cases=current_agreement_cases,
        matched_cases=matched_cases,
        rule_decision_cases=rule_decision_cases,
        model_decision_cases=model_decision_cases,
        gray_zone_cases=gray_zone_cases,
        assumptions=[
            "A simulacao usa o PolicyEngine real: regras fixas + XGBoost para os casos intermediarios.",
            "Casos enviados a acordo usam o valor-alvo calculado pelo pricing da politica.",
            "Casos mantidos em defesa preservam o resultado historico observado na base.",
        ],
    )


def _calculate_projection_rule_only(result_rows, subsidy_by_case, source, runtime_error):
    actual_total_cost = 0.0
    projected_total_cost = 0.0
    projected_agreement_total = 0.0
    projected_agreement_cases = 0
    current_agreement_cases = 0
    matched_cases = 0

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

        critical_count = sum(_parse_binary_flag(subsidy_row.get(column)) for column in CRITICAL_SUBSIDY_COLUMNS)
        uf_cluster = _cluster_for_uf(row.get("UF"))
        recommendation = _project_policy_decision(critical_count, uf_cluster)

        if recommendation == "ACORDO":
            agreement_value = _project_agreement_value(claim_value, critical_count, uf_cluster)
            projected_agreement_cases += 1
            projected_agreement_total += agreement_value
            projected_total_cost += agreement_value
        else:
            projected_total_cost += actual_cost

    assumptions = [
        "Casos enviados a acordo usam o valor-alvo da politica como desembolso estimado.",
        "Casos mantidos em defesa preservam o resultado historico observado na base.",
        "Sem o modelo carregado, a simulacao usa apenas a parte deterministica da politica.",
    ]
    if runtime_error:
        assumptions.append(f"Fallback ativado por indisponibilidade do modelo: {runtime_error}")

    return _finalize_projection(
        source=source,
        projection_type="rule_based_policy_v2_1",
        actual_total_cost=actual_total_cost,
        projected_total_cost=projected_total_cost,
        projected_agreement_total=projected_agreement_total,
        projected_agreement_cases=projected_agreement_cases,
        current_agreement_cases=current_agreement_cases,
        matched_cases=matched_cases,
        rule_decision_cases=matched_cases,
        model_decision_cases=0,
        gray_zone_cases=0,
        assumptions=assumptions,
    )


def _calculate_projection_with_engine_object(result_rows, subsidy_by_case, source, engine):
    actual_total_cost = 0.0
    projected_total_cost = 0.0
    projected_agreement_total = 0.0
    projected_agreement_cases = 0
    current_agreement_cases = 0
    matched_cases = 0
    rule_decision_cases = 0
    model_decision_cases = 0
    gray_zone_cases = 0

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

        decision = engine.evaluate(_build_case_payload(row, subsidy_row, claim_value))
        if decision.source == "MODEL":
            model_decision_cases += 1
        else:
            rule_decision_cases += 1
        gray_zone_cases += int(decision.gray_zone)

        if decision.recommendation == "ACORDO":
            agreement_value = decision.pricing.target_value if decision.pricing else 0.0
            projected_agreement_cases += 1
            projected_agreement_total += agreement_value
            projected_total_cost += agreement_value
        else:
            projected_total_cost += actual_cost

    return _finalize_projection(
        source=source,
        projection_type="hybrid_policy_engine_v2_1",
        actual_total_cost=actual_total_cost,
        projected_total_cost=projected_total_cost,
        projected_agreement_total=projected_agreement_total,
        projected_agreement_cases=projected_agreement_cases,
        current_agreement_cases=current_agreement_cases,
        matched_cases=matched_cases,
        rule_decision_cases=rule_decision_cases,
        model_decision_cases=model_decision_cases,
        gray_zone_cases=gray_zone_cases,
        assumptions=[
            "A simulacao usa o PolicyEngine real: regras fixas + XGBoost para os casos intermediarios.",
            "Casos enviados a acordo usam o valor-alvo calculado pelo pricing da politica.",
            "Casos mantidos em defesa preservam o resultado historico observado na base.",
        ],
    )


def _finalize_projection(
    *,
    source,
    projection_type,
    actual_total_cost,
    projected_total_cost,
    projected_agreement_total,
    projected_agreement_cases,
    current_agreement_cases,
    matched_cases,
    rule_decision_cases,
    model_decision_cases,
    gray_zone_cases,
    assumptions,
):
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
        "projection_type": projection_type,
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
        "assumptions": assumptions,
    }


def _build_policy_runtime():
    model_path = REPO_ROOT / "artefatos" / "modelo_xgboost.pkl"
    if not model_path.exists():
        return None, "modelo_xgboost.pkl ausente"

    try:
        if str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))

        import joblib
        import pandas
        from src.policy.constants import DEFAULT_MODEL_THRESHOLD, FEATURE_COLUMNS, MODEL_GRAY_ZONE
        from src.policy.normalization import is_golpe_sub_assunto
        from src.policy.pricing import calculate_agreement_pricing

        model = joblib.load(model_path)
        return {
            "model": model,
            "pandas": pandas,
            "feature_columns": tuple(FEATURE_COLUMNS),
            "threshold": float(DEFAULT_MODEL_THRESHOLD),
            "gray_zone": tuple(MODEL_GRAY_ZONE),
            "is_golpe_sub_assunto": is_golpe_sub_assunto,
            "calculate_agreement_pricing": calculate_agreement_pricing,
        }, None
    except Exception as exc:
        return None, str(exc)


def _pricing_target_value(runtime, claim_value, critical_count, uf):
    if claim_value <= 0:
        return 0.0

    pricing = runtime["calculate_agreement_pricing"](
        claim_value,
        critical_count,
        uf=uf,
    )
    return float(pricing.target_value)


def _build_feature_row(runtime, result_row, subsidy_row, uf_cluster):
    return {
        "Contrato": _parse_binary_flag(subsidy_row.get("Contrato")),
        "Extrato": _parse_binary_flag(subsidy_row.get("Extrato")),
        "Comprovante de crédito": _parse_binary_flag(subsidy_row.get("Comprovante de crédito")),
        "Dossiê": _parse_binary_flag(subsidy_row.get("Dossiê")),
        "Demonstrativo de evolução da dívida": _parse_binary_flag(
            subsidy_row.get("Demonstrativo de evolução da dívida")
        ),
        "Laudo referenciado": _parse_binary_flag(subsidy_row.get("Laudo referenciado")),
        "is_golpe": int(runtime["is_golpe_sub_assunto"](result_row.get("Sub-assunto"))),
        "uf_alto": int(uf_cluster == "ALTO"),
        "uf_medio": int(uf_cluster == "MEDIO"),
    }


def _build_case_payload(result_row, subsidy_row, claim_value):
    return {
        "case_id": result_row.get("Número do processo"),
        "uf": result_row.get("UF"),
        "value_of_claim": claim_value,
        "sub_subject": result_row.get("Sub-assunto"),
        "contrato": _parse_binary_flag(subsidy_row.get("Contrato")),
        "extrato": _parse_binary_flag(subsidy_row.get("Extrato")),
        "comprovante_credito": _parse_binary_flag(subsidy_row.get("Comprovante de crédito")),
        "dossie": _parse_binary_flag(subsidy_row.get("Dossiê")),
        "demonstrativo_divida": _parse_binary_flag(subsidy_row.get("Demonstrativo de evolução da dívida")),
        "laudo_referenciado": _parse_binary_flag(subsidy_row.get("Laudo referenciado")),
    }


def _resolve_csv_pair():
    for base_dir in _candidate_data_dirs():
        results_path = base_dir / RESULTS_CSV_NAME
        subsidies_path = base_dir / SUBSIDIES_CSV_NAME
        if results_path.exists() and subsidies_path.exists():
            return results_path, subsidies_path
    return None


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


def _candidate_data_dirs():
    return [
        REPO_ROOT / "data",
        REPO_ROOT.parent / "Grupo-9-Hackathon" / "data",
        REPO_ROOT.parent / "Docs Hackkaton" / "drive-dowload",
    ]


def _load_rows_from_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        return [{key: (value if value is not None else "") for key, value in row.items()} for row in reader]


def _load_rows_from_xlsx(path, sheet_name):
    import openpyxl

    workbook = openpyxl.load_workbook(path, read_only=True)
    worksheet = workbook[sheet_name]

    rows = []
    headers = None
    for index, row in enumerate(worksheet.iter_rows(values_only=True)):
        if index == 0:
            headers = [str(cell) for cell in row]
            continue
        rows.append({
            headers[column_index]: (value if value is not None else "")
            for column_index, value in enumerate(row)
        })

    workbook.close()
    return rows


def _parse_binary_flag(value):
    return 1 if str(value).strip() in {"1", "true", "True", "SIM", "sim"} else 0


def _parse_brazilian_money(value):
    if value in (None, ""):
        return 0.0
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


def _cluster_for_uf(uf):
    uf_code = str(uf or "").strip().upper()
    if uf_code in HIGH_RISK_UFS:
        return "ALTO"
    if uf_code in MEDIUM_RISK_UFS:
        return "MEDIO"
    return "BAIXO"


def _project_policy_decision(critical_count, uf_cluster):
    if critical_count <= 1:
        return "ACORDO"
    if uf_cluster == "ALTO" and critical_count <= 2:
        return "ACORDO"
    return "DEFESA"


def _project_agreement_value(claim_value, critical_count, uf_cluster):
    if claim_value <= 0:
        return 0.0

    factor = 0.30
    if critical_count <= 1:
        factor += 0.03
    elif critical_count >= 3:
        factor -= 0.03

    if uf_cluster == "ALTO":
        factor += 0.02
    elif uf_cluster == "BAIXO":
        factor -= 0.02

    factor = max(0.24, min(factor, 0.40))
    return round(claim_value * factor, 2)
