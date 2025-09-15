from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud, database
from pydantic import BaseModel

router = APIRouter(prefix="/users", tags=["users"])

class UserCreate(BaseModel):
    discord_id: str
    display_name: str
    profile_pic_url: str | None = None

class UserOut(BaseModel):
    id: int
    discord_id: str
    display_name: str
    profile_pic_url: str | None

    class Config:
        orm_mode = True


@router.post("/", response_model=UserOut)
def create_user(user: UserCreate, db: Session = Depends(database.get_db)):
    existing = db.query(crud.models.User).filter(crud.models.User.discord_id == user.discord_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    return crud.create_user(db, discord_id=user.discord_id, display_name=user.display_name, profile_pic_url=user.profile_pic_url)


@router.get("/", response_model=list[UserOut])
def list_users(db: Session = Depends(database.get_db)):
    return db.query(crud.models.User).all()


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(database.get_db)):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user