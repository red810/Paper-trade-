from dotenv import load_dotenv
load_dotenv()  # reads DATABASE_URL etc. from a local .env file

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import (
    auth_router,
    trade_router,
    portfolio_router,
    market_router,
    watchlist_router,
    badges_router,
)

# Creates tables on startup if they don't already exist (fine for demo use;
# use Alembic migrations instead for a production setup).
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="PaperTrade API",
    description="Virtual stock trading simulator using real-time market prices.",
    version="0.1.0",
)

# Allows your frontend (running on a different port/domain) to call this API.
# Replace "*" with your actual frontend URL before deploying anywhere public.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(trade_router.router)
app.include_router(portfolio_router.router)
app.include_router(market_router.router)
app.include_router(watchlist_router.router)
app.include_router(badges_router.router)


import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Static files directory path
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def root():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "PaperTrade API is running. Visit /docs for interactive API testing."}

