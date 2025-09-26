import json
from decimal import Decimal
from datetime import datetime, date, timedelta
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


def _normalize_wager_status(wager: models.Wager) -> str:
    status = wager.status
    if isinstance(status, models.WagerStatus):
        return status.value
    return str(status)


def _wager_profit_delta(wager: models.Wager) -> Decimal:
    amount_raw = wager.amount if wager.amount is not None else Decimal("0")
    amount = Decimal(str(amount_raw))
    status = _normalize_wager_status(wager)
    if status == models.WagerStatus.won.value:
        payout = wager.payout or 0
        return Decimal(str(payout))
    if status == models.WagerStatus.lost.value:
        return -amount
    return Decimal("0")


@app.on_event("startup")
async def startup():
    init_db()


@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request, db=Depends(get_db)):
    users = crud.get_users_with_wagers(db)
    team_lookup = crud.build_team_alias_lookup(db)
    for user in users:
        wagers = getattr(user, "active_wagers", user.wagers)
        for wager in wagers:
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


@app.get("/stats", response_class=HTMLResponse)
async def view_stats(request: Request, db=Depends(get_db)):
    users = crud.get_users_with_wagers(db)
    player_stats: list[dict[str, object]] = []
    profit_datasets: list[dict[str, object]] = []
    bet_datasets: list[dict[str, object]] = []

    for user in users:
        wagers = sorted(
            user.wagers,
            key=lambda wager: (wager.created_at or datetime.min),
        )

        wins = losses = open_count = removed = 0
        total_staked = Decimal("0")
        total_profit = Decimal("0")
        archived_count = 0
        daily_profit: dict[date, Decimal] = {}
        daily_bets: dict[date, int] = {}

        for wager in wagers:
            status = _normalize_wager_status(wager)
            amount_raw = wager.amount if wager.amount is not None else Decimal("0")
            amount = Decimal(str(amount_raw))
            total_staked += amount

            if getattr(wager, "archived", False):
                archived_count += 1

            if status == models.WagerStatus.won.value:
                wins += 1
            elif status == models.WagerStatus.lost.value:
                losses += 1
            elif status == models.WagerStatus.open.value:
                open_count += 1
            elif status == models.WagerStatus.removed.value:
                removed += 1

            profit_delta = _wager_profit_delta(wager)
            total_profit += profit_delta

            created_at = wager.created_at
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at)
                except ValueError:
                    created_at = None

            if created_at is not None:
                day = created_at.date()
                daily_bets[day] = daily_bets.get(day, 0) + 1
                daily_profit[day] = daily_profit.get(day, Decimal("0")) + profit_delta

        decided = wins + losses
        win_rate = float((wins / decided) * 100) if decided else 0.0

        player_stats.append(
            {
                "user": user,
                "total": len(wagers),
                "wins": wins,
                "losses": losses,
                "open": open_count,
                "removed": removed,
                "archived": archived_count,
                "staked": float(total_staked),
                "profit": float(total_profit),
                "win_rate": win_rate,
            }
        )

        if daily_profit:
            today = date.today()
            start_day = today - timedelta(days=29)
            profit_points: list[dict[str, object]] = []
            current_day = start_day
            while current_day <= today:
                value = float(daily_profit.get(current_day, Decimal("0")))
                profit_points.append({"x": current_day.isoformat(), "y": value})
                current_day += timedelta(days=1)
            profit_datasets.append(
                {
                    "label": user.display_name or f"Player {user.id}",
                    "data": profit_points,
                    "tension": 0.2,
                    "metric": "profit",
                }
            )

        if daily_bets:
            today = date.today()
            start_day = today - timedelta(days=29)
            bet_points: list[dict[str, object]] = []
            current_day = start_day
            while current_day <= today:
                value = daily_bets.get(current_day, 0)
                bet_points.append({"x": current_day.isoformat(), "y": value})
                current_day += timedelta(days=1)
            bet_datasets.append(
                {
                    "label": user.display_name or f"Player {user.id}",
                    "data": bet_points,
                    "tension": 0.2,
                    "metric": "bets",
                }
            )

    chart_payload = json.dumps({"profit": profit_datasets, "bets": bet_datasets})

    return templates.TemplateResponse(
        "stats.html",
        {
            "request": request,
            "player_stats": player_stats,
            "chart_payload": chart_payload,
            "has_chart": bool(profit_datasets or bet_datasets),
        },
    )


@app.get("/archived", response_class=HTMLResponse)
async def view_archived(request: Request, db=Depends(get_db)):
    users = crud.get_users_with_wagers(db)
    team_lookup = crud.build_team_alias_lookup(db)
    has_archived = False
    for user in users:
        wagers = getattr(user, "archived_wagers", [])
        if wagers:
            has_archived = True
        for wager in wagers:
            for leg in wager.legs:
                leg.matched_teams = crud.match_leg_description_to_teams(leg.description, team_lookup)
    return templates.TemplateResponse(
        "archived.html",
        {"request": request, "users": users, "has_archived": has_archived},
    )


@app.post("/wagers/{wager_id}/status")
async def update_wager_status(wager_id: int, status: str = Form(...), db=Depends(get_db)):
    crud.update_wager_status(db, wager_id, status)
    return RedirectResponse("/", status_code=303)


@app.post("/wagers/{wager_id}/legs/{leg_id}/status")
async def update_wager_leg_status(wager_id: int, leg_id: int, status: str = Form(...), db=Depends(get_db)):
    crud.update_wager_leg_status(db, leg_id, status)
    return RedirectResponse("/", status_code=303)


@app.post("/wagers/{wager_id}/archive")
async def update_wager_archive(
    wager_id: int,
    archived: bool = Form(...),
    redirect_to: str = Form("/"),
    db=Depends(get_db),
):
    crud.set_wager_archived(db, wager_id, archived)
    return RedirectResponse(redirect_to, status_code=303)
