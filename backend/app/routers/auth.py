from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.auth import create_token, get_current_user, verify_password
from app.db import get_db
from app.models import Company, User
from app.schemas import CompanyOut, LoginRequest, MeResponse, TokenResponse, UserOut
router = APIRouter(prefix="/api/auth", tags=["auth"])
@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    return TokenResponse(access_token=create_token(user))
@router.get("/me", response_model=MeResponse)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> MeResponse:
    company = db.get(Company, user.company_id) if user.company_id else None
    return MeResponse(
        user=UserOut.model_validate(user),
        company=CompanyOut.model_validate(company) if company else None,
    )