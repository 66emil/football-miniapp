from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.database import AsyncSessionLocal
from .. import crud

router = APIRouter()

async def get_db():
    async with AsyncSessionLocal() as s:
        yield s

@router.post("/", status_code=201)
async def book(match_id: int, user_id: int, db: AsyncSession = Depends(get_db)):
    # TODO: user_id по-хорошему брать из auth-заголовка
    booking = await crud.create_booking(db, user_id, match_id)
    return booking
