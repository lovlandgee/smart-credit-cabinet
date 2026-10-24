from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.auth import get_current_user
from app.db import get_db
from app.models import User
from app.schemas import NewsOut
from app.services.news import personalized_feed
router = APIRouter(prefix="/api/news", tags=["news"])
@router.get("", response_model=list[NewsOut])
def get_news(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[NewsOut]:
    items = personalized_feed(db, user)
    result = []
    for item in items:
        why = "Подобрано по роли и текущему состоянию кабинета"
        if user.company and any(user.company.okved.startswith(p) for p in (item.okved_prefixes or [])):
            why = f"Отраслевая лента для ОКВЭД {user.company.okved}"
        elif item.status_hooks:
            why = "Связано со статусом вашей заявки"
        elif user.role in (item.audience_tags or []):
            why = "Материал для вашей роли в процессе"
        result.append(
            NewsOut(
                id=item.id,
                title=item.title,
                body=item.body,
                category=item.category,
                published_at=item.published_at,
                why=why,
            )
        )
    return result
