import yfinance as yf
from fastapi import HTTPException
import pandas as pd


def get_current_price(symbol: str) -> float:
    """
    Fetches the latest available price for a stock symbol.
    Uses yfinance, which is free and needs no API key.
    Handles weekend/holiday history gaps and yfinance exceptions.
    """
    symbol = symbol.strip().upper()
    if not symbol:
        raise HTTPException(status_code=400, detail="Symbol cannot be empty.")

    try:
        ticker = yf.Ticker(symbol)
        
        # Try 5d period to handle weekends and market holidays cleanly
        data = ticker.history(period="5d")

        if not data.empty and "Close" in data and not data["Close"].dropna().empty:
            latest_price = float(data["Close"].dropna().iloc[-1])
            if not pd.isna(latest_price) and latest_price > 0:
                return round(latest_price, 2)

        # Fallback to fast_info if history didn't yield a valid close price
        fast_info = getattr(ticker, "fast_info", None)
        if fast_info and hasattr(fast_info, "last_price"):
            price = fast_info.last_price
            if price is not None and not pd.isna(price) and price > 0:
                return round(float(price), 2)

        raise HTTPException(
            status_code=404,
            detail=f"Could not fetch price for symbol '{symbol}'. Check that the ticker symbol is correct.",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Market price service error for symbol '{symbol}': {str(e)}",
        )

