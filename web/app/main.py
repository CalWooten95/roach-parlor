import hashlib
import hmac
import json
import os
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

_raw_admin_key = os.getenv("ADMIN_ACCESS_KEY")
ADMIN_ACCESS_KEY = _raw_admin_key.strip() if _raw_admin_key else None
ADMIN_COOKIE_NAME = "admin_access_token"
ADMIN_KEY_SIGNATURE = (
    hashlib.sha256(ADMIN_ACCESS_KEY.encode("utf-8")).hexdigest()
    if ADMIN_ACCESS_KEY
    else None
)

templates.env.globals["admin_requires_key"] = bool(ADMIN_ACCESS_KEY)
templates.env.globals["admin_dashboard_path"] = "/admin/wagers"
templates.env.globals["admin_cookie_name"] = ADMIN_COOKIE_NAME


def _is_correct_admin_key(candidate: str | None) -> bool:
    if not ADMIN_ACCESS_KEY:
        return True
    if not candidate:
        return False
    try:
        return hmac.compare_digest(candidate, ADMIN_ACCESS_KEY)
    except ValueError:
        return False


def _has_admin_access(request: Request) -> bool:
    if not ADMIN_ACCESS_KEY:
        return True

    cookie_value = request.cookies.get(ADMIN_COOKIE_NAME)
    if cookie_value and ADMIN_KEY_SIGNATURE:
        try:
            if hmac.compare_digest(cookie_value, ADMIN_KEY_SIGNATURE):
                return True
        except ValueError:
            pass

    header_key = request.headers.get("x-admin-key")
    if _is_correct_admin_key(header_key):
        return True

    query_key = request.query_params.get("key")
    if _is_correct_admin_key(query_key):
        return True

    return False


def _attach_admin_cookie(response: RedirectResponse) -> RedirectResponse:
    if ADMIN_KEY_SIGNATURE:
        response.set_cookie(
            ADMIN_COOKIE_NAME,
            ADMIN_KEY_SIGNATURE,
            httponly=True,
            max_age=7 * 24 * 60 * 60,
            samesite="lax",
        )
    return response


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


