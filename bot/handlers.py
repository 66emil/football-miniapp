# bot/handlers.py
from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, func
from backend.app.core.database import AsyncSessionLocal
from backend.app.models import Match, Booking, Venue
from backend.app import crud
from bot.keyboards.admin import main_menu, matches_menu, match_actions, edit_fields_kb, players_menu
from bot.notifier import notify
from bot.config import ADMIN_IDS
from bot.states import CreateMatch, EditMatch

router = Router()

@router.message(F.text == "/start")
async def cmd_start(m: Message):
    if m.from_user.id not in ADMIN_IDS:
        await m.answer("Доступ запрещён."); return
    await m.answer("Главное меню:", reply_markup=main_menu())

@router.message(F.text == "📋 Список матчей")
async def list_matches(m: Message):
    async with AsyncSessionLocal() as db:
        matches = (await db.scalars(select(Match).order_by(Match.starts_at))).all()
    if not matches:
        await m.answer("Матчей нет."); return
    await m.answer("Выберите матч:", reply_markup=matches_menu(matches))



@router.message(F.text == "➕ Создать матч")
async def create_match_start(m: Message, state: FSMContext):
    await m.answer("Название площадки?")
    await state.set_state(CreateMatch.venue)

@router.message(CreateMatch.venue)
async def fsm_venue(m: Message, state: FSMContext):
    await state.update_data(venue=m.text)
    await m.answer("Дата и время (ДД.MM HH:MM)?")
    await state.set_state(CreateMatch.starts_at)

@router.message(CreateMatch.starts_at)
async def fsm_starts_at(m: Message, state: FSMContext):
    try:
        dt = datetime.strptime(m.text, "%d.%m %H:%M")
    except Exception:
        await m.answer("Неверный формат. Пример: 26.07 18:00"); return
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


@router.message(F.text.startswith("Матч #"))
async def match_card(m: Message, state: FSMContext):
    import re
    match = re.search(r"#(\d+)", m.text)
    if not match:
        await m.answer("Не могу определить номер матча."); return
    match_id = int(match.group(1))
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

    if mt.status == "cancelled":
        from bot.keyboards.admin import back_only_kb
        await m.answer(txt, reply_markup=back_only_kb())
        return
    
    await m.answer(txt, reply_markup=match_actions())


@router.message(F.text == "👥 Игроки")
async def players(m: Message, state: FSMContext):
    data = await state.get_data()
    match_id = data.get("curr_match")
    if not match_id:
        await m.answer("Сначала выберите матч."); return
    async with AsyncSessionLocal() as db:
        bookings = (await db.scalars(select(Booking).where(Booking.match_id == match_id))).all()
    lines = [f"{'✅' if b.state == 'main' else '🕒'} {b.user_id} (#{b.id})" for b in bookings]
    await m.answer(
        "\n".join(lines) or "Нет игроков",
        reply_markup=players_menu(bookings)   # ← тут!
    )


@router.message(F.text == "❌ Отменить")
async def cancel_match(m: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    match_id: int | None = data.get("curr_match")
    if not match_id:
        await m.answer("Сначала выберите матч."); return
    async with AsyncSessionLocal() as db:
        bookings = (await db.scalars(select(Booking).where(Booking.match_id == match_id))).all()
        await crud.cancel_match(db, match_id)
    for b in bookings:
        await notify(bot, b.user_id, f"Матч #{match_id} отменён :(")
    await m.answer(f"Матч #{match_id} отменён ✅", reply_markup=main_menu())
    await state.clear()

@router.message(F.text == "✏️ Изменить")
async def edit_choose_field(m: Message, state: FSMContext):
    await m.answer("Что изменить?", reply_markup=edit_fields_kb())
    await state.set_state(EditMatch.field)

@router.message(EditMatch.field)
async def edit_field(m: Message, state: FSMContext):
    field = m.text.lower().strip()
    if field not in {"price", "date", "capacity"}:
        await m.answer("Только price, date, capacity"); return
    await state.update_data(field=field)
    await m.answer("Новое значение:")
    await state.set_state(EditMatch.value)

@router.message(EditMatch.value)
async def edit_value(m: Message, state: FSMContext):
    data = await state.get_data()
    field = data["field"]
    value = m.text.strip()
    match_id = data.get("curr_match")
    payload = {}
    try:
        if field == "price":
            payload["price"] = int(value)
        elif field == "capacity":
            payload["capacity"] = int(value)
        else:
            payload["starts_at"] = datetime.strptime(value, "%d.%m %H:%M").isoformat()
    except Exception:
        await m.answer("Ошибка ввода."); await state.clear(); return

    # PATCH на backend
    import aiohttp
    async with aiohttp.ClientSession() as s:
        await s.patch(f"http://127.0.0.1:8000/matches/{match_id}", json=payload)
    await m.answer("✅ Обновлено", reply_markup=main_menu())
    await state.clear()

@router.message(F.text.startswith("🗑"))
async def delete_player(m: Message, state: FSMContext):
    # user_id и booking_id достаём из текста
    import re
    match = re.search(r'#(\d+)', m.text)
    if not match:
        await m.answer("Некорректный формат."); return
    booking_id = int(match.group(1))
    async with AsyncSessionLocal() as db:
        await db.delete(await db.get(Booking, booking_id)); await db.commit()
    await m.answer("Удалено")

@router.message(F.text == "↩️ Назад")
async def back_to_menu(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("Главное меню:", reply_markup=main_menu())