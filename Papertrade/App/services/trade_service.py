from sqlalchemy.orm import Session
from fastapi import HTTPException

from .. import models
from .market_service import get_current_price
from ..routers.badges_router import check_and_award_badges


def _ensure_stock_exists(db: Session, symbol: str) -> None:
    """Holdings/Transactions have a foreign key into `stocks`, so make sure
    a reference row exists before inserting either."""
    stock = db.query(models.Stock).filter(models.Stock.symbol == symbol).first()
    if not stock:
        db.add(models.Stock(symbol=symbol))
        db.commit()


def buy_stock(db: Session, user: models.User, symbol: str, quantity: int) -> models.Transaction:
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive.")

    symbol = symbol.strip().upper()
    
    # 1. Fetch live market price FIRST. If invalid symbol or market error, fail immediately without polluting DB.
    price = get_current_price(symbol)
    total_cost = price * quantity

    if user.balance < total_cost:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient virtual balance. Required: ${total_cost:,.2f}, Available: ${user.balance:,.2f}.",
        )

    try:
        _ensure_stock_exists(db, symbol)

        # Deduct cash
        user.balance -= total_cost

        # Update or create holding
        holding = (
            db.query(models.Holding)
            .filter(models.Holding.user_id == user.id, models.Holding.symbol == symbol)
            .first()
        )

        if holding:
            total_existing_value = holding.avg_buy_price * holding.quantity
            new_total_value = total_existing_value + total_cost
            new_quantity = holding.quantity + quantity
            holding.avg_buy_price = new_total_value / new_quantity
            holding.quantity = new_quantity
        else:
            holding = models.Holding(
                user_id=user.id,
                symbol=symbol,
                quantity=quantity,
                avg_buy_price=price,
            )
            db.add(holding)

        # Log transaction
        transaction = models.Transaction(
            user_id=user.id,
            symbol=symbol,
            type=models.TransactionType.BUY,
            quantity=quantity,
            price=price,
        )
        db.add(transaction)

        db.commit()
        db.refresh(transaction)

        # Evaluate gamification badges
        check_and_award_badges(db, user, transaction)

        return transaction
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to process buy order: {str(e)}")


def sell_stock(db: Session, user: models.User, symbol: str, quantity: int) -> models.Transaction:
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive.")

    symbol = symbol.strip().upper()

    holding = (
        db.query(models.Holding)
        .filter(models.Holding.user_id == user.id, models.Holding.symbol == symbol)
        .first()
    )

    if not holding or holding.quantity < quantity:
        raise HTTPException(
            status_code=400,
            detail=f"You don't own enough shares of {symbol} to sell.",
        )

    price = get_current_price(symbol)
    proceeds = price * quantity

    try:
        # Credit cash
        user.balance += proceeds

        # Reduce holding
        holding.quantity -= quantity
        if holding.quantity == 0:
            db.delete(holding)

        # Log transaction
        transaction = models.Transaction(
            user_id=user.id,
            symbol=symbol,
            type=models.TransactionType.SELL,
            quantity=quantity,
            price=price,
        )
        db.add(transaction)

        db.commit()
        db.refresh(transaction)

        # Evaluate gamification badges
        check_and_award_badges(db, user, transaction)

        return transaction
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to process sell order: {str(e)}")

