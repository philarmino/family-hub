from __future__ import annotations

import re
from dataclasses import dataclass

import httpx


CHEFKOCH_ID_RE = re.compile(r"/rezepte/(\d+)")


@dataclass
class ParsedIngredient:
    name: str
    amount: float | None
    unit: str | None


@dataclass
class ChefkochRecipe:
    chefkoch_id: str
    title: str
    url: str
    base_servings: int
    instructions: str | None
    image_url: str | None
    ingredients: list[ParsedIngredient]


def extract_recipe_id(url: str) -> str:
    match = CHEFKOCH_ID_RE.search(url)
    if not match:
        raise ValueError("Keine gültige Chefkoch-Rezept-URL")
    return match.group(1)


def _parse_amount(raw: object) -> float | None:
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    text = str(raw).strip().replace(",", ".")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


async def fetch_recipe(url: str) -> ChefkochRecipe:
    recipe_id = extract_recipe_id(url)
    api_url = f"https://api.chefkoch.de/v2/recipes/{recipe_id}"
    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        response = await client.get(api_url)
        if response.status_code == 404:
            raise ValueError("Rezept bei Chefkoch nicht gefunden")
        response.raise_for_status()
        data = response.json()

    ingredients: list[ParsedIngredient] = []
    for group in data.get("ingredientGroups") or []:
        for item in group.get("ingredients") or []:
            name = (item.get("name") or item.get("ingredient") or "").strip()
            if not name:
                continue
            unit = item.get("unit") or item.get("unitName")
            if unit is not None:
                unit = str(unit).strip() or None
            ingredients.append(
                ParsedIngredient(
                    name=name,
                    amount=_parse_amount(item.get("amount") or item.get("quantity")),
                    unit=unit,
                )
            )

    image_url = None
    preview = data.get("previewImageUrlTemplate")
    if preview and isinstance(preview, str):
        image_url = preview.replace("<format>", "crop-600x400")
    elif data.get("imageUrl"):
        image_url = data["imageUrl"]

    instructions = data.get("instructions") or data.get("description")
    servings = data.get("servings") or data.get("numberOfPortions") or 4

    site_url = data.get("siteUrl") or f"https://www.chefkoch.de/rezepte/{recipe_id}/"

    return ChefkochRecipe(
        chefkoch_id=str(recipe_id),
        title=(data.get("title") or f"Rezept {recipe_id}").strip(),
        url=site_url,
        base_servings=max(1, int(servings)),
        instructions=instructions,
        image_url=image_url,
        ingredients=ingredients,
    )


async def download_image(url: str, dest_path) -> None:
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
        dest_path.write_bytes(response.content)
