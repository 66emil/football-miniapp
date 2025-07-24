# backend/app/routers/matches.py
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import SQLModel, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import AsyncSessionLocal
from ..models import Match


router = APIRouter(prefix="/matches", tags=["matches"])


# ───────────────────────── dependency ─────────────────────────
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


# ───────────────────────── upcoming (был) ─────────────────────
@router.get("/upcoming", response_model=list[Match])
async def upcoming(db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Match)
        .where(
            Match.starts_at > datetime.utcnow(),
            Match.status != "cancelled"           # ← НЕ показываем отменённые
        )
        .order_by(Match.starts_at)
        .limit(6)
    )
    res = await db.execute(stmt)
    return res.scalars().all()


# ───────────────────────── GET /matches/{id} ─────────────────
@router.get("/{match_id}", response_model=Match)
async def get_match(match_id: int, db: AsyncSession = Depends(get_db)):
    match = await db.get(Match, match_id)
    if not match:
        raise HTTPException(404, detail="Match not found")
    return match


# ───────────────────────── PATCH /matches/{id} ───────────────
class MatchPatch(SQLModel):
    starts_at: datetime | None = None
    capacity:  int      | None = None
    price:     int      | None = None

@router.patch("/{match_id}", response_model=Match)
async def patch_match(
    match_id: int,
    data: MatchPatch,
    db: AsyncSession = Depends(get_db),
):
    match: Match | None = await db.get(Match, match_id)
    if not match:
        raise HTTPException(404, "Match not found")

    # обновляем только переданные поля
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(match, field, value)

    await db.commit()
    await db.refresh(match)
    return match