def _coerce_datetime(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned.endswith("Z"):
            cleaned = cleaned[:-1] + "+00:00"
        try:
            return datetime.fromisoformat(cleaned)
        except ValueError:
            return None
    return None


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
    window_end = date.today()
    window_start = window_end - timedelta(days=29)

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
        profit_before_window = Decimal("0")

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

            created_at = _coerce_datetime(getattr(wager, "created_at", None))
            if created_at is None and getattr(wager, "matchup", None):
                created_at = _coerce_datetime(getattr(wager.matchup, "scheduled_at", None))

            if created_at is not None:
                day = created_at.date()
                if day < window_start:
                    profit_before_window += profit_delta
                    continue
                if day > window_end:
                    day = window_end
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

        if daily_profit or profit_before_window:
            profit_points: list[dict[str, object]] = []
            current_day = window_start
            running_total = profit_before_window
            while current_day <= window_end:
                delta = daily_profit.get(current_day, Decimal("0"))
                running_total += delta
                profit_points.append({"x": current_day.isoformat(), "y": float(running_total)})
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
            bet_points: list[dict[str, object]] = []
            current_day = window_start
            while current_day <= window_end:
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

    chart_payload = json.dumps(
        {
            "profit": profit_datasets,
            "bets": bet_datasets,
            "range": {
                "start": window_start.isoformat(),
                "end": window_end.isoformat(),
            },
        }
    )

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


@app.get("/admin", response_class=HTMLResponse)
async def admin_login(request: Request):
    if _is_correct_admin_key(request.query_params.get("key")) and ADMIN_ACCESS_KEY:
        return _attach_admin_cookie(RedirectResponse("/admin/wagers", status_code=303))

    if _has_admin_access(request):
        return RedirectResponse("/admin/wagers", status_code=303)

    if not ADMIN_ACCESS_KEY:
        return RedirectResponse("/admin/wagers", status_code=303)

    return templates.TemplateResponse(
        "admin_login.html",
        {"request": request, "error": bool(request.query_params.get("key"))},
    )


@app.post("/admin", response_class=HTMLResponse)
async def admin_login_submit(request: Request, key: str = Form(...)):
    if not ADMIN_ACCESS_KEY or _is_correct_admin_key(key):
        return _attach_admin_cookie(RedirectResponse("/admin/wagers", status_code=303))

    return templates.TemplateResponse(
        "admin_login.html",
        {"request": request, "error": True},
    )


@app.post("/admin/logout")
async def admin_logout():
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie(ADMIN_COOKIE_NAME)
    return response


@app.get("/admin/wagers", response_class=HTMLResponse)
async def admin_wagers(request: Request, db=Depends(get_db)):
    if ADMIN_ACCESS_KEY:
        query_key = request.query_params.get("key")
        if query_key and _is_correct_admin_key(query_key):
            return _attach_admin_cookie(RedirectResponse("/admin/wagers", status_code=303))
        if not _has_admin_access(request):
            return RedirectResponse("/admin", status_code=303)

    users = crud.get_users_with_wagers(db)
    team_lookup = crud.build_team_alias_lookup(db)
    status_counts: dict[str, int] = {status.value: 0 for status in models.WagerStatus}
    archived_count = 0
    total_wagers = 0

    for user in users:
        ordered: list[tuple[datetime, models.Wager]] = []
        for wager in user.wagers:
            total_wagers += 1
            status = _normalize_wager_status(wager)
            status_counts.setdefault(status, 0)
            status_counts[status] += 1
            if getattr(wager, "archived", False):
                archived_count += 1
            for leg in wager.legs:
                leg.matched_teams = crud.match_leg_description_to_teams(leg.description, team_lookup)
            created_at = wager.created_at
            if isinstance(created_at, str):
                try:
                    created_at_dt = datetime.fromisoformat(created_at)
                except ValueError:
                    created_at_dt = datetime.min
            elif isinstance(created_at, datetime):
                created_at_dt = created_at
            else:
                created_at_dt = datetime.min
            ordered.append((created_at_dt, wager))

        ordered.sort(key=lambda item: item[0], reverse=True)
        setattr(user, "all_wagers_admin", [item[1] for item in ordered])

    current_url = request.url.path
    if request.url.query:
        current_url = f"{current_url}?{request.url.query}"

    return templates.TemplateResponse(
        "admin_wagers.html",
        {
            "request": request,
            "users": users,
            "status_counts": status_counts,
            "archived_count": archived_count,
            "total_wagers": total_wagers,
            "wager_statuses": list(models.WagerStatus),
            "current_url": current_url,
        },
    )


@app.post("/wagers/{wager_id}/status")
async def update_wager_status(
    wager_id: int,
    status: str = Form(...),
    redirect_to: str = Form("/"),
    db=Depends(get_db),
):
    crud.update_wager_status(db, wager_id, status)
    target = redirect_to or "/"
    return RedirectResponse(target, status_code=303)


@app.post("/wagers/{wager_id}/legs/{leg_id}/status")
async def update_wager_leg_status(
    wager_id: int,
    leg_id: int,
    status: str = Form(...),
    redirect_to: str = Form("/"),
    db=Depends(get_db),
):
    crud.update_wager_leg_status(db, leg_id, status)
    target = redirect_to or "/"
    return RedirectResponse(target, status_code=303)


@app.post("/wagers/{wager_id}/archive")
async def update_wager_archive(
    wager_id: int,
    archived: bool = Form(...),
    redirect_to: str = Form("/"),
    db=Depends(get_db),
):
    crud.set_wager_archived(db, wager_id, archived)
    return RedirectResponse(redirect_to, status_code=303)


@app.post("/admin/wagers/{wager_id}/edit")
async def admin_edit_wager(
    request: Request,
    wager_id: int,
    description: str | None = Form(None),
    amount: str | None = Form(None),
    line: str | None = Form(None),
    status: str | None = Form(None),
    archived: str | None = Form(None),
    redirect_to: str = Form("/admin/wagers"),
    db=Depends(get_db),
):
    if ADMIN_ACCESS_KEY and not _has_admin_access(request):
        return RedirectResponse("/admin", status_code=303)

    archived_flag = None
    if archived is not None:
        normalized_archived = archived.strip().lower()
        if normalized_archived:
            archived_flag = normalized_archived in {"true", "1", "yes", "on"}

    crud.update_wager_details(
        db,
        wager_id,
        description=description,
        amount=amount,
        line=line,
        status=status,
        archived=archived_flag,
    )

    target = redirect_to or "/admin/wagers"
    return RedirectResponse(target, status_code=303)


@app.post("/admin/wagers/{wager_id}/delete")
async def admin_delete_wager(
    request: Request,
    wager_id: int,
    redirect_to: str = Form("/admin/wagers"),
    db=Depends(get_db),
):
    if ADMIN_ACCESS_KEY and not _has_admin_access(request):
        return RedirectResponse("/admin", status_code=303)

    crud.delete_wager(db, wager_id)
    target = redirect_to or "/admin/wagers"
    return RedirectResponse(target, status_code=303)
