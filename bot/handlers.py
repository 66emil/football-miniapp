from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, func

from backend.app.core.database import AsyncSessionLocal
from backend.app import crud
from backend.app.models import Match, Booking, Venue
from backend.app.workers import expire_and_promote
from bot.keyboards.admin import main_menu, matches_menu, match_actions
from bot.config import ADMIN_IDS
from bot.states import CreateMatch
from bot.notifier import notify

router = Router()          # регистрируется в main.py


# ─────────────── /start ───────────────
@router.message(F.text == "/start")
async def cmd_start(m: Message):
    if m.from_user.id not in ADMIN_IDS:
        await m.answer("Доступ запрещён.")
        return
    await m.answer("Главное меню:", reply_markup=main_menu())


# ─────── «Список матчей» ───────
@router.message(F.text == "📋 Список матчей")
async def list_matches(m: Message):
    async with AsyncSessionLocal() as db:
        ids = (await db.scalars(select(Match.id).order_by(Match.starts_at))).all()

    if not ids:
        await m.answer("Матчей нет.")
        return

    await m.answer("Выберите матч:", reply_markup=matches_menu(ids))


# ─────── карточка матча ───────
@router.message(F.text.startswith("Матч #"))
async def match_card(m: Message, state: FSMContext):
    match_id = int(m.text.split("#")[1])

    async with AsyncSessionLocal() as db:
        mt: Match | None = await db.get(Match, match_id)
        if not mt:
            await m.answer("Матч не найден"); return

        main_cnt = await db.scalar(
            select(func.count()).select_from(Booking).where(
                Booking.match_id == match_id,
                Booking.state == "main"
            )
        )

    txt = (f"<b>Матч #{mt.id}</b>\n"
           f"Дата: {mt.starts_at:%d.%m %H:%M}\n"
           f"Цена: {mt.price}₽\n"
           f"Capacity: {main_cnt}/{mt.capacity}\n"
           f"Статус: {mt.status}")

    await state.update_data(curr_match=match_id)
    await m.answer(txt, reply_markup=match_actions())


# ─────── «Игроки» ───────
@router.message(F.text == "👥 Игроки")
async def players(m: Message, state: FSMContext):
    data = await state.get_data()
    match_id: int | None = data.get("curr_match")
    if not match_id:
        await m.answer("Сначала выберите матч."); return

    async with AsyncSessionLocal() as db:
        books = (await db.scalars(
            select(Booking).where(Booking.match_id == match_id).order_by(Booking.id)
        )).all()

    lines = [
        f"{'✅' if b.state=='main' else '🕒'} {b.user_id}  (#{b.id})"
        for b in books
    ] or ["Нет броней"]
    await m.answer("\n".join(lines))


# ─────── «❌ Отменить» ───────
@router.message(F.text == "❌ Отменить")
async def cancel_match(m: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    match_id: int | None = data.get("curr_match")
    if not match_id:
        await m.answer("Сначала выберите матч."); return

    # 1. достаём всех игроков -> уведомим
    async with AsyncSessionLocal() as db:
        bookings = (await db.scalars(
            select(Booking).where(Booking.match_id == match_id)
        )).all()
        await crud.cancel_match(db, match_id)

    for b in bookings:
        await notify(bot, b.user_id, f"Матч #{match_id} отменён :(")

    await m.answer(f"Матч #{match_id} отменён ✅", reply_markup=main_menu())
    await state.clear()


# ─────── «➕ Создать матч» (старт FSM) ───────
@router.message(F.text == "➕ Создать матч")
async def create_start(m: Message, state: FSMContext):
    await m.answer("Название площадки?")
    await state.set_state(CreateMatch.venue)


# ─────── 5 шагов FSM «Создать матч» ───────
@router.message(CreateMatch.venue)
async def fsm_venue(m: Message, state: FSMContext):
    await state.update_data(venue=m.text)
    await m.answer("Дата и время (ДД.MM HH:MM)?")
    await state.set_state(CreateMatch.starts_at)

@router.message(CreateMatch.starts_at)
async def fsm_starts(m: Message, state: FSMContext):
    try:
        dt = datetime.strptime(m.text, "%d.%m %H:%M")
    except ValueError:
        await m.answer("Неверный формат, введите ещё раз."); return
    await state.update_data(starts_at=dt)
    await m.answer("Длительность (мин)?")
    await state.set_state(CreateMatch.duration)

@router.message(CreateMatch.duration)
async def fsm_duration(m: Message, state: FSMContext):
    await state.update_data(duration=int(m.text))
    await m.answer("Цена (₽)?")
    await state.set_state(CreateMatch.price)

@router.message(CreateMatch.price)
async def fsm_price(m: Message, state: FSMContext):
    await state.update_data(price=int(m.text))
    await m.answer("Вместимость (capacity)?")
    await state.set_state(CreateMatch.capacity)

@router.message(CreateMatch.capacity)
async def fsm_capacity(m: Message, state: FSMContext):
    data = await state.update_data(capacity=int(m.text))

    async with AsyncSessionLocal() as db:
        venue = Venue(title=data["venue"], address="-")
        db.add(venue); await db.flush()

        match = Match(
            venue_id=venue.id,
            starts_at=data["starts_at"],
            duration_min=data["duration"],
            price=data["price"],
            capacity=data["capacity"],
        )
        db.add(match); await db.commit()

    await m.answer(f"✔ Матч #{match.id} создан!", reply_markup=main_menu())
    await state.clear()


# ─────── «↩️ Назад» ───────
@router.message(F.text == "↩️ Назад")
async def back_to_menu(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("Главное меню:", reply_markup=main_menu())
