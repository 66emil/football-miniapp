from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from .models import Booking, Match
from datetime import datetime, timedelta
from .payments import yk_create_payment

PAYMENT_TTL = 30  # минут

async def create_booking(db, user_id: int, match_id: int) -> Booking:
    # 1. сколько уже подтверждённых «main»-мест
    cnt_stmt = (
        select(func.count())
        .select_from(Booking)
        .where(
            Booking.match_id == match_id,
            Booking.state == "main",
            Booking.paid_at.is_not(None),
        )
    )
    main_count: int = (await db.scalar(cnt_stmt)) or 0   # ← одно число

    # 2. берём сам матч и смотрим capacity
    match: Match | None = await db.get(Match, match_id)
    if match is None:
        raise ValueError("Match not found")

    state = "main" if main_count < match.capacity else "reserve"

    booking = Booking(
        user_id=user_id,
        match_id=match_id,
        state=state,
        # резервистам даём TTL
        expires_at=datetime.utcnow() + timedelta(minutes=PAYMENT_TTL) if state == "reserve" else None,
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)

    payment_url: str | None = None
    if booking.state == "main":
        # создаём платёж в ЮKassa
        confirmation_url, pay_id = yk_create_payment(match.price, booking.id)

        booking.payment_id = pay_id
        payment_url = confirmation_url
        await db.commit()                  # сохраняем payment_id

    return {
        "booking": booking,
        "payment_url": payment_url,
    }

async def cancel_match(db: AsyncSession, match_id: int):
    match = await db.get(Match, match_id)
    if not match:
        raise ValueError("Match not found")

    # снимаем все брони
    await db.execute(
        delete(Booking).where(Booking.match_id == match_id)
    )
    match.status = "cancelled"
    await db.commit()

async def delete_booking(db: AsyncSession, booking_id: int):
    booking = await db.get(Booking, booking_id)
    if not booking:
        raise ValueError("Booking not found")

    match_id = booking.match_id
    await db.delete(booking)
    await db.commit()
    return match_id 