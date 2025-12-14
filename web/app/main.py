import asyncio
import json
import logging
import os
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, date, timedelta, timezone
from typing import Optional
from urllib.parse import urlencode

from fastapi import FastAPI, Request, Depends, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse, Response, JSONResponse
import requests
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.orm import selectinload

from .database import SessionLocal, get_db, init_db
from . import crud, models, schemas
from .services import espn
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
AI_PROXY_BASE_URL = (os.getenv("AI_PROXY_BASE_URL") or "http://40netse.fortiddns.com:3002/").rstrip("/")
AI_PROXY_PATH_PREFIXES: tuple[str, ...] = (
    "@vite",
    "@react-refresh",
    "src",
    "assets",
    "node_modules",
    "vite.svg",
    "api",
)


def _parse_positive_int_env(var_name: str, default: int) -> int:
    raw_value = os.getenv(var_name)
    if raw_value is None:
        return default
    try:
        parsed = int(raw_value)
        if parsed > 0:
            return parsed
    except ValueError:
        pass
    return default


AUTO_ARCHIVE_INTERVAL_SECONDS = _parse_positive_int_env(
    "WAGER_AUTO_ARCHIVE_INTERVAL_SECONDS",
    60 * 60 * 72,
)
AUTO_ARCHIVE_INITIAL_DELAY_SECONDS = _parse_positive_int_env(
    "WAGER_AUTO_ARCHIVE_INITIAL_DELAY_SECONDS",
    60,
)

logger = logging.getLogger(__name__)

_archive_task: asyncio.Task | None = None

LEAGUE_LABELS = {
    key: key.upper()
    for key in espn.SUPPORTED_LEAGUES
}

templates.env.globals["admin_dashboard_path"] = "/admin/wagers"
templates.env.globals["session_cookie_name"] = SESSION_COOKIE_NAME

STATS_WINDOW_OPTIONS: dict[str, dict[str, object]] = {
    "30": {"label": "30 Days", "days": 30},
    "90": {"label": "90 Days", "days": 90},
    "180": {"label": "180 Days", "days": 180},
    "365": {"label": "1 Year", "days": 365},
}
DEFAULT_STATS_WINDOW = "30"


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


def _should_proxy_ai_path(path: str) -> bool:
    normalized = (path or "").lstrip("/")
    if not normalized:
        return False
    for prefix in AI_PROXY_PATH_PREFIXES:
        if normalized == prefix or normalized.startswith(f"{prefix.rstrip('/')}/"):
            return True
    return False


def _build_ai_proxy_url(path: str, query_string: str | None) -> str:
    normalized_path = path or "/"
    if not normalized_path.startswith("/"):
        normalized_path = f"/{normalized_path}"
    base = AI_PROXY_BASE_URL
    if normalized_path == "/" and base.endswith("/"):
        target = base
    else:
        target = f"{base.rstrip('/')}{normalized_path}"
    if query_string:
        target = f"{target}?{query_string}"
    return target


async def _proxy_ai_content(path: str, request: Request) -> Response:
    if not AI_PROXY_BASE_URL:
        raise HTTPException(status_code=503, detail="AI proxy is not configured")

    target_url = _build_ai_proxy_url(path, request.url.query)

    def _fetch():
        return requests.get(target_url, timeout=20)

    try:
        upstream = await asyncio.to_thread(_fetch)
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Failed to reach AI proxy: {exc}") from exc

    media_type = upstream.headers.get("content-type")
    forward_headers: dict[str, str] = {}
    for header in ("cache-control", "content-language", "expires", "last-modified"):
        value = upstream.headers.get(header)
        if value:
            forward_headers[header] = value

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        media_type=media_type,
        headers=forward_headers,
    )

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
        if getattr(wager, "is_free_play", False):
            return Decimal("0")
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


def _archive_decided_wagers_sync() -> int:
    db = SessionLocal()
    try:
        return crud.archive_decided_wagers(db)
    finally:
        db.close()


async def _archive_decided_wagers_once() -> int:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _archive_decided_wagers_sync)


