from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database.db import get_active_games, get_user, get_game
from game_logic.game_session import GameSession
import logging

from keyboards.inline.inline_keyboards import get_cards_list_keyboard, get_players_list_keyboard

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.text == "Правила игры")
async def show_rules(message: Message):
    """Показать правила игры"""
    rules = (
        "Правила игры Квартет:\n\n"
        "1. В игре используется колода из 48 карточек, разбитых на 12 квартетов по 4 карты.\n"
        "2. Каждый квартет объединен общей темой (фракцией).\n"
        "3. В начале игры все карты раздаются игрокам поровну.\n"
        "4. Первый ход делает игрок, получивший последнюю карту при раздаче.\n"
        "5. Игрок может запросить карту у другого игрока только из квартета, часть которого уже есть у него.\n"
        "6. Если запрошенная карта есть у игрока, он обязан её отдать.\n"
        "7. При успешном запросе игрок делает следующий ход.\n"
        "8. При неудачном запросе ход переходит к тому, у кого спрашивали.\n"
        "9. Собранный квартет объявляется и откладывается.\n"
        "10. Игрок, собравший больше всего квартетов, побеждает.\n"
        "11. Игрок выбывает из игры, если у него закончились карты."
    )
    await message.answer(rules)

@router.message(F.text == "Сделать ход")
async def make_move(message: Message, state: FSMContext):
    """Начать ход"""
    user = await get_user(str(message.from_user.id))
    if not user:
        await message.answer("Вы не участвуете ни в одной игре")
        return
        
    # Находим активную игру игрока
    game_session = None
    for game in await get_active_games():
        session = GameSession(game.id)
        await session.load()
        for player in session.players:
            if player.user_id == user.id:
                game_session = session
                break
        if game_session:
            break
            
    if not game_session:
        await message.answer("Вы не участвуете ни в одной игре")
        return
        
    # Проверяем, чей сейчас ход
    if game_session.game.current_player_id != user.id:
        await message.answer("Сейчас не ваш ход")
        return
        
    # Получаем список других игроков
    other_players = [p for p in game_session.players if p.user_id != user.id]
    await message.answer(
        "Выберите игрока, у которого хотите запросить карту:",
        reply_markup=get_players_list_keyboard(other_players)
    )
    await state.set_state("requesting_player")

@router.callback_query(F.data.startswith("select_player_"))
async def select_player(callback: CallbackQuery, state: FSMContext):
    """Выбор игрока для запроса карты"""
    player_id = int(callback.data.split("_")[-1])
    await state.update_data(selected_player_id=player_id)
    
    # Получаем карты текущего игрока
    user = await get_user(str(callback.from_user.id))
    game_session = GameSession(callback.message.chat.id)
    await game_session.load()
    
    cards = await game_session.get_player_cards(user.id)
    await callback.message.answer(
        "Выберите карту, которую хотите запросить:",
        reply_markup=get_cards_list_keyboard(cards)
    )
    await state.set_state("requesting_card")
    await callback.answer()

@router.callback_query(F.data.startswith("select_card_"))
async def select_card(callback: CallbackQuery, state: FSMContext):
    """Выбор карты для запроса"""
    card_id = int(callback.data.split("_")[-1])
    data = await state.get_data()
    selected_player_id = data.get("selected_player_id")
    
    user = await get_user(str(callback.from_user.id))
    game_session = GameSession(callback.message.chat.id)
    await game_session.load()
    
    # Запрашиваем карту
    success = await game_session.request_card(
        from_player_id=user.id,
        to_player_id=selected_player_id,
        card_name=card_id
    )
    
    if success:
        await callback.message.answer("Карта получена успешно!")
        # Проверяем, не собран ли квартет
        faction = await game_session.check_quartet(user.id)
        if faction:
            await callback.message.answer(f"Поздравляем! Вы собрали квартет '{faction.name}'!")
    else:
        await callback.message.answer("У этого игрока нет такой карты. Ход переходит к нему.")
    
    await state.clear()
    await callback.answer() 