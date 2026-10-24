from typing import Any
from app.models import Application, Company, DecisionCode, Product
def decide(
    company: Company,
    application: Application,
    product: Product,
    scoring: dict[str, Any],
    extra_info_provided: bool = False,
) -> dict[str, Any]:
    score = scoring["score"]
    band = scoring["risk_band"]
    amount = application.amount
    term = application.term_months
    debt_load = company.existing_debt / max(company.revenue_last_year, 1)
    amount_to_revenue = amount / max(company.revenue_last_year, 1)
    rate = product.base_rate
    if band == "high" and (amount_to_revenue > 0.45 or debt_load > 0.55):
        return {
            "code": DecisionCode.REJECT,
            "reason": "Совокупность повышенной долговой нагрузки, риска по кредитной истории и размера запроса не позволяет выдать финансирование на запрошенных условиях.",
            "offered_amount": None,
            "offered_term_months": None,
            "offered_rate": None,
            "info_request": None,
        }
    if band == "high" and not extra_info_provided:
        return {
            "code": DecisionCode.NEED_INFO,
            "reason": "Автоматическая оценка недостаточна для решения: нужны пояснения по обязательствам и источникам погашения.",
            "offered_amount": None,
            "offered_term_months": None,
            "offered_rate": None,
            "info_request": "Приложите пояснение по текущим кредитам, план погашения и подтверждение оборотов за последние 3 месяца.",
        }
    offered_amount = amount
    offered_term = term
    reason_bits = []
    if amount > product.max_amount:
        offered_amount = product.max_amount
        reason_bits.append("сумма ограничена продуктовым лимитом")
    if amount_to_revenue > 0.35 and band != "low":
        offered_amount = min(offered_amount, int(company.revenue_last_year * 0.28))
        reason_bits.append("сумма приведена к обороту компании")
    if band == "medium":
        rate += 1.4
        reason_bits.append("надбавка к ставке за умеренный риск")
    if band == "high":
        rate += 3.2
        offered_amount = min(offered_amount, int(company.monthly_turnover * 4))
        reason_bits.append("сокращён лимит и повышена ставка")
    if product.collateral_required and band != "low":
        offered_term = min(term, max(product.min_term_months, term - 6))
        reason_bits.append("срок скорректирован до появления залога в полном объёме")
    offered_amount = max(product.min_amount, offered_amount)
    changed = offered_amount != amount or offered_term != term or abs(rate - product.base_rate) > 0.05
    if changed:
        return {
            "code": DecisionCode.APPROVE_WITH_CHANGES,
            "reason": "Банк готов финансировать, но на скорректированных условиях: " + "; ".join(reason_bits) + ".",
            "offered_amount": offered_amount,
            "offered_term_months": offered_term,
            "offered_rate": round(rate, 2),
            "info_request": None,
        }
    return {
        "code": DecisionCode.APPROVE,
        "reason": f"Риск {scoring['risk_band_name'].lower()}, запрос соразмерен обороту и укладывается в продуктовую политику.",
        "offered_amount": offered_amount,
        "offered_term_months": offered_term,
        "offered_rate": round(rate, 2),
        "info_request": None,
    }