async def _archive_scheduler():
    if AUTO_ARCHIVE_INITIAL_DELAY_SECONDS:
        try:
            await asyncio.sleep(AUTO_ARCHIVE_INITIAL_DELAY_SECONDS)
        except asyncio.CancelledError:
            raise

    while True:
        try:
            count = await _archive_decided_wagers_once()
            if count:
                logger.info("Auto-archived %s decided wagers", count)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Failed to auto-archive decided wagers")

        try:
            await asyncio.sleep(AUTO_ARCHIVE_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            raise


def _calculate_week_start(reference: date, week_offset: int) -> date:
    monday = reference - timedelta(days=reference.weekday())
    return monday + timedelta(days=week_offset * 7)


def _format_game_time(value: datetime | None) -> str:
    if value is None:
        return "TBD"
    local_time = value.astimezone()
    time_str = local_time.strftime("%I:%M %p").lstrip("0")
    tz_abbr = local_time.strftime("%Z")
    if tz_abbr:
        return f"{time_str} {tz_abbr}"
    return time_str


def _format_decimal_value(value: float) -> str:
    if abs(value - round(value)) < 1e-6:
        return str(int(round(value)))
    return f"{value:.1f}".rstrip("0").rstrip(".")


def _format_moneyline_value(value: object) -> str | None:
    if value is None:
        return None
    try:
        number = int(round(float(value)))
    except (TypeError, ValueError):
        return None
    sign = "+" if number > 0 else ""
    return f"{sign}{number}"


def _format_spread_value(value: object) -> str | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if abs(number) < 1e-6:
        return "PK"
    formatted = _format_decimal_value(abs(number))
    sign = "+" if number > 0 else "-"
    return f"{sign}{formatted}"


def _format_total_value(value: object) -> str | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return _format_decimal_value(number)


def _serialize_schedule(days: list[espn.DaySchedule]):
    serialized: list[dict[str, object]] = []
    for day in days:
        games: list[dict[str, object]] = []
        for game in day.games:
            networks = ", ".join(game.networks)

            serialized_teams: list[dict[str, object]] = []
            for team in sorted(game.teams, key=lambda t: t.is_home):
                serialized_teams.append(
                    {
                        "name": team.name,
                        "abbreviation": team.abbreviation,
                        "record": team.record,
                        "score": team.score,
                        "is_home": team.is_home,
                        "logo": team.logo,
                        "moneyline": _format_moneyline_value(team.moneyline),
                        "spread": _format_spread_value(team.spread),
                        "spread_odds": _format_moneyline_value(team.spread_odds),
                        "favorite": bool(team.favorite) if team.favorite is not None else None,
                    }
                )

            odds_info = None
            if getattr(game, "odds", None):
                odds_info = {
                    "provider": game.odds.provider,
                    "details": game.odds.details,
                    "spread": _format_spread_value(game.odds.spread),
                    "over_under": _format_total_value(game.odds.over_under),
                }

            games.append(
                {
                    "id": game.event_id,
                    "name": game.name,
                    "short_name": game.short_name,
                    "status": game.status,
                    "status_detail": game.status_detail,
                    "start_time": _format_game_time(game.start_time),
                    "raw_start_time": game.start_time,
                    "venue": game.venue,
                    "networks": networks,
                    "teams": serialized_teams,
                    "odds": odds_info,
                }
            )
        serialized.append(
            {
                "day": day.day,
                "games": games,
            }
        )
    return serialized


@app.get("/health")
async def health_check():
    details = {"app": "ok"}
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - best effort logging
        logger.exception("Health check failed to reach database: %s", exc)
        return JSONResponse(status_code=503, content={"app": "ok", "database": "unreachable"})
    details["database"] = "ok"
    return details


@app.on_event("startup")
async def startup():
    init_db()
    ensure_initial_admin()
    try:
        count = await _archive_decided_wagers_once()
        if count:
            logger.info("Auto-archived %s decided wagers on startup", count)
    except Exception:
        logger.exception("Failed to auto-archive decided wagers during startup")

    global _archive_task
    if _archive_task is None:
        _archive_task = asyncio.create_task(_archive_scheduler())


@app.on_event("shutdown")
async def shutdown_event():
    global _archive_task
    task = _archive_task
    if task is not None:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        finally:
            _archive_task = None


@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request, db=Depends(get_db)):
    raw_users = crud.get_users_with_wagers(db)
    users = [user for user in raw_users if getattr(user, "tracked", True)]
    team_lookup = crud.build_team_alias_lookup(db)
    for user in users:
        wagers = getattr(user, "active_wagers", user.wagers)
        for wager in wagers:
            for leg in wager.legs:
                leg.matched_teams = crud.match_leg_description_to_teams(leg.description, team_lookup)

    # Build a small "recent wagers" list (5 most recent wagers across all users)
    recent_wagers: list[dict[str, object]] = []
    try:
        recent_query = (
            db.query(models.Wager)
            .order_by(models.Wager.created_at.desc())
            .limit(5)
            .all()
        )
    except Exception:
        recent_query = []

    for wager in recent_query:
        try:
            user = getattr(wager, "user", None)
            user_display = getattr(user, "display_name", None) or (f"User {getattr(user, 'id', '')}" if user else "Unknown")
            status = _normalize_wager_status(wager)
            try:
                amount_value = float(wager.amount) if wager.amount is not None else None
            except Exception:
                amount_value = None
            recent_wagers.append(
                {
                    "id": wager.id,
                    "user_display_name": user_display,
                    "description": (wager.description or "").strip(),
                    "amount": amount_value,
                    "line": wager.line or "",
                    "status": status,
                    "created_at": getattr(wager, "created_at", None),
                }
            )
        except Exception:
            continue

    return templates.TemplateResponse("index.html", {"request": request, "users": users, "recent_wagers": recent_wagers})


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


