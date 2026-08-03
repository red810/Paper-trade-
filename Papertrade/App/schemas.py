from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
from .models import TransactionType


# ---------- Auth ----------
class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50, examples=["johndoe"])
    email: EmailStr = Field(examples=["johndoe@example.com"])
    password: str = Field(min_length=4, examples=["securepass123"])


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    balance: float

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str


# ---------- Trading ----------
class TradeRequest(BaseModel):
    symbol: str = Field(min_length=1, examples=["AAPL"])
    quantity: int = Field(gt=0, examples=[5])


class HoldingOut(BaseModel):
    symbol: str
    quantity: int
    avg_buy_price: float

    class Config:
        from_attributes = True


class TransactionOut(BaseModel):
    symbol: str
    type: TransactionType
    quantity: int
    price: float
    timestamp: datetime

    class Config:
        from_attributes = True


# ---------- Portfolio & Watchlist Response Models ----------
class PortfolioSummaryOut(BaseModel):
    cash_balance: float
    invested_value: float
    net_worth: float


class LeaderboardEntryOut(BaseModel):
    rank: int
    user_id: int
    username: str
    cash_balance: float
    invested_value: float
    net_worth: float


class WatchlistItemOut(BaseModel):
    symbol: str
    added_at: datetime
    current_price: Optional[float] = None


class BadgeOut(BaseModel):
    badge_name: str
    earned_at: datetime