from sqlalchemy.orm import Session
from app.models import Application, Company, NewsItem, User
def personalized_feed(db: Session, user: User) -> list[NewsItem]:
    company: Company | None = user.company
    applications = []
    if company:
        applications = (
            db.query(Application)
            .filter(Application.company_id == company.id)
            .order_by(Application.updated_at.desc())
            .all()
        )
    items = db.query(NewsItem).order_by(NewsItem.priority.desc(), NewsItem.published_at.desc()).all()
    selected: list[NewsItem] = []
    statuses = {app.status for app in applications}
    product_ids = {app.product_id for app in applications}
    okved = company.okved if company else ""
    tag = company.profile_tag if company else ""
    for item in items:
        tags = item.audience_tags or []
        okveds = item.okved_prefixes or []
        hooks = item.status_hooks or []
        products = item.product_ids or []
        match = False
        if "all" in tags:
            match = True
        if user.role in tags:
            match = True
        if tag and tag in tags:
            match = True
        if okveds and any(okved.startswith(prefix) for prefix in okveds):
            match = True
        if hooks and statuses.intersection(hooks):
            match = True
        if products and product_ids.intersection(products):
            match = True
        if match:
            selected.append(item)
    return selected[:12]