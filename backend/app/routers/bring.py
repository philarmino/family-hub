from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..config import Settings, get_settings
from ..schemas import BringListOut
from ..services import bring_service

router = APIRouter(prefix="/api/bring", tags=["bring"])


class PasswordBody(BaseModel):
    password: str


@router.post("/lists", response_model=list[BringListOut])
async def get_lists(payload: PasswordBody, settings: Settings = Depends(get_settings)):
    if not settings.bring_push_password or not secrets.compare_digest(
        payload.password, settings.bring_push_password
    ):
        raise HTTPException(403, "Falsches Passwort")
    try:
        lists = await bring_service.list_bring_lists(settings)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"Bring!-Fehler: {exc}") from exc
    return [BringListOut(**entry) for entry in lists]
