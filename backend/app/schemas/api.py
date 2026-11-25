from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class MerchantOut(BaseModel):
    id: int
    code: str
    name: str
    category: str
    status: str
    region: str
    revenue: Decimal = Decimal("0")
    transactions: int = 0
    subscribers: int = 0
    score: float = 0
    grade: str = "D"
    model_config = ConfigDict(from_attributes=True)


class ForecastOut(BaseModel):
    target_date: date
    model_name: str
    predicted_revenue: Decimal
    lower_bound: Decimal
    upper_bound: Decimal


class AnomalyOut(BaseModel):
    merchant_id: int
    detected_at: datetime
    metric: str
    observed_value: Decimal
    severity: str
    method: str
    details: str
