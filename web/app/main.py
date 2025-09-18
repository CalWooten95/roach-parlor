from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from .database import get_db, init_db
from . import crud, models, schemas
from .routers import wagers
from .routers import users
from .routers import catalog

app = FastAPI()
app.include_router(users.router)
app.include_router(wagers.router)
app.include_router(catalog.router)
templates = Jinja2Templates(directory="app/templates")


@app.on_event("startup")
async def startup():
    init_db()


@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request, db=Depends(get_db)):
    users = crud.get_users_with_wagers(db)
    team_lookup = crud.build_team_alias_lookup(db)
    for user in users:
        for wager in user.wagers:
            for leg in wager.legs:
                leg.matched_teams = crud.match_leg_description_to_teams(leg.description, team_lookup)
    return templates.TemplateResponse("index.html", {"request": request, "users": users})


@app.get("/catalog", response_class=HTMLResponse)
async def view_catalog(request: Request, db=Depends(get_db)):
    leagues = crud.get_leagues_with_catalog(db)
    return templates.TemplateResponse(
        "catalog.html",
        {
            "request": request,
            "leagues": leagues,
        },
    )


@app.post("/wagers/{wager_id}/status")
async def update_wager_status(wager_id: int, status: str = Form(...), db=Depends(get_db)):
    crud.update_wager_status(db, wager_id, status)
    return RedirectResponse("/", status_code=303)


@app.post("/wagers/{wager_id}/legs/{leg_id}/status")
async def update_wager_leg_status(wager_id: int, leg_id: int, status: str = Form(...), db=Depends(get_db)):
    crud.update_wager_leg_status(db, leg_id, status)
    return RedirectResponse("/", status_code=303)
