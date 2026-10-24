from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.auth import get_current_user
from app.db import get_db
from app.models import Product, User
from app.schemas import ProductOut, RecommendRequest
router = APIRouter(prefix="/api/products", tags=["products"])
PURPOSE_MAP = {
    "working_capital": ["turnover", "overdraft"],
    "gap": ["overdraft", "turnover"],
    "payroll": ["turnover"],
    "equipment": ["investment"],
    "expansion": ["investment", "turnover"],
    "renovation": ["investment"],
}
@router.get("", response_model=list[ProductOut])
def list_products(_: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Product]:
    return db.query(Product).all()
@router.post("/recommend", response_model=list[ProductOut])
def recommend(
    payload: RecommendRequest,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Product]:
    preferred = PURPOSE_MAP.get(payload.purpose, ["turnover"])
    products = {item.id: item for item in db.query(Product).all()}
    ordered = [products[pid] for pid in preferred if pid in products]
    if payload.amount > 8_000_000 and products.get("investment") not in ordered:
        ordered.append(products["investment"])
    if payload.urgency == "asap" and products.get("overdraft") not in ordered:
        ordered.insert(0, products["overdraft"])
    return ordered