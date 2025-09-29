import json
import os
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, date, timedelta, timezone
from typing import Optional
from urllib.parse import urlencode

from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .database import SessionLocal, get_db, init_db
from . import crud, models, schemas
from .routers import wagers
from .routers import users
from .routers import catalog
from .security import (
    SESSION_DURATION,
    build_session_token,
    ensure_initial_admin,
    parse_session_token,
    verify_password,
)

@dataclass
class AuthenticatedUser:
    id: int
    username: str
    is_admin: bool


app = FastAPI()
app.include_router(users.router)
app.include_router(wagers.router)
app.include_router(catalog.router)
templates = Jinja2Templates(directory="app/templates")

SESSION_COOKIE_NAME = "session_token"
SESSION_SECRET = os.getenv("SESSION_SECRET") or os.getenv("ADMIN_ACCESS_KEY") or "change-me"

templates.env.globals["admin_dashboard_path"] = "/admin/wagers"
templates.env.globals["session_cookie_name"] = SESSION_COOKIE_NAME


def _current_user(request: Request) -> Optional[AuthenticatedUser]:
    user = getattr(request.state, "auth_user", None)
    if isinstance(user, AuthenticatedUser):
        return user
    return None


def _sanitize_redirect_target(value: str, default: str = "/") -> str:
    if not value:
        return default
    if value.startswith("http://") or value.startswith("https://"):
        return default
    if not value.startswith("/"):
        return default
    return value


def _redirect_to_login(request: Request) -> RedirectResponse:
    next_target = request.url.path
    if request.url.query:
        next_target = f"{next_target}?{request.url.query}"
    login_url = "/admin"
    if next_target:
        login_url = f"{login_url}?{urlencode({'next': next_target})}"
    return RedirectResponse(login_url, status_code=303)


def _require_admin(request: Request) -> Optional[RedirectResponse]:
    user = _current_user(request)
    if not user or not user.is_admin:
        return _redirect_to_login(request)
    return None


def _attach_session_cookie(response: RedirectResponse, user_id: int) -> RedirectResponse:
    if not SESSION_SECRET:
        raise RuntimeError("SESSION_SECRET must be configured")

    token = build_session_token(user_id, SESSION_SECRET)
    response.set_cookie(
        SESSION_COOKIE_NAME,
        token,
        httponly=True,
        max_age=int(SESSION_DURATION.total_seconds()),
        samesite="lax",
    )
    return response


def _clear_session_cookie(response: RedirectResponse) -> RedirectResponse:
    response.delete_cookie(SESSION_COOKIE_NAME, samesite="lax")
    return response

@app.middleware("http")
async def populate_authenticated_user(request: Request, call_next):
    request.state.auth_user = None
    session_token = request.cookies.get(SESSION_COOKIE_NAME)
    if session_token and SESSION_SECRET:
        user_id = parse_session_token(session_token, SESSION_SECRET)
        if user_id is not None:
            db = SessionLocal()
            try:
                auth_user = crud.get_auth_user_by_id(db, user_id)
                if auth_user:
                    request.state.auth_user = AuthenticatedUser(
                        id=auth_user.id,
                        username=auth_user.username,
                        is_admin=bool(auth_user.is_admin),
                    )
            finally:
                db.close()
    response = await call_next(request)
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
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time(), tzinfo=timezone.utc)
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
    ensure_initial_admin()


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
    users = [user for user in crud.get_users_with_wagers(db) if getattr(user, "tracked", True)]
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
    user = _current_user(request)
    requested_next = request.query_params.get("next")
    next_target = _sanitize_redirect_target(requested_next, "/admin/wagers")
    if user and user.is_admin:
        return RedirectResponse(next_target, status_code=303)

    error_flag = request.query_params.get("error") == "1"
    return templates.TemplateResponse(
        "admin_login.html",
        {
            "request": request,
            "error": error_flag,
            "redirect_to": next_target,
        },
    )


@app.post("/admin", response_class=HTMLResponse)
async def admin_login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    redirect_to: str = Form("/admin/wagers"),
    db=Depends(get_db),
):
    next_target = _sanitize_redirect_target(redirect_to, "/admin/wagers")
    auth_user = crud.get_auth_user_by_username(db, username.strip())
    if (
        auth_user
        and auth_user.is_admin
        and verify_password(password, auth_user.salt, auth_user.password_hash)
    ):
        response = RedirectResponse(next_target, status_code=303)
        return _attach_session_cookie(response, auth_user.id)

    return templates.TemplateResponse(
        "admin_login.html",
        {
            "request": request,
            "error": True,
            "redirect_to": next_target,
        },
    )


def _logout_response() -> RedirectResponse:
    response = RedirectResponse("/", status_code=303)
    return _clear_session_cookie(response)


@app.post("/logout")
async def logout():
    return _logout_response()


@app.post("/admin/logout")
async def admin_logout():
    return _logout_response()


@app.get("/admin/wagers", response_class=HTMLResponse)
async def admin_wagers(request: Request, db=Depends(get_db)):
    guard = _require_admin(request)
    if guard:
        return guard

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


@app.post("/admin/users/{user_id}/tracking")
async def update_user_tracking(
    request: Request,
    user_id: int,
    tracked_state: str | None = Form(None),
    redirect_to: str = Form("/admin/wagers"),
    db=Depends(get_db),
):
    guard = _require_admin(request)
    if guard:
        return guard

    normalized = (tracked_state or "").strip().lower()
    tracked = normalized not in {"", "0", "false", "off", "no"}
    updated = crud.set_user_tracked(db, user_id, tracked)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    target = _sanitize_redirect_target(redirect_to, "/admin/wagers")
    return RedirectResponse(target, status_code=303)


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
    created_at: str | None = Form(None),
    redirect_to: str = Form("/admin/wagers"),
    db=Depends(get_db),
):
    guard = _require_admin(request)
    if guard:
        return guard

    archived_flag = None
    if archived is not None:
        normalized_archived = archived.strip().lower()
        if normalized_archived:
            archived_flag = normalized_archived in {"true", "1", "yes", "on"}

    created_at_dt = None
    if created_at is not None and created_at.strip():
        parsed = _coerce_datetime(created_at)
        if parsed is not None and parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        created_at_dt = parsed

    crud.update_wager_details(
        db,
        wager_id,
        description=description,
        amount=amount,
        line=line,
        status=status,
        archived=archived_flag,
        created_at=created_at_dt,
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
    guard = _require_admin(request)
    if guard:
        return guard

    crud.delete_wager(db, wager_id)
    target = redirect_to or "/admin/wagers"
    return RedirectResponse(target, status_code=303)
