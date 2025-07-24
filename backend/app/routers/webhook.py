from fastapi import APIRouter, BackgroundTasks, status
from ..core.database import AsyncSessionLocal
from ..models import Booking
from datetime import datetime

router = APIRouter(prefix="/payments", tags=["payments"])

@router.post("/payments/webhook", status_code=status.HTTP_204_NO_CONTENT)
async def yk_webhook(payload: dict, bg: BackgroundTasks):
    if payload.get("event") != "payment.succeeded":
        return
    booking_id = int(payload["object"]["metadata"]["booking_id"])
    bg.add_task(mark_paid, booking_id)

async def mark_paid(booking_id: int):
    async with AsyncSessionLocal() as db:
        b = await db.get(Booking, booking_id)
        if b and b.paid_at is None:
            b.paid_at = datetime.utcnow()
            await db.commit()
