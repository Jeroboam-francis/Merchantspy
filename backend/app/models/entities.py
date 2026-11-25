from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class Region(Base):
    __tablename__ = "regions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    country: Mapped[str] = mapped_column(String(80), default="India", nullable=False)
    merchants: Mapped[list["Merchant"]] = relationship(back_populates="region")


class Role(Base):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Merchant(Base):
    __tablename__ = "merchants"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    region_id: Mapped[int] = mapped_column(ForeignKey("regions.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    region: Mapped[Region] = relationship(back_populates="merchants")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="merchant")
    subscribers: Mapped[list["Subscriber"]] = relationship(back_populates="merchant")


class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), nullable=False)
    transaction_ref: Mapped[str] = mapped_column(String(48), unique=True, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    channel: Mapped[str] = mapped_column(String(30), nullable=False)
    merchant: Mapped[Merchant] = relationship(back_populates="transactions")
    __table_args__ = (Index("ix_tx_merchant_date", "merchant_id", "occurred_at"),)


class Collection(Base):
    __tablename__ = "collections"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), nullable=False, index=True)
    transaction_id: Mapped[int | None] = mapped_column(ForeignKey("transactions.id"), nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)


class Disbursement(Base):
    __tablename__ = "disbursements"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), nullable=False, index=True)
    disbursed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    reference: Mapped[str] = mapped_column(String(48), unique=True, nullable=False)


class Subscriber(Base):
    __tablename__ = "subscribers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), nullable=False, index=True)
    subscriber_ref: Mapped[str] = mapped_column(String(48), unique=True, nullable=False)
    joined_at: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    merchant: Mapped[Merchant] = relationship(back_populates="subscribers")


class ForecastResult(Base):
    __tablename__ = "forecast_results"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    merchant_id: Mapped[int | None] = mapped_column(ForeignKey("merchants.id"), nullable=True, index=True)
    target_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    model_name: Mapped[str] = mapped_column(String(40), nullable=False)
    predicted_revenue: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    lower_bound: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    upper_bound: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class AnomalyResult(Base):
    __tablename__ = "anomaly_results"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), nullable=False, index=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    metric: Mapped[str] = mapped_column(String(40), nullable=False)
    observed_value: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    method: Mapped[str] = mapped_column(String(40), nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False)
    __table_args__ = (
        UniqueConstraint("merchant_id", "detected_at", "metric", "method", name="uq_anomaly_signal"),
    )