DECIDED_WAGER_STATUSES = {
    models.WagerStatus.won.value,
    models.WagerStatus.lost.value,
}


@app.get("/stats", response_class=HTMLResponse)
async def view_stats(request: Request, db=Depends(get_db)):
    requested_window = request.query_params.get("range", DEFAULT_STATS_WINDOW)
    if requested_window not in STATS_WINDOW_OPTIONS:
        requested_window = DEFAULT_STATS_WINDOW
    window_config = STATS_WINDOW_OPTIONS[requested_window]
    window_days = int(window_config["days"])
    users = [user for user in crud.get_users_with_wagers(db) if getattr(user, "tracked", True)]
    player_stats: list[dict[str, object]] = []
    profit_datasets: list[dict[str, object]] = []
    bet_datasets: list[dict[str, object]] = []
    window_end = date.today()
    window_start = window_end - timedelta(days=window_days - 1)

    def _serialize_wager_detail(
        wager: models.Wager,
        *,
        amount_value: Decimal,
        status_value: str,
        profit_value: Decimal | None,
    ) -> dict[str, object]:
        description = (wager.description or "").strip()
        if not description:
            description = f"Wager #{wager.id}"
        detail: dict[str, object] = {
            "id": wager.id,
            "description": description,
            "status": status_value,
            "amount": float(amount_value),
            "is_free_play": bool(getattr(wager, "is_free_play", False)),
            "is_live_bet": bool(getattr(wager, "is_live_bet", False)),
        }
        if profit_value is None:
            detail["profit"] = None
        else:
            detail["profit"] = float(profit_value)
        return detail

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
        daily_profit_details: dict[date, list[dict[str, object]]] = {}
        daily_bets: dict[date, int] = {}
        daily_bet_details: dict[date, list[dict[str, object]]] = {}
        profit_before_window = Decimal("0")

        for wager in wagers:
            status = _normalize_wager_status(wager)
            amount_raw = wager.amount if wager.amount is not None else Decimal("0")
            amount = Decimal(str(amount_raw))
            if not getattr(wager, "is_free_play", False):
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

            placed_day = created_at.date() if created_at else None
            if placed_day is not None and window_start <= placed_day <= window_end:
                detail = _serialize_wager_detail(
                    wager,
                    amount_value=amount,
                    status_value=status,
                    profit_value=None,
                )
                daily_bets.setdefault(placed_day, 0)
                daily_bets[placed_day] += 1
                daily_bet_details.setdefault(placed_day, []).append(detail)

            result_datetime = _coerce_datetime(getattr(wager, "resulted_at", None))
            if result_datetime is None and status in DECIDED_WAGER_STATUSES and getattr(wager, "matchup", None):
                result_datetime = _coerce_datetime(getattr(wager.matchup, "scheduled_at", None))
            result_day = result_datetime.date() if result_datetime else placed_day
            if result_day is not None:
                if result_day < window_start:
                    profit_before_window += profit_delta
                    continue
                if result_day > window_end:
                    result_day = window_end
                daily_profit[result_day] = daily_profit.get(result_day, Decimal("0")) + profit_delta
                daily_profit_details.setdefault(result_day, []).append(
                    _serialize_wager_detail(
                        wager,
                        amount_value=amount,
                        status_value=status,
                        profit_value=profit_delta,
                    )
                )
            elif profit_delta:
                profit_before_window += profit_delta

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
            profit_points: list[dict[str, object]] = []
            running_total = profit_before_window
            for result_day in sorted(daily_profit.keys()):
                running_total += daily_profit[result_day]
                profit_points.append(
                    {
                        "x": result_day.isoformat(),
                        "y": float(running_total),
                        "bets": daily_profit_details.get(result_day, []),
                    }
                )
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
            for bet_day in sorted(daily_bets.keys()):
                bet_points.append(
                    {
                        "x": bet_day.isoformat(),
                        "y": daily_bets[bet_day],
                        "bets": daily_bet_details.get(bet_day, []),
                    }
                )
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
            "selected_range": requested_window,
            "range_options": [
                {"key": key, "label": config["label"]}
                for key, config in STATS_WINDOW_OPTIONS.items()
            ],
            "range_label": window_config["label"],
        },
    )


