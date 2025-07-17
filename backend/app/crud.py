from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Booking, Match
from datetime import datetime, timedelta

PAYMENT_TTL = 30  # минут

async def create_booking(db: AsyncSession, user_id: int, match_id: int) -> Booking:
    # сколько уже в основном списке?
    cnt_stmt = select(Booking).where(
        Booking.match_id == match_id,
        Booking.state == "main",
        Booking.paid_at.is_not(None)
    )
    res = await db.execute(cnt_stmt)
    main_count = res.scalars().unique().count()

    # узнаём вместимость матча
    m = await db.get(Match, match_id)
    state = "main" if main_count < m.capacity else "reserve"

    booking = Booking(
        user_id=user_id,
        match_id=match_id,
        state=state,
        expires_at=datetime.utcnow() + timedelta(minutes=PAYMENT_TTL) if state == "main" else None,
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking
