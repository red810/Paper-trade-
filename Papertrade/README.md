# PaperTrade — Virtual Stock Trading Simulator (Backend)

A FastAPI backend for a paper-trading platform. Users get a virtual cash
balance and can buy/sell real stocks at their live market price.

## Project structure

```
papertrade/
├── app/
│   ├── main.py                # FastAPI app, wires up all routers
│   ├── database.py            # SQLAlchemy engine/session setup
│   ├── models.py               # User, Holding, Transaction tables
│   ├── schemas.py              # Pydantic request/response models
│   ├── auth.py                 # Password hashing + JWT handling
│   ├── routers/
│   │   ├── auth_router.py      # /auth/signup, /auth/login
│   │   ├── trade_router.py     # /trade/buy, /trade/sell
│   │   ├── portfolio_router.py # /portfolio/holdings, /summary, /transactions
│   │   └── market_router.py    # /market/price/{symbol}
│   └── services/
│       ├── trade_service.py    # Core buy/sell logic, wallet math
│       └── market_service.py   # Live price fetching via yfinance
└── requirements.txt
```

## Setup

1. Create a virtual environment (recommended):
   ```
   python -m venv venv
   source venv/bin/activate      # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the server:
   ```
   uvicorn app.main:app --reload
   ```

4. Open your browser at **http://127.0.0.1:8000/docs** — this is FastAPI's
   auto-generated Swagger UI, where you can test every endpoint directly
   without building a frontend first.

## Testing the flow via Swagger UI

1. **POST /auth/signup** — create a user (you'll get 100000.0 virtual balance).
2. **POST /auth/login** — log in with username/password, copy the `access_token`.
3. Click the **Authorize** button (top right of Swagger UI) and paste the token
   as `Bearer <token>`.
4. **POST /trade/buy** — e.g. `{"symbol": "AAPL", "quantity": 5}`.
5. **GET /portfolio/holdings** — see your position with live P&L.
6. **GET /portfolio/summary** — see cash balance, invested value, net worth.
7. **POST /trade/sell** — sell some or all of a holding.
8. **GET /portfolio/transactions** — see your full trade history.

## Notes

- Stock prices are fetched live via `yfinance` (no API key needed, but
  slightly delayed depending on the exchange). Use real ticker symbols,
  e.g. `AAPL`, `MSFT`, `TCS.NS`, `RELIANCE.NS` (NSE symbols need the `.NS` suffix).
- The `SECRET_KEY` in `app/auth.py` is a placeholder — change it before
  showing this to anyone outside a classroom demo.
- Database is SQLite (`papertrade.db`, created automatically on first run).
  Swap `DATABASE_URL` in `database.py` for PostgreSQL if you want to scale later.

## Suggested next steps

- Add a leaderboard endpoint (rank users by net worth).
- Add a watchlist model (stocks tracked without buying).
- Build the frontend to consume these endpoints.
