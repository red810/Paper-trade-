from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey, DateTime, Date, Enum, UniqueConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from .database import Base


class TransactionType(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    balance = Column(Float, default=100000.0)  # virtual cash balance
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    holdings = relationship("Holding", back_populates="owner", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="owner", cascade="all, delete-orphan")
    watchlist_items = relationship("WatchlistItem", back_populates="owner", cascade="all, delete-orphan")
    badges = relationship("Badge", back_populates="owner", cascade="all, delete-orphan")


class Stock(Base):
    """Reference table so a symbol isn't just a free-text string everywhere else."""
    __tablename__ = "stocks"

    symbol = Column(String, primary_key=True, index=True)  # e.g. "AAPL", "TCS.NS"
    company_name = Column(String, nullable=True)
    exchange = Column(String, nullable=True)  # e.g. "NASDAQ", "NSE"

    holdings = relationship("Holding", back_populates="stock")
    transactions = relationship("Transaction", back_populates="stock")
    watchlist_items = relationship("WatchlistItem", back_populates="stock")
    price_history = relationship("PriceHistory", back_populates="stock", cascade="all, delete-orphan")


class Holding(Base):
    """A user's current aggregated position in a given stock."""
    __tablename__ = "holdings"
    __table_args__ = (UniqueConstraint("user_id", "symbol", name="uq_user_symbol_holding"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol = Column(String, ForeignKey("stocks.symbol"), nullable=False)
    quantity = Column(Integer, default=0)
    avg_buy_price = Column(Float, default=0.0)

    owner = relationship("User", back_populates="holdings")
    stock = relationship("Stock", back_populates="holdings")


class Transaction(Base):
    """Immutable log of every buy/sell action -- the audit trail."""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol = Column(String, ForeignKey("stocks.symbol"), nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)  # price per share at execution time
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="transactions")
    stock = relationship("Stock", back_populates="transactions")


class WatchlistItem(Base):
    """Stocks a user is tracking without owning."""
    __tablename__ = "watchlist"
    __table_args__ = (UniqueConstraint("user_id", "symbol", name="uq_user_symbol_watchlist"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol = Column(String, ForeignKey("stocks.symbol"), nullable=False)
    added_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="watchlist_items")
    stock = relationship("Stock", back_populates="watchlist_items")


class PriceHistory(Base):
    """Daily closing prices per stock, so charts don't need to hit the live API every time."""
    __tablename__ = "price_history"
    __table_args__ = (UniqueConstraint("symbol", "date", name="uq_symbol_date_price"),)

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, ForeignKey("stocks.symbol"), nullable=False)
    close_price = Column(Float, nullable=False)
    date = Column(Date, nullable=False)

    stock = relationship("Stock", back_populates="price_history")


class Badge(Base):
    """Gamification: achievements earned by a user (e.g. 'First Trade', 'Streak x5')."""
    __tablename__ = "badges"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    badge_name = Column(String, nullable=False)
    earned_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="badges")

