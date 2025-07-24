import asyncio
from datetime import datetime, timedelta

from app.core.database import AsyncSessionLocal
from app.models import Venue, Match


async def seed():
    async with AsyncSessionLocal() as db:
        # 1. площадка
        venue = Venue(
            title="Спартак Манеж",
            address="Москва, ул. Полевой 3",
        )
        db.add(venue)
        await db.flush()                 # venue.id уже готов

        # 2. матч на завтра
        match = Match(
            venue_id=venue.id,
            starts_at=datetime.utcnow() + timedelta(days=1),
            duration_min=60,
            capacity=12,
            price=500,
        )
        db.add(match)
        await db.commit()
        await db.refresh(match)
        print("MATCH_ID =", match.id)


if __name__ == "__main__":
    asyncio.run(seed())
