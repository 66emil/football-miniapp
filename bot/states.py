from aiogram.fsm.state import StatesGroup, State

class CreateMatch(StatesGroup):
    venue     = State()
    starts_at = State()
    duration  = State()
    price     = State()
    capacity  = State()
