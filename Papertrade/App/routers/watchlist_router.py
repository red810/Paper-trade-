from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from .. import models, auth
from ..database import get_db
from ..services.market_service import get_current_price

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])


class WatchlistRequest(BaseModel):
    symbol: str


@router.post("/add")
def add_to_watchlist(
    request: WatchlistRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    symbol = request.symbol.strip().upper()
    if not symbol:
        raise HTTPException(status_code=400, detail="Symbol cannot be empty.")

    # 1. Validate ticker exists by fetching price first
    get_current_price(symbol)

    # 2. Ensure stock exists in reference table
    stock = db.query(models.Stock).filter(models.Stock.symbol == symbol).first()
    if not stock:
        stock = models.Stock(symbol=symbol)
        db.add(stock)
        db.commit()

    existing = (
        db.query(models.WatchlistItem)
        .filter(models.WatchlistItem.user_id == current_user.id, models.WatchlistItem.symbol == symbol)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail=f"{symbol} is already on your watchlist.")

    item = models.WatchlistItem(user_id=current_user.id, symbol=symbol)
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"message": f"{symbol} added to watchlist."}


@router.delete("/remove/{symbol}")
def remove_from_watchlist(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    symbol = symbol.strip().upper()
    item = (
        db.query(models.WatchlistItem)
        .filter(models.WatchlistItem.user_id == current_user.id, models.WatchlistItem.symbol == symbol)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail=f"{symbol} is not on your watchlist.")

    db.delete(item)
    db.commit()
    return {"message": f"{symbol} removed from watchlist."}


@router.get("/")
def get_watchlist(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    items = (
        db.query(models.WatchlistItem)
        .filter(models.WatchlistItem.user_id == current_user.id)
        .all()
    )
    result = []
    for i in items:
        try:
            price = get_current_price(i.symbol)
        except Exception:
            price = None
        result.append({
            "symbol": i.symbol,
            "added_at": i.added_at,
            "current_price": price
        })
    return result

