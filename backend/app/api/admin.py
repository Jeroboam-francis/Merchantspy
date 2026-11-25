from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.auth.security import hash_password
from app.database.session import get_db
from app.models import Role, User

router = APIRouter(prefix="/admin", tags=["administration"], dependencies=[Depends(require_roles("admin"))])


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: str


@router.get("/roles")
def list_roles(db: Session = Depends(get_db)):
    return [{"id": role.id, "name": role.name} for role in db.query(Role).order_by(Role.name).all()]


@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [{"id": user.id, "email": user.email, "full_name": user.full_name, "active": user.is_active,
             "role": db.query(Role.name).filter(Role.id == user.role_id).scalar()} for user in users]


@router.post("/users", status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    if len(payload.password) < 12:
        raise HTTPException(status_code=422, detail="Password must be at least 12 characters")
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email already exists")
    role = db.query(Role).filter(Role.name == payload.role).first()
    if role is None:
        raise HTTPException(status_code=422, detail="Role must be admin, manager, analyst, or viewer")
    user = User(email=payload.email, full_name=payload.full_name,
                hashed_password=hash_password(payload.password), role_id=role.id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email, "full_name": user.full_name, "role": role.name}
