from __future__ import annotations

from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .config import get_settings
from .models import Meal, Suggestion, WeekPlan, WeekPlanDay, Wish

MAX_WEEK_OFFSET = 2


def monday_of(d: date | None = None) -> date:
    today = d or date.today()
    return today - timedelta(days=today.weekday())


def week_start_for_offset(offset: int) -> date:
    if offset < 0 or offset > MAX_WEEK_OFFSET:
        raise HTTPException(400, f"offset muss 0-{MAX_WEEK_OFFSET} sein")
    return monday_of() + timedelta(weeks=offset)


async def reload_plan(db: AsyncSession, plan_id: int) -> WeekPlan:
    result = await db.execute(
        select(WeekPlan)
        .where(WeekPlan.id == plan_id)
        .options(
            selectinload(WeekPlan.days).selectinload(WeekPlanDay.meal).selectinload(Meal.ingredients),
            selectinload(WeekPlan.suggestions).selectinload(Suggestion.meal),
            selectinload(WeekPlan.suggestions).selectinload(Suggestion.member),
            selectinload(WeekPlan.wishes).selectinload(Wish.member),
        )
    )
    return result.scalar_one()


async def get_or_create_plan(db: AsyncSession, offset: int = 0) -> WeekPlan:
    week_start = week_start_for_offset(offset)
    result = await db.execute(select(WeekPlan).where(WeekPlan.week_start == week_start))
    plan = result.scalar_one_or_none()
    if plan:
        return await reload_plan(db, plan.id)

    settings = get_settings()
    plan = WeekPlan(
        week_start=week_start,
        status="suggesting",
        target_servings=settings.default_servings,
    )
    db.add(plan)
    await db.flush()
    for weekday in range(7):
        db.add(
            WeekPlanDay(
                plan_id=plan.id,
                weekday=weekday,
                meal_id=None,
                servings=settings.default_servings,
            )
        )
    await db.commit()
    return await reload_plan(db, plan.id)


async def get_or_create_current_plan(db: AsyncSession) -> WeekPlan:
    return await get_or_create_plan(db, 0)
