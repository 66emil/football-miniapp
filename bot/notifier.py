from aiogram import Bot
from backend.app.core.config import settings            # BASE_URL пригодится

async def notify(bot: Bot, tg_id: int, text: str):
    try:
        await bot.send_message(tg_id, text)
    except Exception:
        # юзер заблокировал бота — игнорируем
        pass