@app.get("/ai-tools", response_class=HTMLResponse)
async def view_ai_tools(request: Request):
    return templates.TemplateResponse(
        "ai_tools.html",
        {
            "request": request,
            "ai_proxy_configured": bool(AI_PROXY_BASE_URL),
        },
    )


@app.get("/ai-tools/proxy")
async def proxy_ai_root(request: Request):
    return await _proxy_ai_content("/", request)


@app.get("/ai-tools/proxy/{resource_path:path}")
async def proxy_ai_resource(resource_path: str, request: Request):
    path = f"/{resource_path.lstrip('/')}" if resource_path else "/"
    return await _proxy_ai_content(path, request)


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


@app.get("/games", response_class=HTMLResponse)
async def view_games(
    request: Request,
    league: str = Query(espn.DEFAULT_LEAGUE),
    week: int = Query(0),
):
    normalized_league = (league or espn.DEFAULT_LEAGUE).lower()
    if normalized_league not in espn.SUPPORTED_LEAGUES:
        normalized_league = espn.DEFAULT_LEAGUE

    week_offset = week
    reference_day = date.today()
    week_start = _calculate_week_start(reference_day, week_offset)
    week_end = week_start + timedelta(days=6)

    schedules = await asyncio.to_thread(
        espn.fetch_week_schedule,
        normalized_league,
        week_start,
    )

    schedule_days = _serialize_schedule(schedules)

    context = {
        "request": request,
        "league": normalized_league,
        "league_tabs": [
            {
                "key": key,
                "label": LEAGUE_LABELS.get(key, key.upper()),
                "active": key == normalized_league,
                "url": f"/games?league={key}&week={week_offset}",
            }
            for key in espn.SUPPORTED_LEAGUES
        ],
        "week_start": week_start,
        "week_end": week_end,
        "week_label": f"{week_start.strftime('%b %d, %Y')} – {week_end.strftime('%b %d, %Y')}",
        "week_offset": week_offset,
        "prev_week": week_offset - 1,
        "next_week": week_offset + 1,
        "is_current_week": week_offset == 0,
        "schedule_days": schedule_days,
    }

    return templates.TemplateResponse("games.html", context)


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
    free_play_present: str | None = Form(None),
    is_free_play: str | None = Form(None),
    live_bet_present: str | None = Form(None),
    is_live_bet: str | None = Form(None),
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

    free_play_flag = None
    if free_play_present is not None:
        normalized_free_play = (is_free_play or "").strip().lower()
        free_play_flag = normalized_free_play in {"true", "1", "yes", "on"}

    live_bet_flag = None
    if live_bet_present is not None:
        normalized_live = (is_live_bet or "").strip().lower()
        live_bet_flag = normalized_live in {"true", "1", "yes", "on"}

    crud.update_wager_details(
        db,
        wager_id,
        description=description,
        amount=amount,
        line=line,
        status=status,
        archived=archived_flag,
        is_free_play=free_play_flag,
        is_live_bet=live_bet_flag,
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


@app.get("/{proxy_path:path}", include_in_schema=False)
async def proxy_ai_prefixed_paths(proxy_path: str, request: Request):
    if _should_proxy_ai_path(proxy_path):
        normalized = proxy_path if proxy_path.startswith("/") else f"/{proxy_path}"
        return await _proxy_ai_content(normalized, request)
    raise HTTPException(status_code=404, detail="Not Found")
