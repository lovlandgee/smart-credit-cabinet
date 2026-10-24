from __future__ import annotations

from typing import Any

import httpx

from app.config import settings


def build_features(company: Any, application: Any, enrichment: dict[str, Any]) -> dict[str, float]:
    bki, egrul, fns = enrichment["bki"], enrichment["egrul"], enrichment["fns"]
    growth = ((company.revenue_last_year - company.revenue_prev_year) / company.revenue_prev_year) if company.revenue_prev_year else 0.0
    return {
        "revenue_growth": growth,
        "profit_margin": company.profit_last_year / max(company.revenue_last_year, 1),
        "debt_load": company.existing_debt / max(company.revenue_last_year, 1),
        "amount_to_revenue": application.amount / max(company.revenue_last_year, 1),
        "bki_score": float(bki.get("score", 600)),
        "overdue_90d": float(bki.get("overdue_90d", 0)),
        "registration_years": float(egrul.get("registration_years", 1)),
        "tax_arrears": float(bool(fns.get("tax_arrears"))),
        "legal_risk_flags": float(len(fns.get("risk_flags") or [])),
    }


def predict_risk(company: Any, application: Any, enrichment: dict[str, Any]) -> dict[str, Any]:
    response = httpx.post(
        f"{settings.ml_service_url.rstrip('/')}/predict",
        json={"features": build_features(company, application, enrichment)},
        timeout=settings.ml_request_timeout,
    )
    response.raise_for_status()
    return response.json()
