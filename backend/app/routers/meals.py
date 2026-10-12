from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..config import Settings, get_settings
from ..database import get_db
from ..models import Ingredient, Meal
from ..schemas import ChefkochImport, MealCreate, MealOut, MealUpdate
from ..serializers import meal_out
from ..services import chefkoch as chefkoch_service

router = APIRouter(prefix="/api/meals", tags=["meals"])


async def _get_meal(db: AsyncSession, meal_id: int) -> Meal:
    result = await db.execute(
        select(Meal).where(Meal.id == meal_id).options(selectinload(Meal.ingredients))
    )
    meal = result.scalar_one_or_none()
    if not meal:
        raise HTTPException(404, "Essen nicht gefunden")
    return meal


@router.get("", response_model=list[MealOut])
async def list_meals(active_only: bool = True, db: AsyncSession = Depends(get_db)):
    stmt = select(Meal).options(selectinload(Meal.ingredients)).order_by(Meal.title)
    if active_only:
        stmt = stmt.where(Meal.active.is_(True))
    result = await db.execute(stmt)
    return [meal_out(m) for m in result.scalars().all()]


@router.get("/{meal_id}", response_model=MealOut)
async def get_meal(meal_id: int, db: AsyncSession = Depends(get_db)):
    return meal_out(await _get_meal(db, meal_id))


@router.post("", response_model=MealOut)
async def create_meal(payload: MealCreate, db: AsyncSession = Depends(get_db)):
    meal = Meal(
        title=payload.title.strip(),
        base_servings=payload.base_servings,
        instructions=payload.instructions,
        notes=payload.notes,
        source=payload.source,
        chefkoch_url=payload.chefkoch_url,
        chefkoch_id=payload.chefkoch_id,
    )
    for idx, ing in enumerate(payload.ingredients):
        meal.ingredients.append(
            Ingredient(
                name=ing.name.strip(),
                amount=ing.amount,
                unit=ing.unit,
                sort_order=ing.sort_order if ing.sort_order else idx,
            )
        )
    db.add(meal)
    await db.commit()
    return meal_out(await _get_meal(db, meal.id))


@router.put("/{meal_id}", response_model=MealOut)
async def update_meal(meal_id: int, payload: MealUpdate, db: AsyncSession = Depends(get_db)):
    meal = await _get_meal(db, meal_id)
    if payload.title is not None:
        meal.title = payload.title.strip()
    if payload.base_servings is not None:
        meal.base_servings = payload.base_servings
    if payload.instructions is not None:
        meal.instructions = payload.instructions
    if payload.notes is not None:
        meal.notes = payload.notes
    if payload.active is not None:
        meal.active = payload.active
    if payload.ingredients is not None:
        meal.ingredients.clear()
        await db.flush()
        for idx, ing in enumerate(payload.ingredients):
            meal.ingredients.append(
                Ingredient(
                    name=ing.name.strip(),
                    amount=ing.amount,
                    unit=ing.unit,
                    sort_order=ing.sort_order if ing.sort_order else idx,
                )
            )
    await db.commit()
    return meal_out(await _get_meal(db, meal.id))


@router.delete("/{meal_id}")
async def delete_meal(meal_id: int, db: AsyncSession = Depends(get_db)):
    meal = await _get_meal(db, meal_id)
    meal.active = False
    await db.commit()
    return {"ok": True}


@router.post("/{meal_id}/photo", response_model=MealOut)
async def upload_photo(
    meal_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    meal = await _get_meal(db, meal_id)
    suffix = Path(file.filename or "photo.jpg").suffix.lower() or ".jpg"
    if suffix not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        raise HTTPException(400, "Nur Bilddateien erlaubt")
    filename = f"{meal_id}_{uuid.uuid4().hex[:8]}{suffix}"
    dest = settings.data_dir / "photos" / filename
    content = await file.read()
    dest.write_bytes(content)
    meal.photo_path = f"/media/photos/{filename}"
    await db.commit()
    return meal_out(await _get_meal(db, meal.id))


@router.post("/from-chefkoch", response_model=MealOut)
async def import_chefkoch(
    payload: ChefkochImport,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    try:
        recipe = await chefkoch_service.fetch_recipe(payload.url.strip())
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"Chefkoch nicht erreichbar: {exc}") from exc

    meal = Meal(
        title=recipe.title,
        source="chefkoch",
        chefkoch_url=recipe.url,
        chefkoch_id=recipe.chefkoch_id,
        base_servings=recipe.base_servings,
        instructions=recipe.instructions,
    )
    for idx, ing in enumerate(recipe.ingredients):
        meal.ingredients.append(
            Ingredient(
                name=ing.name,
                amount=ing.amount,
                unit=ing.unit,
                sort_order=idx,
            )
        )
    db.add(meal)
    await db.flush()

    if recipe.image_url:
        filename = f"{meal.id}_{recipe.chefkoch_id}.jpg"
        dest = settings.data_dir / "photos" / filename
        try:
            await chefkoch_service.download_image(recipe.image_url, dest)
            meal.photo_path = f"/media/photos/{filename}"
        except Exception:  # noqa: BLE001
            pass

    await db.commit()
    return meal_out(await _get_meal(db, meal.id))
