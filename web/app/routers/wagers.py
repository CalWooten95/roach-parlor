from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud, models, database
from pydantic import BaseModel

router = APIRouter(prefix="/wagers", tags=["wagers"])

class WagerCreate(BaseModel):
    user_id: int
    description: str
    amount: float
    line: str

class WagerOut(BaseModel):
    id: int
    user_id: int
    description: str
    amount: float
    line: str
    status: str

    class Config:
        orm_mode = True


@router.post("/", response_model=WagerOut)
def create_wager(wager: WagerCreate, db: Session = Depends(database.get_db)):
    user = crud.get_user(db, wager.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.create_wager(db, user_id=wager.user_id, description=wager.description, amount=wager.amount, line=wager.line)


@router.get("/{user_id}", response_model=list[WagerOut])
def list_user_wagers(user_id: int, db: Session = Depends(database.get_db)):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.get_user_wagers(db, user_id)


@router.patch("/{wager_id}/status", response_model=WagerOut)
def update_status(wager_id: int, status: str, db: Session = Depends(database.get_db)):
    wager = crud.update_wager_status(db, wager_id, status)
    if not wager:
        raise HTTPException(status_code=404, detail="Wager not found")
    return wager


@router.delete("/{wager_id}", response_model=WagerOut)
def delete_wager(wager_id: int, db: Session = Depends(database.get_db)):
    wager = crud.delete_wager(db, wager_id)
    if not wager:
        raise HTTPException(status_code=404, detail="Wager not found")
    return wager