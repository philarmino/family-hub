from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class IngredientIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    amount: float | None = None
    unit: str | None = None
    sort_order: int = 0


class IngredientOut(IngredientIn):
    id: int

    model_config = {"from_attributes": True}


class MealCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    base_servings: int = Field(default=4, ge=1, le=50)
    instructions: str | None = None
    notes: str | None = None
    ingredients: list[IngredientIn] = []
    source: str = "custom"
    chefkoch_url: str | None = None
    chefkoch_id: str | None = None


class MealUpdate(BaseModel):
    title: str | None = None
    base_servings: int | None = Field(default=None, ge=1, le=50)
    instructions: str | None = None
    notes: str | None = None
    ingredients: list[IngredientIn] | None = None
    active: bool | None = None


class MealOut(BaseModel):
    id: int
    title: str
    photo_path: str | None
    source: str
    chefkoch_url: str | None
    chefkoch_id: str | None
    base_servings: int
    instructions: str | None
    notes: str | None
    active: bool
    ingredients: list[IngredientOut] = []

    model_config = {"from_attributes": True}


class ChefkochImport(BaseModel):
    url: str


class MemberCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    role: str = "kid"


class MemberOut(BaseModel):
    id: int
    name: str
    role: str

    model_config = {"from_attributes": True}


class SuggestionCreate(BaseModel):
    meal_id: int
    member_id: int | None = None


class SuggestionOut(BaseModel):
    id: int
    meal_id: int
    member_id: int | None
    meal_title: str | None = None
    member_name: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class WishCreate(BaseModel):
    texts: list[str] = Field(min_length=1)
    member_id: int | None = None


class WishUpdate(BaseModel):
    status: str  # approved | rejected


class WishOut(BaseModel):
    id: int
    text: str
    status: str
    member_id: int | None
    member_name: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DayAssignment(BaseModel):
    weekday: int = Field(ge=0, le=6)
    meal_id: int | None = None
    servings: int | None = Field(default=None, ge=1, le=50)


class DaysUpdate(BaseModel):
    days: list[DayAssignment]
    target_servings: int | None = Field(default=None, ge=1, le=50)


class DayOut(BaseModel):
    weekday: int
    meal_id: int | None
    servings: int = 4
    meal: MealOut | None = None


class WeekPlanOut(BaseModel):
    id: int
    week_start: date
    week_offset: int = 0
    status: str
    target_servings: int
    days: list[DayOut] = []
    suggestions: list[SuggestionOut] = []
    wishes: list[WishOut] = []


class BringPushRequest(BaseModel):
    password: str
    include_meals: bool = True
    include_wishes: bool = True
    wish_ids: list[int] | None = None  # if set, only these approved wishes


class BringPushResult(BaseModel):
    ok: bool
    items_added: int
    message: str


class BringListOut(BaseModel):
    list_uuid: str
    name: str
