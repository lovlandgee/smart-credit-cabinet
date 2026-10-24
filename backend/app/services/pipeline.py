import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from app.config import settings
from app.db import SessionLocal
from app.integrations.bki import fetch_credit_history
from app.integrations.egrul import fetch_registry
from app.integrations.fns import fetch_transparent_business
from app.models import Application, ApplicationEvent, ApplicationStatus, DecisionCode
from app.services.decision import decide
from app.services.ml_client import predict_risk
from app.services.scoring import score_application
def add_event(db: Session, application: Application, actor: str, stage: str, title: str, detail: str) -> None:
    db.add(
        ApplicationEvent(
            application_id=application.id,
            actor=actor,
            stage=stage,
            title=title,
            detail=detail,
        )
    )
    application.updated_at = datetime.utcnow()
def _set_status(application: Application, status: ApplicationStatus) -> None:
    application.status = status.value
    application.updated_at = datetime.utcnow()
async def run_pipeline(application_id: int, extra_info_provided: bool = False) -> None:
    await asyncio.to_thread(_run_pipeline_sync, application_id, extra_info_provided)
def _sleep() -> None:
    delay = settings.pipeline_step_delay_sec
    if delay > 0:
        import time
        time.sleep(delay)
def _run_pipeline_sync(application_id: int, extra_info_provided: bool) -> None:
    db = SessionLocal()
    try:
        app = db.get(Application, application_id)
        if app is None:
            return
        _set_status(app, ApplicationStatus.INTAKE)
        add_event(
            db,
            app,
            "Конвейер",
            ApplicationStatus.INTAKE,
            "Проверка комплектности",
            "Система сверила сумму, срок, цель и реквизиты компании с требованиями продукта.",
        )
        db.commit()
        _sleep()
        missing = []
        if app.amount <= 0:
            missing.append("сумма")
        if not app.purpose_details.strip():
            missing.append("описание цели")
        if missing:
            _set_status(app, ApplicationStatus.NEED_INFO)
            app.decision_code = DecisionCode.NEED_INFO
            app.info_request = "Не хватает данных: " + ", ".join(missing)
            add_event(db, app, "Конвейер", ApplicationStatus.NEED_INFO, "Заявка неполная", app.info_request)
            db.commit()
            return

        _set_status(app, ApplicationStatus.ENRICHMENT)
        add_event(
            db,
            app,
            "Интеграции",
            ApplicationStatus.ENRICHMENT,
            "Обогащение данными",
            "Запрашиваем БКИ, ЕГРЮЛ/ЕГРИП и сервис ФНС «Прозрачный бизнес» (локальные симуляторы).",
        )
        db.commit()
        _sleep()
        inn = app.company.inn
        enrichment = {
            "bki": fetch_credit_history(inn),
            "egrul": fetch_registry(inn),
            "fns": fetch_transparent_business(inn),
        }
        app.enrichment = enrichment
        add_event(
            db,
            app,
            "Интеграции",
            ApplicationStatus.ENRICHMENT,
            "Данные получены",
            enrichment["bki"]["comment"] + " Реестр: " + enrichment["egrul"].get("status_name", "нет данных") + ".",
        )
        db.commit()
        _sleep()
        _set_status(app, ApplicationStatus.SCORING)
        scoring = score_application(app.company, app, app.product, enrichment)
        try:
            ml_risk = predict_risk(app.company, app, enrichment)
        except Exception as exc:
            ml_risk = {"model": "unavailable", "score": scoring["score"], "risk_band": scoring["risk_band"], "default_probability": None, "error": str(exc), "disclaimer": "ML-сервис недоступен; использован fallback rule-based scoring."}
        scoring["ml_risk"] = ml_risk
        scoring["ml_risk_note"] = "ML-прогноз используется как дополнительный сигнал и не заменяет объяснимый скоринг."
        app.score = round(scoring["score"] * 0.7 + ml_risk["score"] * 0.3)
        app.risk_band = scoring["risk_band"]
        app.score_breakdown = scoring
        add_event(
            db,
            app,
            "Скоринг",
            ApplicationStatus.SCORING,
            f"Оценка риска {scoring['score']} · {scoring['risk_band_name']}",
            "Скоринг сформировал балл. Кредитное решение считается отдельно с учётом продукта и лимитов.",
        )
        db.commit()
        _sleep()
        _set_status(app, ApplicationStatus.DECISION)
        result = decide(app.company, app, app.product, scoring, extra_info_provided=extra_info_provided)
        app.decision_code = result["code"]
        app.decision_reason = result["reason"]
        app.offered_amount = result["offered_amount"]
        app.offered_term_months = result["offered_term_months"]
        app.offered_rate = result["offered_rate"]
        app.info_request = result["info_request"]
        if result["code"] == DecisionCode.REJECT:
            _set_status(app, ApplicationStatus.REJECTED)
            add_event(db, app, "Кредитный движок", ApplicationStatus.REJECTED, "Отказ", result["reason"])
        elif result["code"] == DecisionCode.NEED_INFO:
            _set_status(app, ApplicationStatus.NEED_INFO)
            add_event(db, app, "Кредитный движок", ApplicationStatus.NEED_INFO, "Нужны уточнения", result["info_request"])
        else:
            _set_status(app, ApplicationStatus.OFFERED)
            title = "Одобрено" if result["code"] == DecisionCode.APPROVE else "Одобрено с изменениями"
            add_event(db, app, "Кредитный движок", ApplicationStatus.OFFERED, title, result["reason"])
        db.commit()
    finally:
        db.close()