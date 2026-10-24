from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    job_title: str
    company_id: int | None
    model_config = {"from_attributes": True}
class CompanyOut(BaseModel):
    id: int
    inn: str
    ogrn: str
    legal_name: str
    short_name: str
    legal_form: str
    okved: str
    okved_name: str
    region: str
    address: str
    registration_date: str
    employees: int
    revenue_last_year: int
    revenue_prev_year: int
    profit_last_year: int
    existing_debt: int
    monthly_turnover: int
    tax_regime: str
    profile_tag: str
    model_config = {"from_attributes": True}
class ProductOut(BaseModel):
    id: str
    name: str
    short_name: str
    purpose_hint: str
    min_amount: int
    max_amount: int
    min_term_months: int
    max_term_months: int
    base_rate: float
    collateral_required: bool
    description: str
    suitable_for: list[Any]
    model_config = {"from_attributes": True}
class RecommendRequest(BaseModel):
    purpose: str
    amount: int
    urgency: str = "normal"
class ApplicationCreate(BaseModel):
    product_id: str
    amount: int = Field(gt=0)
    term_months: int = Field(gt=0)
    purpose: str
    purpose_details: str
class InfoReply(BaseModel):
    comment: str
class ManualDecision(BaseModel):
    code: str
    reason: str
    offered_amount: int | None = None
    offered_term_months: int | None = None
    offered_rate: float | None = None
    info_request: str | None = None
class EventOut(BaseModel):
    id: int
    actor: str
    stage: str
    title: str
    detail: str
    created_at: datetime
    model_config = {"from_attributes": True}
class ApplicationOut(BaseModel):
    id: int
    public_id: str
    company_id: int
    applicant_id: int
    product_id: str
    status: str
    amount: int
    term_months: int
    purpose: str
    purpose_details: str
    offered_amount: int | None
    offered_term_months: int | None
    offered_rate: float | None
    decision_code: str | None
    decision_reason: str | None
    info_request: str | None
    client_comment: str | None
    score: int | None
    risk_band: str | None
    score_breakdown: dict | None
    enrichment: dict | None
    signed: bool
    created_at: datetime
    updated_at: datetime
    events: list[EventOut] = []
    product: ProductOut | None = None
    company: CompanyOut | None = None
    model_config = {"from_attributes": True}
class NewsOut(BaseModel):
    id: int
    title: str
    body: str
    category: str
    published_at: datetime
    why: str | None = None
    model_config = {"from_attributes": True}
class MeResponse(BaseModel):
    user: UserOut
    company: CompanyOut | None