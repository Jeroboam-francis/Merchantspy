from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.auth.security import create_access_token, verify_password
from app.database.session import get_db
from app.models import Role, User
from app.schemas.api import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email, User.is_active.is_(True)).first()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    role = db.query(Role).filter(Role.id == user.role_id).first()
    if role is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User role is not configured")
    return TokenResponse(access_token=create_access_token(user.email, role.name))


@router.get("/me")
def me(user: User = Depends(current_user), db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.id == user.role_id).first()
    return {"id": user.id, "email": user.email, "full_name": user.full_name, "role": role.name if role else None}
