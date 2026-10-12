from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings
from ..models import Ingredient, Meal
from . import chefkoch as chefkoch_service

logger = logging.getLogger(__name__)

# Familienfreundliche Chefkoch-Beispiele (IDs aus Suche)
SEED_CHEFKOCH_URLS = [
    "https://www.chefkoch.de/rezepte/555331153292728/Omas-Hackfleischpfanne-mit-Gemuese.html",
    "https://www.chefkoch.de/rezepte/1061421211444101/Nudel-Hackfleisch-Auflauf.html",
    "https://www.chefkoch.de/rezepte/745721177147257/Lasagne.html",
    "https://www.chefkoch.de/rezepte/2165691347605868/Allerbeste-Oma-Nudeln.html",
    "https://www.chefkoch.de/rezepte/1750731284474566/Romys-Wuerstchengulasch.html",
    "https://www.chefkoch.de/rezepte/2508231393621075/Paprika-Hack-Pfanne-mit-Feta.html",
    "https://www.chefkoch.de/rezepte/1208161226570428/Der-perfekte-Pfannkuchen-gelingt-einfach-immer.html",
    "https://www.chefkoch.de/rezepte/878151193224107/Reis-Haehnchen-Auflauf.html",
]


async def seed_example_meals(db: AsyncSession, settings: Settings) -> int:
    """Importiert fehlende Beispielrezepte (nach chefkoch_id)."""
    imported = 0
    photos_dir = settings.data_dir / "photos"
    photos_dir.mkdir(parents=True, exist_ok=True)

    for url in SEED_CHEFKOCH_URLS:
        try:
            recipe = await chefkoch_service.fetch_recipe(url)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Seed Chefkoch fehlgeschlagen (%s): %s", url, exc)
            continue

        existing = await db.execute(
            select(Meal).where(Meal.chefkoch_id == recipe.chefkoch_id)
        )
        if existing.scalar_one_or_none():
            continue

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
            dest: Path = photos_dir / filename
            try:
                await chefkoch_service.download_image(recipe.image_url, dest)
                meal.photo_path = f"/media/photos/{filename}"
            except Exception as exc:  # noqa: BLE001
                logger.warning("Seed-Bild fehlgeschlagen: %s", exc)

        imported += 1

    if imported:
        await db.commit()
    return imported
