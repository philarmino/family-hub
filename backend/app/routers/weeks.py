from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..config import Settings, get_settings
from ..database import get_db
from ..models import Meal, Suggestion, Wish
from ..schemas import (
    BringPushRequest,
    BringPushResult,
    DaysUpdate,
    SuggestionCreate,
    SuggestionOut,
    WeekPlanOut,
    WishCreate,
    WishOut,
    WishUpdate,
)
from ..serializers import suggestion_out, week_plan_out, wish_out
from ..services import bring_service
from ..week_utils import MAX_WEEK_OFFSET, get_or_create_plan, reload_plan

router = APIRouter(prefix="/api/weeks", tags=["weeks"])


def _offset_param(offset: int = Query(0, ge=0, le=MAX_WEEK_OFFSET)) -> int:
    return offset


@router.get("/current", response_model=WeekPlanOut)
async def current_week(
    offset: int = Depends(_offset_param),
    db: AsyncSession = Depends(get_db),
):
    plan = await get_or_create_plan(db, offset)
    return week_plan_out(plan, offset)


@router.post("/current/suggestions", response_model=SuggestionOut)
async def add_suggestion(
    payload: SuggestionCreate,
    offset: int = Depends(_offset_param),
    db: AsyncSession = Depends(get_db),
):
    plan = await get_or_create_plan(db, offset)
    meal = await db.get(Meal, payload.meal_id)
    if not meal or not meal.active:
        raise HTTPException(404, "Essen nicht gefunden")

    existing = await db.execute(
        select(Suggestion).where(
            Suggestion.plan_id == plan.id,
            Suggestion.meal_id == payload.meal_id,
            Suggestion.member_id == payload.member_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(409, "Schon vorgeschlagen")

    suggestion = Suggestion(
        plan_id=plan.id,
        meal_id=payload.meal_id,
        member_id=payload.member_id,
    )
    db.add(suggestion)
    if plan.status == "suggesting":
        plan.status = "draft"
    await db.commit()
    result = await db.execute(
        select(Suggestion)
        .where(Suggestion.id == suggestion.id)
        .options(selectinload(Suggestion.meal), selectinload(Suggestion.member))
    )
    return suggestion_out(result.scalar_one())


@router.delete("/current/suggestions/{suggestion_id}")
async def remove_suggestion(
    suggestion_id: int,
    offset: int = Depends(_offset_param),
    db: AsyncSession = Depends(get_db),
):
    plan = await get_or_create_plan(db, offset)
    suggestion = await db.get(Suggestion, suggestion_id)
    if not suggestion or suggestion.plan_id != plan.id:
        raise HTTPException(404, "Vorschlag nicht gefunden")
    await db.delete(suggestion)
    await db.commit()
    return {"ok": True}


@router.post("/current/wishes", response_model=list[WishOut])
async def add_wishes(
    payload: WishCreate,
    offset: int = Depends(_offset_param),
    db: AsyncSession = Depends(get_db),
):
    plan = await get_or_create_plan(db, offset)
    created: list[Wish] = []
    for text in payload.texts:
        cleaned = text.strip()
        if not cleaned:
            continue
        wish = Wish(
            plan_id=plan.id,
            member_id=payload.member_id,
            text=cleaned[:200],
            status="pending",
        )
        db.add(wish)
        created.append(wish)
    if not created:
        raise HTTPException(400, "Keine gÃ¼ltigen Wunschtexte")
    await db.commit()
    for wish in created:
        await db.refresh(wish)
    return [
        WishOut(
            id=wish.id,
            text=wish.text,
            status=wish.status,
            member_id=wish.member_id,
            member_name=None,
            created_at=wish.created_at,
        )
        for wish in created
    ]


@router.patch("/current/wishes/{wish_id}", response_model=WishOut)
async def update_wish(
    wish_id: int,
    payload: WishUpdate,
    offset: int = Depends(_offset_param),
    db: AsyncSession = Depends(get_db),
):
    if payload.status not in {"approved", "rejected", "pending"}:
        raise HTTPException(400, "UngÃ¼ltiger Status")
    plan = await get_or_create_plan(db, offset)
    wish = await db.get(Wish, wish_id)
    if not wish or wish.plan_id != plan.id:
        raise HTTPException(404, "Wunsch nicht gefunden")
    wish.status = payload.status
    await db.commit()
    plan = await reload_plan(db, plan.id)
    updated = next(w for w in plan.wishes if w.id == wish_id)
    return wish_out(updated)


@router.put("/current/days", response_model=WeekPlanOut)
async def update_days(
    payload: DaysUpdate,
    offset: int = Depends(_offset_param),
    db: AsyncSession = Depends(get_db),
):
    plan = await get_or_create_plan(db, offset)
    if plan.status == "finalized":
        raise HTTPException(400, "Plan ist finalisiert - erst zuruecksetzen")

    day_map = {d.weekday: d for d in plan.days}
    for assignment in payload.days:
        day = day_map.get(assignment.weekday)
        if not day:
            continue
        if assignment.meal_id is not None:
            meal = await db.get(Meal, assignment.meal_id)
            if not meal:
                raise HTTPException(404, f"Essen {assignment.meal_id} nicht gefunden")
        day.meal_id = assignment.meal_id
        if assignment.servings is not None:
            day.servings = assignment.servings

    if payload.target_servings is not None:
        plan.target_servings = payload.target_servings
    if plan.status == "suggesting":
        plan.status = "draft"
    await db.commit()
    return week_plan_out(await reload_plan(db, plan.id), offset)


@router.post("/current/finalize", response_model=WeekPlanOut)
async def finalize_week(
    offset: int = Depends(_offset_param),
    db: AsyncSession = Depends(get_db),
):
    plan = await get_or_create_plan(db, offset)
    assigned = [d for d in plan.days if d.meal_id]
    if not assigned:
        raise HTTPException(400, "Mindestens einen Tag belegen")
    plan.status = "finalized"
    await db.commit()
    return week_plan_out(await reload_plan(db, plan.id), offset)


@router.post("/current/reopen", response_model=WeekPlanOut)
async def reopen_week(
    offset: int = Depends(_offset_param),
    db: AsyncSession = Depends(get_db),
):
    plan = await get_or_create_plan(db, offset)
    plan.status = "draft"
    await db.commit()
    return week_plan_out(await reload_plan(db, plan.id), offset)


@router.post("/current/reset-days", response_model=WeekPlanOut)
async def reset_days(
    offset: int = Depends(_offset_param),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Leert alle Tages-Essen der gewaehlten Woche und setzt Personen zurueck."""
    plan = await get_or_create_plan(db, offset)
    default_servings = plan.target_servings or settings.default_servings
    for day in plan.days:
        day.meal_id = None
        day.meal = None
        day.servings = default_servings
    plan.status = "suggesting"
    await db.commit()
    return week_plan_out(await reload_plan(db, plan.id), offset)


@router.post("/current/push-bring", response_model=BringPushResult)
async def push_bring(
    payload: BringPushRequest,
    offset: int = Depends(_offset_param),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    if not settings.bring_push_password or not secrets.compare_digest(
        payload.password, settings.bring_push_password
    ):
        raise HTTPException(403, "Falsches Passwort")

    plan = await get_or_create_plan(db, offset)
    items: list[bring_service.BringItem] = []

    if payload.include_meals:
        for day in plan.days:
            if day.meal:
                servings = day.servings or plan.target_servings or settings.default_servings
                items.extend(bring_service.meal_to_items(day.meal, servings))

    if payload.include_wishes:
        wishes = [w for w in plan.wishes if w.status == "approved"]
        if payload.wish_ids is not None:
            id_set = set(payload.wish_ids)
            wishes = [w for w in wishes if w.id in id_set]
        items.extend(bring_service.wishes_to_items(wishes))
    else:
        wishes = []

    seen: set[tuple[str, str]] = set()
    unique_items: list[bring_service.BringItem] = []
    for item in items:
        key = (item.name.lower(), item.spec.lower())
        if key in seen:
            continue
        seen.add(key)
        unique_items.append(item)

    try:
        count = await bring_service.push_items(settings, unique_items)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"Bring!-Fehler: {exc}") from exc

    if payload.include_wishes:
        for wish in wishes:
            wish.status = "pushed"
        await db.commit()

    return BringPushResult(
        ok=True,
        items_added=count,
        message=f"{count} EintrÃ¤ge zu Bring! hinzugefÃ¼gt",
    )
