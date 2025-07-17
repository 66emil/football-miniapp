from datetime import datetime
from fastapi import APIRouter, Depends
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.database import AsyncSessionLocal
from ..models import Match

router = APIRouter()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

@router.get("/upcoming")
async def upcoming(db: AsyncSession = Depends(get_db)):
    stmt = select(Match).where(Match.starts_at > datetime.utcnow()).order_by(Match.starts_at).limit(6)
    res = await db.execute(stmt)
    return res.scalars().all()
