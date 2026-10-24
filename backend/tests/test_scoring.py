from app.models import Application, Company, Product
from app.services.decision import decide
from app.services.scoring import score_application
def _company(**overrides) -> Company:
    data = dict(
        id=1,
        inn="7701234567",
        ogrn="1",
        legal_name="Test",
        short_name="Test",
        legal_form="ООО",
        okved="10.71",
        okved_name="x",
        region="Москва",
        address="a",
        registration_date="2022-01-01",
        employees=10,
        revenue_last_year=40_000_000,
        revenue_prev_year=32_000_000,
        profit_last_year=4_000_000,
        existing_debt=2_000_000,
        monthly_turnover=3_000_000,
        tax_regime="УСН",
        profile_tag="stable_food",
    )
    data.update(overrides)
    return Company(**data)
def _product() -> Product:
    return Product(
        id="turnover",
        name="Оборотный",
        short_name="Оборотный",
        purpose_hint="",
        min_amount=300_000,
        max_amount=8_000_000,
        min_term_months=3,
        max_term_months=18,
        base_rate=18.9,
        collateral_required=False,
        description="",
        suitable_for=[],
    )
def test_low_risk_is_approved() -> None:
    company = _company()
    application = Application(
        public_id="K-1",
        company_id=1,
        applicant_id=1,
        product_id="turnover",
        status="scoring",
        amount=2_000_000,
        term_months=12,
        purpose="working_capital",
        purpose_details="закупка муки",
    )
    enrichment = {
        "bki": {"score": 742, "overdue_90d": 0, "comment": "ok"},
        "egrul": {"registration_years": 4, "mass_address": False, "liquidating": False},
        "fns": {"tax_arrears": False, "risk_flags": []},
    }
    scoring = score_application(company, application, _product(), enrichment)
    result = decide(company, application, _product(), scoring)
    assert scoring["score"] >= 700
    assert result["code"] in {"approve", "approve_with_changes"}
def test_high_debt_can_be_rejected() -> None:
    company = _company(revenue_last_year=20_000_000, existing_debt=18_000_000, profit_last_year=-1_000_000)
    application = Application(
        public_id="K-2",
        company_id=1,
        applicant_id=1,
        product_id="turnover",
        status="scoring",
        amount=12_000_000,
        term_months=12,
        purpose="expansion",
        purpose_details="закрыть кассовый разрыв",
    )
    enrichment = {
        "bki": {"score": 500, "overdue_90d": 1, "comment": "bad"},
        "egrul": {"registration_years": 6, "mass_address": True, "liquidating": False},
        "fns": {"tax_arrears": True, "risk_flags": ["tax_arrears"]},
    }
    scoring = score_application(company, application, _product(), enrichment)
    result = decide(company, application, _product(), scoring)
    assert scoring["risk_band"] == "high"
    assert result["code"] in {"reject", "need_info"}