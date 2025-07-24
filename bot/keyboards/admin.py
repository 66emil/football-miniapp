from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Список матчей")],
            [KeyboardButton(text="➕ Создать матч")],
        ],
        resize_keyboard=True,
    )

def matches_menu(matches):
    # matches: List[Match] — список объектов или словарей
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=f"Матч #{m.id} {'❌' if getattr(m, 'status', '') == 'cancelled' else ''}")]
            for m in matches
        ] + [[KeyboardButton(text="↩️ Назад")]],
        resize_keyboard=True
    )

def match_actions():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👥 Игроки"), KeyboardButton(text="✏️ Изменить")],
            [KeyboardButton(text="❌ Отменить"), KeyboardButton(text="↩️ Назад")]
        ],
        resize_keyboard=True,
    )

def players_menu(bookings):
    # Для каждого игрока — отдельная кнопка
    buttons = [
        [KeyboardButton(text=f"🗑 {b.user_id} (#{b.id})")]
        for b in bookings
    ]
    buttons.append([KeyboardButton(text="↩️ Назад")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def edit_fields_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="price")],
            [KeyboardButton(text="date")],
            [KeyboardButton(text="capacity")],
            [KeyboardButton(text="↩️ Назад")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def back_only_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="↩️ Назад")]],
        resize_keyboard=True,
    )
