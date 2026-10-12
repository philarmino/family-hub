from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

import aiohttp
from bring_api import Bring, BringItemOperation

from ..config import Settings
from ..models import Ingredient, Meal, Wish
from .scaling import format_spec, scale_amount


@dataclass
class BringItem:
    name: str
    spec: str = ""


async def list_bring_lists(settings: Settings) -> list[dict[str, str]]:
    _require_credentials(settings)
    async with aiohttp.ClientSession() as session:
        bring = Bring(session, settings.bring_email, settings.bring_password)
        await bring.login()
        payload = await bring.load_lists()
        return [
            {"list_uuid": entry["listUuid"], "name": entry.get("name") or entry["listUuid"]}
            for entry in payload.get("lists", [])
        ]


def meal_to_items(meal: Meal, target_servings: int) -> list[BringItem]:
    items: list[BringItem] = []
    for ingredient in meal.ingredients:
        scaled = scale_amount(ingredient.amount, meal.base_servings, target_servings)
        items.append(
            BringItem(
                name=ingredient.name.strip(),
                spec=format_spec(scaled, ingredient.unit),
            )
        )
    return items


def wishes_to_items(wishes: list[Wish]) -> list[BringItem]:
    return [BringItem(name=wish.text.strip()) for wish in wishes if wish.text.strip()]


async def push_items(settings: Settings, items: list[BringItem]) -> int:
    _require_credentials(settings)
    if not settings.bring_list_uuid:
        raise ValueError("BRING_LIST_UUID ist nicht gesetzt")
    if not items:
        return 0

    payload = [
        {"itemId": item.name, "spec": item.spec, "uuid": str(uuid4())}
        for item in items
        if item.name
    ]
    async with aiohttp.ClientSession() as session:
        bring = Bring(session, settings.bring_email, settings.bring_password)
        await bring.login()
        await bring.batch_update_list(
            settings.bring_list_uuid,
            payload,
            BringItemOperation.ADD,
        )
    return len(payload)


def _require_credentials(settings: Settings) -> None:
    if not settings.bring_email or not settings.bring_password:
        raise ValueError("Bring!-Zugangsdaten (BRING_EMAIL / BRING_PASSWORD) fehlen")
