import secrets
from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.auth import get_current_user, require_roles
from app.db import get_db
from app.models import Application, ApplicationStatus, DecisionCode, Product, User, UserRole
from app.schemas import ApplicationCreate, ApplicationOut, InfoReply, ManualDecision
from app.services.pipeline import add_event, run_pipeline
router = APIRouter(prefix="/api/applications", tags=["applications"])
def _load(db: Session, application_id: int) -> Application | None:
    application = (
        db.query(Application)
        .options(
            joinedload(Application.events),
            joinedload(Application.product),
            joinedload(Application.company),
        )
        .filter(Application.id == application_id)
        .first()
    )
    if application is not None:
        application.events.sort(key=lambda event: event.id)
    return application
def _ensure_owner(app: Application, user: User) -> None:
    if user.role == UserRole.CLIENT and app.applicant_id != user.id and app.company_id != user.company_id:
        raise HTTPException(status_code=403, detail="Нет доступа к заявке")
@router.get("", response_model=list[ApplicationOut])
def list_applications(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Application]:
    query = db.query(Application).options(joinedload(Application.events), joinedload(Application.product), joinedload(Application.company))
    if user.role == UserRole.CLIENT:
        query = query.filter(Application.company_id == user.company_id)
    return query.order_by(Application.created_at.desc()).all()
