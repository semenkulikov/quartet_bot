from aiogram.fsm.state import StatesGroup, State


class FactionStates(StatesGroup):
    waiting_for_faction_name = State()
    waiting_for_card_1 = State()
    waiting_for_card_2 = State()
    waiting_for_card_3 = State()
    waiting_for_card_4 = State()
    # Можно добавить состояние для редактирования, если потребуется
