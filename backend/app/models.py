from datetime import datetime
from enum import StrEnum
from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base
class UserRole(StrEnum):
    CLIENT = "client"
    ANALYST = "analyst"
    UNDERWRITER = "underwriter"
class ApplicationStatus(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    INTAKE = "intake"
    ENRICHMENT = "enrichment"
    SCORING = "scoring"
    DECISION = "decision"
    NEED_INFO = "need_info"
    OFFERED = "offered"
    DOCUMENTS = "documents"
    DISBURSEMENT = "disbursement"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
class DecisionCode(StrEnum):
    APPROVE = "approve"
    APPROVE_WITH_CHANGES = "approve_with_changes"
    NEED_INFO = "need_info"
    REJECT = "reject"
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(160))
    role: Mapped[str] = mapped_column(String(32))
    password_hash: Mapped[str] = mapped_column(String(255))
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"), nullable=True)
    job_title: Mapped[str] = mapped_column(String(120), default="Представитель")
    company: Mapped["Company | None"] = relationship(back_populates="users")
class Company(Base):
    __tablename__ = "companies"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    inn: Mapped[str] = mapped_column(String(12), unique=True, index=True)
    ogrn: Mapped[str] = mapped_column(String(15))
    legal_name: Mapped[str] = mapped_column(String(255))
    short_name: Mapped[str] = mapped_column(String(120))
    legal_form: Mapped[str] = mapped_column(String(32))
    okved: Mapped[str] = mapped_column(String(16))
    okved_name: Mapped[str] = mapped_column(String(255))
    region: Mapped[str] = mapped_column(String(120))
    address: Mapped[str] = mapped_column(String(255))
    registration_date: Mapped[str] = mapped_column(String(32))
    employees: Mapped[int] = mapped_column(Integer)
    revenue_last_year: Mapped[int] = mapped_column(Integer)
    revenue_prev_year: Mapped[int] = mapped_column(Integer)
    profit_last_year: Mapped[int] = mapped_column(Integer)
    existing_debt: Mapped[int] = mapped_column(Integer)
    monthly_turnover: Mapped[int] = mapped_column(Integer)
    tax_regime: Mapped[str] = mapped_column(String(64))
    profile_tag: Mapped[str] = mapped_column(String(32))
    users: Mapped[list[User]] = relationship(back_populates="company")
    applications: Mapped[list["Application"]] = relationship(back_populates="company")
class Product(Base):
    __tablename__ = "products"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    short_name: Mapped[str] = mapped_column(String(80))
    purpose_hint: Mapped[str] = mapped_column(Text)
    min_amount: Mapped[int] = mapped_column(Integer)
    max_amount: Mapped[int] = mapped_column(Integer)
    min_term_months: Mapped[int] = mapped_column(Integer)
    max_term_months: Mapped[int] = mapped_column(Integer)
    base_rate: Mapped[float] = mapped_column(Float)
    collateral_required: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str] = mapped_column(Text)
    suitable_for: Mapped[list] = mapped_column(JSON)
class Application(Base):
    __tablename__ = "applications"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[str] = mapped_column(String(24), unique=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    applicant_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"))
    status: Mapped[str] = mapped_column(String(32), index=True)
    amount: Mapped[int] = mapped_column(Integer)
    term_months: Mapped[int] = mapped_column(Integer)
    purpose: Mapped[str] = mapped_column(String(64))
    purpose_details: Mapped[str] = mapped_column(Text)
    offered_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    offered_term_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    offered_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    decision_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    info_request: Mapped[str | None] = mapped_column(Text, nullable=True)
    client_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    risk_band: Mapped[str | None] = mapped_column(String(16), nullable=True)
    score_breakdown: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    enrichment: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    signed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    company: Mapped[Company] = relationship(back_populates="applications")
    applicant: Mapped[User] = relationship()
    product: Mapped[Product] = relationship()
    events: Mapped[list["ApplicationEvent"]] = relationship(back_populates="application")
class ApplicationEvent(Base):
    __tablename__ = "application_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"), index=True)
    actor: Mapped[str] = mapped_column(String(80))
    stage: Mapped[str] = mapped_column(String(32))
    title: Mapped[str] = mapped_column(String(160))
    detail: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    application: Mapped[Application] = relationship(back_populates="events")
class NewsItem(Base):
    __tablename__ = "news_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(40))
    audience_tags: Mapped[list] = mapped_column(JSON)
    okved_prefixes: Mapped[list] = mapped_column(JSON)
    status_hooks: Mapped[list] = mapped_column(JSON)
    product_ids: Mapped[list] = mapped_column(JSON)
    priority: Mapped[int] = mapped_column(Integer, default=50)
    published_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)