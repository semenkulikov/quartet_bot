from aiogram.fsm.state import StatesGroup, State


class AdminStates(StatesGroup):
    """ Состояния для админ хендлеров """
    managing_factions = State()
    managing_games = State()
    creating_faction = State()
    adding_cards = State()
    deleting_faction = State()
    viewing_faction = State()
    viewing_game = State()
    ending_game = State()

class AdminPanel(StatesGroup):
    """ FSM states for admin panel """
    get_users = State()


class GameStates(StatesGroup):
    """ States for game """
    waiting_for_players = State()
    in_game = State()
    requesting_card = State()
