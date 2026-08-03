from fastapi import APIRouter

from ..services.market_service import get_current_price

router = APIRouter(prefix="/market", tags=["Market"])


@router.get("/price/{symbol}")
def price(symbol: str):
    current_price = get_current_price(symbol.upper())
    return {"symbol": symbol.upper(), "price": current_price}
