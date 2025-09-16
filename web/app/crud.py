from sqlalchemy.orm import Session
from . import models


def _prepare_legs(wager: models.Wager, legs: list[dict]):
    wager.legs = []
    for leg in legs:
        desc = (leg.get("description") or "").strip()
        if not desc:
            continue
        status = leg.get("status") or models.WagerLegStatus.open
        if isinstance(status, str):
            try:
                status = models.WagerLegStatus(status)
            except ValueError:
                status = models.WagerLegStatus.open
        wager.legs.append(models.WagerLeg(description=desc, status=status))

# --- User Operations ---
def get_users_with_wagers(db: Session):
    return db.query(models.User).all()

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def create_user(db: Session, discord_id: str, display_name: str, profile_pic_url: str = None):
    user = models.User(
        discord_id=discord_id,
        display_name=display_name,
        profile_pic_url=profile_pic_url
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# --- Wager Operations ---
def get_user_wagers(db: Session, user_id: int):
    return db.query(models.Wager).filter(models.Wager.user_id == user_id).all()

def create_wager(db: Session, user_id: int, description: str, amount: float, line: str, legs: list[dict] | None = None):
    wager = models.Wager(user_id=user_id, description=description, amount=amount, line=line)
    if legs:
        _prepare_legs(wager, legs)
    db.add(wager)
    db.commit()
    db.refresh(wager)
    return wager

def update_wager_status(db: Session, wager_id: int, new_status: str):
    wager = db.query(models.Wager).filter(models.Wager.id == wager_id).first()
    if not wager:
        return None

    # Toggle: if same status is clicked again → reset to open
    if wager.status == new_status:
        wager.status = models.WagerStatus.open
    else:
        wager.status = new_status

    db.commit()
    db.refresh(wager)
    return wager


def update_wager_leg_status(db: Session, leg_id: int, new_status: str):
    leg = db.query(models.WagerLeg).filter(models.WagerLeg.id == leg_id).first()
    if not leg:
        return None

    current = leg.status.value if isinstance(leg.status, models.WagerLegStatus) else leg.status
    if current == new_status:
        leg.status = models.WagerLegStatus.open
    else:
        try:
            leg.status = models.WagerLegStatus(new_status)
        except ValueError:
            leg.status = models.WagerLegStatus.open

    db.commit()
    db.refresh(leg)
    return leg
    
def delete_wager(db: Session, wager_id: int):
    wager = db.query(models.Wager).filter(models.Wager.id == wager_id).first()
    if wager:
        db.delete(wager)
        db.commit()
    return wager
