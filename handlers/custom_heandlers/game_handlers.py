from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db import (create_game, 
                         create_user, 
                         get_active_games, 
                         get_game, 
                         get_players_by_game_query, 
                         get_waiting_games, 
                         join_game, 
                         get_user, 
                         get_game_by_user_id)
from game_logic.game_session import GameSession
from keyboards.reply.handlers_reply import get_game_keyboard
from keyboards.inline.inline_keyboards import get_games_list_keyboard
import logging

from keyboards.reply.handlers_reply import get_admin_keyboard

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user = await get_user(str(message.from_user.id))
    if not user:
        # Создаем нового пользователя
        user = await create_user(
            user_id=str(message.from_user.id),
            full_name=message.from_user.full_name,
            username=message.from_user.username
        )
    
    await message.answer(
        "Добро пожаловать в игру Квартет!\n"
        "Выберите действие:",
        reply_markup=get_game_keyboard()
    )

@router.message(F.text == "Создать игру")
async def create_new_game(message: Message):
    """Создание новой игры"""
    game = await create_game()
    await message.answer(
        f"Создана новая игра #{game.id}\n"
        "Ожидаем игроков...",
        reply_markup=get_game_keyboard()
    )
    logger.info(f"Создана новая игра с ID: {game.id}")

@router.message(F.text == "Присоединиться к игре")
async def join_existing_game(message: Message):
    """Присоединение к существующей игре"""
    games = await get_waiting_games()
    if not games:
        await message.answer(
            "Нет доступных игр. Создайте новую игру!",
            reply_markup=get_game_keyboard()
        )
        return
        
    await message.answer(
        "Выберите игру для присоединения:",
        reply_markup=await get_games_list_keyboard(games)
    )

@router.callback_query(F.data.startswith("join_game_"))
async def process_join_game(callback: CallbackQuery):
    """Обработка выбора игры для присоединения"""
    game_id = int(callback.data.split("_")[-1])
    user = await get_user(str(callback.from_user.id))

    # Проверяем, присоединился ли уже пользователь к какой-либо игре
    existing_player = await get_game_by_user_id(user.id)
    if existing_player:
        await callback.message.answer(
            "Вы уже присоединились к другой игре!"
        )
        return
    
    if await join_game(game_id, user.id):
        # Удаление предыдущего сообщения
        await callback.message.delete()
        game = await get_game(game_id)
        players_count = len(await get_players_by_game_query(game_id))

        await callback.message.answer(
            f"Вы присоединились к игре #{game_id} ({players_count}/{game.max_players})",
            reply_markup=get_game_keyboard()
        )
        logger.info(f"Игрок {callback.from_user.id} присоединился к игре {game_id}")
    elif await join_game(game_id, user.id):
        await callback.message.answer(
            "Вы уже присоединились к этой игре!"
        )
    else:
        await callback.message.answer(
            "Не удалось присоединиться к игре. Возможно, она уже началась или заполнена.",
            reply_markup=get_game_keyboard()
        )
    
    await callback.answer()

@router.message(F.text == "Мои карты")
async def show_my_cards(message: Message):
    """Показать карты игрока"""
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
        
    # Получаем карты игрока
    cards = await game_session.get_player_cards(user.id)
    if not cards:
        await message.answer("У вас нет карт")
        return
        
    # Группируем карты по фракциям
    factions = await game_session.get_player_factions(user.id)
    response = "Ваши карты:\n\n"
    for faction, faction_cards in factions.items():
        response += f"{faction.name}:\n"
        for card in faction_cards:
            response += f"- {card.name}\n"
        response += "\n"
        
    await message.answer(response)
