from __future__ import annotations

from .models import Meal, Suggestion, WeekPlan, Wish
from .schemas import (
    DayOut,
    IngredientOut,
    MealOut,
    SuggestionOut,
    WeekPlanOut,
    WishOut,
)
from .week_utils import monday_of


def meal_out(meal: Meal) -> MealOut:
    return MealOut(
        id=meal.id,
        title=meal.title,
        photo_path=meal.photo_path,
        source=meal.source,
        chefkoch_url=meal.chefkoch_url,
        chefkoch_id=meal.chefkoch_id,
        base_servings=meal.base_servings,
        instructions=meal.instructions,
        notes=meal.notes,
        active=meal.active,
        ingredients=[
            IngredientOut(
                id=ing.id,
                name=ing.name,
                amount=ing.amount,
                unit=ing.unit,
                sort_order=ing.sort_order,
            )
            for ing in meal.ingredients
        ],
    )


def suggestion_out(s: Suggestion) -> SuggestionOut:
    return SuggestionOut(
        id=s.id,
        meal_id=s.meal_id,
        member_id=s.member_id,
        meal_title=s.meal.title if s.meal else None,
        member_name=s.member.name if s.member else None,
        created_at=s.created_at,
    )


def wish_out(w: Wish) -> WishOut:
    return WishOut(
        id=w.id,
        text=w.text,
        status=w.status,
        member_id=w.member_id,
        member_name=w.member.name if w.member else None,
        created_at=w.created_at,
    )


def week_plan_out(plan: WeekPlan, offset: int | None = None) -> WeekPlanOut:
    if offset is None:
        delta = (plan.week_start - monday_of()).days
        offset = max(0, delta // 7)
    return WeekPlanOut(
        id=plan.id,
        week_start=plan.week_start,
        week_offset=offset,
        status=plan.status,
        target_servings=plan.target_servings,
        days=[
            DayOut(
                weekday=day.weekday,
                meal_id=day.meal_id,
                servings=day.servings or plan.target_servings or 4,
                meal=meal_out(day.meal) if day.meal_id and day.meal else None,
            )
            for day in sorted(plan.days, key=lambda d: d.weekday)
        ],
        suggestions=[suggestion_out(s) for s in plan.suggestions],
        wishes=[wish_out(w) for w in plan.wishes],
    )
