# bot/keyboards/admin.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        resize_keyboard=True,       # компактная высота
        keyboard=[
            [KeyboardButton(text="➕ Создать матч")],
            [KeyboardButton(text="📋 Список матчей")],
        ]
    )

def matches_menu(match_ids: list[int]) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True,      # клавиатура исчезнет после выбора
        keyboard=[[KeyboardButton(text=f"Матч #{mid}")] for mid in match_ids],
    )

def match_actions() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True,
        keyboard=[
            [KeyboardButton(text="✏️ Изменить"),  KeyboardButton(text="❌ Отменить")],
            [KeyboardButton(text="👥 Игроки"),     KeyboardButton(text="↩️ Назад")],
        ]
    )
