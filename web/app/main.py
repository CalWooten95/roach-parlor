from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from .database import get_db, init_db
from . import crud, models, schemas
from .routers import wagers
from .routers import users

app = FastAPI()
app.include_router(users.router)
app.include_router(wagers.router)
templates = Jinja2Templates(directory="app/templates")


@app.on_event("startup")
async def startup():
    init_db()


@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request, db=Depends(get_db)):
    users = crud.get_users_with_wagers(db)
    return templates.TemplateResponse("index.html", {"request": request, "users": users})


@app.post("/wagers/{wager_id}/status")
async def update_wager_status(wager_id: int, status: str = Form(...), db=Depends(get_db)):
    crud.update_wager_status(db, wager_id, status)
    return RedirectResponse("/", status_code=303)
