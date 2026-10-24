"""Simulated FNS Transparent Business adapter."""
from typing import Any
FNS: dict[str, dict[str, Any]] = {
    "7701234567": {
        "tax_arrears": False,
        "disqualified_director": False,
        "invalid_address": False,
        "special_tax_regime": "УСН доходы минус расходы",
        "employees_range": "15-20",
        "okved_match": True,
        "risk_flags": [],
    },
    "540812345678": {
        "tax_arrears": False,
        "disqualified_director": False,
        "invalid_address": False,
        "special_tax_regime": "Патент + УСН",
        "employees_range": "3-5",
        "okved_match": True,
        "risk_flags": ["thin_financials"],
    },
    "7812345678": {
        "tax_arrears": True,
        "disqualified_director": False,
        "invalid_address": False,
        "special_tax_regime": "ОСНО",
        "employees_range": "40-50",
        "okved_match": True,
        "risk_flags": ["tax_arrears", "mass_address", "high_inquiries"],
    },
}
def fetch_transparent_business(inn: str) -> dict[str, Any]:
    record = FNS.get(inn)
    if not record:
        return {"source": "FNS-MOCK", "found": False, "inn": inn, "risk_flags": ["no_data"]}
    return {"source": "FNS-MOCK", "found": True, "inn": inn, **record}