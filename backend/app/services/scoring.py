from typing import Any
from app.models import Application, Company, Product
def _clamp(value: int, lo: int = 0, hi: int = 200) -> int:
    return max(lo, min(hi, value))
def score_application(
    company: Company,
    application: Application,
    product: Product,
    enrichment: dict[str, Any],
) -> dict[str, Any]:
    bki = enrichment["bki"]
    fns = enrichment["fns"]
    egrul = enrichment["egrul"]
    revenue_trend = 0
    if company.revenue_prev_year:
        growth = (company.revenue_last_year - company.revenue_prev_year) / company.revenue_prev_year
        revenue_trend = int(growth * 100)
    margin = company.profit_last_year / max(company.revenue_last_year, 1)
    debt_load = company.existing_debt / max(company.revenue_last_year, 1)
    amount_to_revenue = application.amount / max(company.revenue_last_year, 1)
    factors = [
        {
            "code": "revenue_stability",
            "title": "Динамика выручки",
            "value": f"{revenue_trend:+.0f}%",
            "points": _clamp(80 + revenue_trend * 2, 20, 160),
            "note": "Рост выручки снижает риск, сжатие — повышает.",
        },
        {
            "code": "profitability",
            "title": "Рентабельность",
            "value": f"{margin:.0%}",
            "points": _clamp(int(70 + margin * 250), 10, 150),
            "note": "Операционная прибыль показывает запас прочности.",
        },
        {
            "code": "debt_load",
            "title": "Долговая нагрузка",
            "value": f"{debt_load:.0%} к выручке",
            "points": _clamp(int(140 - debt_load * 220), 0, 160),
            "note": "Существующие обязательства ограничивают ёмкость нового кредита.",
        },
        {
            "code": "credit_history",
            "title": "Кредитная история",
            "value": f"балл БКИ {bki.get('score', 0)}, просрочки 90+ {bki.get('overdue_90d', 0)}",
            "points": _clamp(int((bki.get("score") or 600) / 5 - bki.get("overdue_90d", 0) * 40), 0, 180),
            "note": "Платёжная дисциплина — прямой сигнал риска.",
        },
        {
            "code": "request_fit",
            "title": "Соразмерность запроса",
            "value": f"{amount_to_revenue:.0%} годовой выручки",
            "points": _clamp(int(130 - amount_to_revenue * 160), 0, 140),
            "note": "Запрос сильно выше оборота повышает вероятность отказа или урезания.",
        },
        {

            "code": "company_age",
            "title": "Срок жизни бизнеса",
            "value": f"{egrul.get('registration_years', 1)} лет",
            "points": _clamp(40 + int(egrul.get("registration_years", 1)) * 12, 20, 100),
            "note": "Молодой бизнес имеет меньше наблюдаемой истории.",
        },
        {
            "code": "tax_and_legal",
            "title": "Налоговые и реестровые флаги",
            "value": ", ".join(fns.get("risk_flags") or ["чисто"]) ,
            "points": 90
            - (40 if fns.get("tax_arrears") else 0)
            - (25 if egrul.get("mass_address") else 0)
            - (50 if egrul.get("liquidating") else 0)
            - (15 if "thin_financials" in (fns.get("risk_flags") or []) else 0),
            "note": "Активные налоговые и адресные риски ухудшают оценку.",
        },
    ]
    raw = sum(int(item["points"]) for item in factors)
    score = max(250, min(980, raw))
    if score >= 760:
        band = "low"
        band_name = "Низкий риск"
    elif score >= 620:
        band = "medium"
        band_name = "Умеренный риск"
    else:
        band = "high"
        band_name = "Повышенный риск"
    return {
        "score": score,
        "risk_band": band,
        "risk_band_name": band_name,
        "factors": factors,
        "product_context": {
            "product_id": product.id,
            "base_rate": product.base_rate,
            "collateral_required": product.collateral_required,
            "note": "Скоринг оценивает риск заёмщика. Итоговое решение дополнительно учитывает продукт, сумму и внутренние лимиты.",
        },
    }