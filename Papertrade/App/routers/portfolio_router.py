from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from .. import models, schemas, auth
from ..database import get_db
from ..services.market_service import get_current_price

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


@router.get("/holdings")
def get_holdings(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    holdings = (
        db.query(models.Holding).filter(models.Holding.user_id == current_user.id).all()
    )

    result = []
    for h in holdings:
        try:
            current_price = get_current_price(h.symbol)
        except Exception:
            current_price = h.avg_buy_price

        current_value = current_price * h.quantity
        invested_value = h.avg_buy_price * h.quantity
        profit_loss = current_value - invested_value

        result.append(
            {
                "symbol": h.symbol,
                "quantity": h.quantity,
                "avg_buy_price": h.avg_buy_price,
                "current_price": current_price,
                "current_value": round(current_value, 2),
                "profit_loss": round(profit_loss, 2),
                "profit_loss_percent": round(
                    (profit_loss / invested_value) * 100, 2
                ) if invested_value > 0 else 0.0,
            }
        )
    return result


@router.get("/summary")
def get_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    holdings = (
        db.query(models.Holding).filter(models.Holding.user_id == current_user.id).all()
    )
    
    invested_value = 0.0
    for h in holdings:
        try:
            price = get_current_price(h.symbol)
        except Exception:
            price = h.avg_buy_price
        invested_value += price * h.quantity

    return {
        "cash_balance": round(current_user.balance, 2),
        "invested_value": round(invested_value, 2),
        "net_worth": round(current_user.balance + invested_value, 2),
    }


@router.get("/transactions", response_model=List[schemas.TransactionOut])
def get_transactions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return (
        db.query(models.Transaction)
        .filter(models.Transaction.user_id == current_user.id)
        .order_by(models.Transaction.timestamp.desc())
        .all()
    )


@router.get("/leaderboard")
def get_leaderboard(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Ranks all users by net worth (cash balance + live market value of stock holdings)."""
    users = db.query(models.User).all()
    leaderboard = []

    for user in users:
        holdings = (
            db.query(models.Holding).filter(models.Holding.user_id == user.id).all()
        )
        invested_val = 0.0
        for h in holdings:
            try:
                p = get_current_price(h.symbol)
            except Exception:
                p = h.avg_buy_price
            invested_val += p * h.quantity

        net_worth = user.balance + invested_val
        leaderboard.append({
            "user_id": user.id,
            "username": user.username,
            "cash_balance": round(user.balance, 2),
            "invested_value": round(invested_val, 2),
            "net_worth": round(net_worth, 2),
        })

    # Sort users by net worth descending
    leaderboard.sort(key=lambda x: x["net_worth"], reverse=True)

    # Assign 1-indexed ranks
    for idx, entry in enumerate(leaderboard, start=1):
        entry["rank"] = idx

    return leaderboard

