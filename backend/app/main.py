from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, analytics, auth, finance, forecasts, merchants, reports
from app.auth.security import hash_password
from app.core.config import settings
from app.database.session import Base, SessionLocal, engine
from app.models import Region, Role, User


def initialize_database() -> None:
    if settings.app_env.lower() == "production":
        if len(settings.jwt_secret_key) < 32 or settings.jwt_secret_key == "development-only-change-me":
            raise RuntimeError("Production requires a unique JWT_SECRET_KEY with at least 32 characters")
        if settings.seed_admin_password == "ChangeMe-LocalOnly-123!" or len(settings.seed_admin_password) < 16:
            raise RuntimeError("Production requires a unique SEED_ADMIN_PASSWORD with at least 16 characters")
        if settings.seed_admin_email == "admin@airtel.example":
            raise RuntimeError("Production requires a configured SEED_ADMIN_EMAIL")
        if settings.database_url.startswith("sqlite") or "LocalApp-ChangeMe" in settings.database_url:
            raise RuntimeError("Production requires a configured Oracle DATABASE_URL")
        if any("localhost" in origin or "127.0.0.1" in origin for origin in settings.cors_origin_list):
            raise RuntimeError("Production CORS_ORIGINS must not contain localhost")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        roles = ("admin", "manager", "analyst", "viewer")
        for name in roles:
            if db.query(Role).filter(Role.name == name).first() is None:
                db.add(Role(name=name))
        if db.query(Region).count() == 0:
            for name in ("North", "South", "East", "West", "Central"):
                db.add(Region(name=name))
        db.commit()
        if db.query(User).filter(User.email == settings.seed_admin_email).first() is None:
            admin_role = db.query(Role).filter(Role.name == "admin").one()
            db.add(User(email=settings.seed_admin_email, full_name="Platform Administrator",
                        hashed_password=hash_password(settings.seed_admin_password), role_id=admin_role.id))
            db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title=settings.app_name, version="1.0.0",
    docs_url="/docs" if settings.enable_api_docs and settings.app_env.lower() != "production" else None,
    redoc_url="/redoc" if settings.enable_api_docs and settings.app_env.lower() != "production" else None,
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"], allow_headers=["Authorization", "Content-Type"],
)
for router in (auth.router, analytics.router, merchants.router, finance.router, forecasts.router, reports.router, admin.router):
    app.include_router(router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok", "service": "merchant-analytics"}
