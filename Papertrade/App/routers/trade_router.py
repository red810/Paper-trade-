from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas, auth
from ..database import get_db
from ..services import trade_service

router = APIRouter(prefix="/trade", tags=["Trade"])


@router.post("/buy", response_model=schemas.TransactionOut)
def buy(
    request: schemas.TradeRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return trade_service.buy_stock(db, current_user, request.symbol.upper(), request.quantity)


@router.post("/sell", response_model=schemas.TransactionOut)
def sell(
    request: schemas.TradeRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return trade_service.sell_stock(db, current_user, request.symbol.upper(), request.quantity)
