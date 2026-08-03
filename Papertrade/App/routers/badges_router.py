from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, auth
from ..database import get_db

router = APIRouter(prefix="/badges", tags=["Badges"])


@router.get("/")
def get_badges(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    badges = db.query(models.Badge).filter(models.Badge.user_id == current_user.id).all()
    return [{"badge_name": b.badge_name, "earned_at": b.earned_at} for b in badges]


def award_badge(db: Session, user_id: int, badge_name: str) -> models.Badge:
    """Awards a badge to a user if they haven't already earned it."""
    existing = (
        db.query(models.Badge)
        .filter(models.Badge.user_id == user_id, models.Badge.badge_name == badge_name)
        .first()
    )
    if existing:
        return existing

    badge = models.Badge(user_id=user_id, badge_name=badge_name)
    db.add(badge)
    db.commit()
    db.refresh(badge)
    return badge


def check_and_award_badges(db: Session, user: models.User, transaction: models.Transaction) -> list:
    """Evaluates gamification badges for the user based on their trading activity."""
    awarded = []
    
    # 1. First Trade badge
    tx_count = db.query(models.Transaction).filter(models.Transaction.user_id == user.id).count()
    if tx_count >= 1:
        if award_badge(db, user.id, "First Trade"):
            awarded.append("First Trade")

    # 2. Big Spender ($10,000+ single transaction)
    if (transaction.price * transaction.quantity) >= 10000.0:
        if award_badge(db, user.id, "Big Spender"):
            awarded.append("Big Spender")

    # 3. Diversified (holds 3+ distinct stock symbols)
    holdings_count = (
        db.query(models.Holding)
        .filter(models.Holding.user_id == user.id, models.Holding.quantity > 0)
        .count()
    )
    if holdings_count >= 3:
        if award_badge(db, user.id, "Diversified Portfolio"):
            awarded.append("Diversified Portfolio")

    # 4. Profit Taker (executed first sell)
    if transaction.type == models.TransactionType.SELL:
        if award_badge(db, user.id, "Profit Taker"):
            awarded.append("Profit Taker")

    return awarded