@router.post("", response_model=ApplicationOut)
def create_application(
    payload: ApplicationCreate,
    background: BackgroundTasks,
    user: User = Depends(require_roles(UserRole.CLIENT)),
    db: Session = Depends(get_db),
) -> Application:
    if user.company_id is None:
        raise HTTPException(status_code=400, detail="К пользователю не привязана компания")
    product = db.get(Product, payload.product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    if not (product.min_amount <= payload.amount <= product.max_amount * 1.2):
        raise HTTPException(status_code=400, detail="Сумма вне допустимого диапазона продукта")
    if not (product.min_term_months <= payload.term_months <= product.max_term_months):
        raise HTTPException(status_code=400, detail="Срок вне допустимого диапазона продукта")
    public_id = "К-" + secrets.token_hex(3).upper()
    app = Application(
        public_id=public_id,
        company_id=user.company_id,
        applicant_id=user.id,
        product_id=product.id,
        status=ApplicationStatus.SUBMITTED,
        amount=payload.amount,
        term_months=payload.term_months,
        purpose=payload.purpose,
        purpose_details=payload.purpose_details,
    )
    db.add(app)
    db.flush()
    add_event(
        db,
        app,
        user.full_name,
        ApplicationStatus.SUBMITTED,
        "Заявка отправлена",
        f"{product.name}: {payload.amount:,} ₽ на {payload.term_months} мес. Цель: {payload.purpose_details}",
    )
    db.commit()
    background.add_task(run_pipeline, app.id, False)
    loaded = _load(db, app.id)
    assert loaded
    return loaded


@router.get("/{application_id}", response_model=ApplicationOut)
def get_application(
        application_id: int,
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
) -> Application:
    app = _load(db, application_id)
    if app is None:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    _ensure_owner(app, user)
    return app


@router.post("/{application_id}/info", response_model=ApplicationOut)
def reply_info(
        application_id: int,
        payload: InfoReply,
        background: BackgroundTasks,
        user: User = Depends(require_roles(UserRole.CLIENT)),
        db: Session = Depends(get_db),
) -> Application:
    app = _load(db, application_id)
    if app is None:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    _ensure_owner(app, user)
    if app.status != ApplicationStatus.NEED_INFO:
        raise HTTPException(status_code=400, detail="Сейчас уточнения не требуются")
    app.client_comment = payload.comment
    app.status = ApplicationStatus.SUBMITTED
    add_event(db, app, user.full_name, ApplicationStatus.SUBMITTED, "Клиент дополнил сведения", payload.comment)
    db.commit()
    background.add_task(run_pipeline, app.id, True)
    loaded = _load(db, app.id)
    assert loaded
    return loaded


@router.post("/{application_id}/accept", response_model=ApplicationOut)
def accept_offer(
        application_id: int,
        user: User = Depends(require_roles(UserRole.CLIENT)),
        db: Session = Depends(get_db),
) -> Application:
    app = _load(db, application_id)
    if app is None:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    _ensure_owner(app, user)
    if app.status != ApplicationStatus.OFFERED:
        raise HTTPException(status_code=400, detail="Нет активного предложения")
    app.status = ApplicationStatus.DOCUMENTS
    add_event(db, app, user.full_name, ApplicationStatus.DOCUMENTS, "Условия приняты",
              "Клиент согласился с предложенными параметрами. Сформирован комплект документов.")
    db.commit()
    loaded = _load(db, app.id)
    assert loaded
    return loaded
@router.post("/{application_id}/sign", response_model=ApplicationOut)
def sign_docs(
    application_id: int,
    user: User = Depends(require_roles(UserRole.CLIENT)),
    db: Session = Depends(get_db),
) -> Application:
    app = _load(db, application_id)
    if app is None:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    _ensure_owner(app, user)
    if app.status != ApplicationStatus.DOCUMENTS:
        raise HTTPException(status_code=400, detail="Документы ещё не готовы")
    app.signed = True
    app.status = ApplicationStatus.DISBURSEMENT
    add_event(db, app, user.full_name, ApplicationStatus.DISBURSEMENT, "Документы подписаны", "Подписание смоделировано внутри продукта. Инициирована имитация выдачи.")
    db.commit()
    app.status = ApplicationStatus.COMPLETED
    add_event(
        db,
        app,
        "Операции",
        ApplicationStatus.COMPLETED,
        "Финансирование проведено",
        f"Смоделированная выдача {app.offered_amount:,} ₽. Реальные деньги не переводятся.",
    )
    app.updated_at = datetime.utcnow()
    db.commit()
    loaded = _load(db, app.id)
    assert loaded
    return loaded
@router.post("/{application_id}/cancel", response_model=ApplicationOut)
def cancel(
    application_id: int,
    user: User = Depends(require_roles(UserRole.CLIENT)),
    db: Session = Depends(get_db),
) -> Application:
    app = _load(db, application_id)
    if app is None:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    _ensure_owner(app, user)
    if app.status in {ApplicationStatus.COMPLETED, ApplicationStatus.REJECTED, ApplicationStatus.DISBURSEMENT}:
        raise HTTPException(status_code=400, detail="Заявку нельзя отменить")
    app.status = ApplicationStatus.CANCELLED
    add_event(db, app, user.full_name, ApplicationStatus.CANCELLED, "Клиент отозвал заявку", "Рассмотрение остановлено по инициативе клиента.")
    db.commit()
    loaded = _load(db, app.id)
    assert loaded
    return loaded

@router.post("/{application_id}/manual-decision", response_model=ApplicationOut)
def manual_decision(
    application_id: int,
    payload: ManualDecision,
    user: User = Depends(require_roles(UserRole.ANALYST, UserRole.UNDERWRITER)),
    db: Session = Depends(get_db),
) -> Application:
    app = _load(db, application_id)
    if app is None:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    app.decision_code = payload.code
    app.decision_reason = payload.reason
    app.offered_amount = payload.offered_amount
    app.offered_term_months = payload.offered_term_months
    app.offered_rate = payload.offered_rate
    app.info_request = payload.info_request
    mapping = {
        DecisionCode.APPROVE: ApplicationStatus.OFFERED,
        DecisionCode.APPROVE_WITH_CHANGES: ApplicationStatus.OFFERED,
        DecisionCode.NEED_INFO: ApplicationStatus.NEED_INFO,
        DecisionCode.REJECT: ApplicationStatus.REJECTED,
    }
    try:
        code = DecisionCode(payload.code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Неизвестный код решения") from exc
    app.status = mapping[code]
    add_event(db, app, user.full_name, app.status, "Ручное решение", payload.reason)
    db.commit()
    loaded = _load(db, app.id)
    assert loaded
    return loaded
