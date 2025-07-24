from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlmodel import select
from .core.database import AsyncSessionLocal      
from .models import Booking, Match
from .payments import yk_create_payment
from sqlalchemy import select, func
from aiogram.client.default import DefaultBotProperties
from bot.notifier import notify
from bot.config import BOT_TOKEN
from aiogram import Bot

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))



async def expire_and_promote():
    now = datetime.utcnow()

    async with AsyncSessionLocal() as db:
        # 1. удаляем/отменяем просроченные reserve
        stmt = select(Booking).where(
            Booking.state == "reserve",
            Booking.expires_at < now,
        )
        for booking in (await db.scalars(stmt)).all():
            await db.delete(booking)

        # 2. для каждого матча ищем свободные места
        sub = select(
            Booking.match_id,
            Booking.state,
        ).where(Booking.state == "main").subquery()

        # capacity нужно получить из Match
        matches = (await db.execute(select(Match))).scalars().all()
        for match in matches:
            main_count = await db.scalar(
                select(func.count())
                .select_from(Booking)
                .where(
                    Booking.match_id == match.id,
                    Booking.state == "main",
                    Booking.paid_at.is_not(None),
                )
            )
            if main_count >= match.capacity:
                continue

            # есть свободные места → поднимаем первый reserve
            reserve_stmt = (
                select(Booking)
                .where(
                    Booking.match_id == match.id,
                    Booking.state == "reserve",
                )
                .order_by(Booking.id)
                .limit(1)
            )
            reserve = (await db.scalars(reserve_stmt)).first()
            if reserve:
                reserve.state = "main"
                reserve.expires_at = None
                # создаём платёж
                url, pay_id = yk_create_payment(match.price, reserve.id)
                reserve.payment_id = pay_id
                # здесь можно отправить уведомление пользователю через бот
                await notify(
                    bot,
                    reserve.user_id,
                    f"🎉 Ваше место в резерве подтверждено!\n"
                    f"Матч #{match.id} • оплатите, чтобы закрепить бронь."
                )

        await db.commit()


def start_scheduler():
    sched = AsyncIOScheduler(timezone="UTC")
    sched.add_job(expire_and_promote, "interval", minutes=1)
    sched.start()
