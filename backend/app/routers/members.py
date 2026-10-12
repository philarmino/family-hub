from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import FamilyMember
from ..schemas import MemberCreate, MemberOut

router = APIRouter(prefix="/api/members", tags=["members"])


@router.get("", response_model=list[MemberOut])
async def list_members(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FamilyMember).order_by(FamilyMember.name))
    return result.scalars().all()


@router.post("", response_model=MemberOut)
async def create_member(payload: MemberCreate, db: AsyncSession = Depends(get_db)):
    if payload.role not in {"kid", "parent"}:
        raise HTTPException(400, "role muss kid oder parent sein")
    member = FamilyMember(name=payload.name.strip(), role=payload.role)
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member


@router.delete("/{member_id}")
async def delete_member(member_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FamilyMember).where(FamilyMember.id == member_id))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(404, "Mitglied nicht gefunden")
    await db.delete(member)
    await db.commit()
    return {"ok": True}
