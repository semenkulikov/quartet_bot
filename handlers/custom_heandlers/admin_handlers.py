from aiogram.filters import Command, StateFilter

from aiogram import types
from aiogram.fsm.context import FSMContext
from keyboards.inline.inline_keyboards import get_factions_list_keyboard, get_games_list_keyboard_for_admin
from keyboards.reply.handlers_reply import get_admin_keyboard, get_faction_management_keyboard, get_game_management_keyboard
from loader import dp
from config_data.config import ADMIN_IDS
from keyboards.inline.accounts import users_markup
from states.states import AdminPanel, AdminStates
from database.db import async_session, end_game, get_cards_by_faction, get_cards_by_game_query, get_current_player, get_factions, get_game, get_players_by_game_query
from sqlalchemy import select
from database.models import Card, Faction, User
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from database.db import (
    create_faction, add_card_to_faction, get_faction,
    delete_faction, get_active_games
)
import logging

logger = logging.getLogger(__name__)
router = Router()


@dp.message(Command('admin_panel'))
async def admin_panel(message: types.Message, state: FSMContext):
    if int(message.from_user.id) in ADMIN_IDS:
        logger.info(f"Администратор @{message.from_user.username} вошел в админ панель.")
        await message.answer("Вам доступна клавиатура админ-панели", reply_markup=get_admin_keyboard())
        markup = await users_markup()
        await message.answer("Все пользователи базы данных:", reply_markup=markup)
        await state.set_state(AdminPanel.get_users)
    else:
        await message.answer("У вас недостаточно прав")

@dp.callback_query(StateFilter(AdminPanel.get_users))
async def get_user(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    if call.data == "Выход":
        await call.message.answer("Вы успешно вышли из админ панели.")
        await state.clear()
        logger.info(f"Администратор @{call.from_user.username} вышел из админ панели.")
    else:
        async with async_session() as session:
            result = await session.execute(select(User).where(User.id == int(call.data)))
            user_obj = result.scalars().first()
        if user_obj:
            text = f"Имя: {user_obj.full_name}\nТелеграм: @{user_obj.username}\n"
            await call.message.answer(text)
        else:
            await call.message.answer("Пользователь не найден")

@router.message(F.text == "Управление фракциями")
async def manage_factions(message: Message, state: FSMContext):
    """Управление фракциями"""
    await state.set_state(AdminStates.managing_factions)
    await message.answer(
        "Управление фракциями:",
        reply_markup=get_faction_management_keyboard()
    )

@router.message(F.text == "Управление играми")
async def manage_games(message: Message, state: FSMContext):
    """Управление играми"""
    await state.set_state(AdminStates.managing_games)
    await message.answer(
        "Управление играми:",
        reply_markup=get_game_management_keyboard()
    )

@router.message(F.text == "Список фракций")
async def list_factions(message: Message, state: FSMContext):
    """Список фракций"""
    factions = await get_factions()
    if not factions:
        await message.answer("Нет доступных фракций")
        await state.set_state(AdminStates.managing_factions)
        return
    
    await message.answer(
        "Список фракций:",
        reply_markup=get_factions_list_keyboard(factions)
    )
    await state.set_state(AdminStates.viewing_faction)

@router.callback_query(F.data.startswith("select_faction_"), AdminStates.viewing_faction)
async def process_select_faction(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора фракции"""
    await callback.answer()
    faction_id = int(callback.data.split("_")[-1])
    # Выдача информации о фракции: название, описание, карты
    faction = await get_faction(faction_id)
    cards = await get_cards_by_faction(faction_id)
    
    # Преобразуем карты в список названий
    card_names = [card.name for card in cards]
    
    await callback.message.answer(
        f"Название: {faction.name}\n"
        f"Описание: {faction.description}\n"
        f"Карты: {', '.join(card_names)}"
    )
    await state.set_state(AdminStates.managing_factions)


@router.message(F.text == "Создать фракцию", AdminStates.managing_factions)
async def create_faction_handler(message: Message, state: FSMContext):
    """Создание новой фракции"""
    await state.set_state(AdminStates.creating_faction)
    await message.answer(
        "Введите название фракции и описание (опционально - через тире):",
        reply_markup=None
    )

@router.message(AdminStates.creating_faction)
async def process_faction_name(message: Message, state: FSMContext):
    """Обработка названия фракции"""
    faction_name = message.text
    if "-" in faction_name:
        faction_name, faction_description = faction_name.split("-")
    else:
        faction_description = None  
    
    # Обработка уникального имени фракции
    async with async_session() as session:
        result = await session.execute(
            select(Faction).where(Faction.name == faction_name)
        )
        existing_faction = result.scalar_one_or_none()  
        if existing_faction:
            await message.answer("Фракция с таким названием уже существует")
            return
        
    faction = await create_faction(faction_name, faction_description)
    await state.update_data(faction_id=faction.id)
    await state.set_state(AdminStates.adding_cards)
    await message.answer(
        f"Фракция '{faction_name}' создана.\n"
        "Введите название первой карты:"
    )

@router.message(AdminStates.adding_cards)
async def process_card_name(message: Message, state: FSMContext):
    """Обработка названия карты"""
    data = await state.get_data()
    faction_id = data.get("faction_id")
    card_name = message.text
    
    cards_count = len(await get_cards_by_faction(faction_id))
    # Добавляем карту
    await add_card_to_faction(faction_id, card_name)

    # Получаем обновленное количество карт
    if cards_count >= 4:
        await state.set_state(AdminStates.managing_factions)
        await message.answer(
            "Фракция создана успешно!",
            reply_markup=get_faction_management_keyboard()
        )
    else:
        await message.answer(
            f"Карта '{card_name}' добавлена.\n"
            f"Введите название следующей карты ({cards_count}/4):"
        )

@router.message(F.text == "Удалить фракцию", AdminStates.managing_factions)
async def delete_faction_handler(message: Message, state: FSMContext):
    """Удаление фракции"""
    await state.set_state(AdminStates.deleting_faction)
    factions = await get_factions()
    await message.answer(
        "Выберите фракцию для удаления:",
        reply_markup=get_factions_list_keyboard(factions)
    )

@router.callback_query(F.data.startswith("select_faction_"), AdminStates.deleting_faction)
async def process_delete_faction(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора фракции для удаления"""
    faction_id = int(callback.data.split("_")[-1])
    if await delete_faction(faction_id):
        await callback.message.answer(
            "Фракция удалена успешно!",
            reply_markup=get_faction_management_keyboard()
        )
    else:
        await callback.message.answer(
            "Не удалось удалить фракцию",
            reply_markup=get_faction_management_keyboard()
        )
    await state.set_state(AdminStates.managing_factions)
    await callback.answer()

@router.message(F.text == "Завершить игру", AdminStates.managing_games)
async def end_game_handler(message: Message, state: FSMContext):
    """Завершение игры"""
    await state.set_state(AdminStates.ending_game)
    games = await get_active_games()
    if not games:
        await message.answer(
            "Нет активных игр",
            reply_markup=get_game_management_keyboard()
        )
        await state.set_state(AdminStates.managing_games)
        return
        
    await message.answer(
        "Выберите игру для завершения:",
        reply_markup=await get_games_list_keyboard_for_admin(games)
    )
    await state.set_state(AdminStates.ending_game)

@router.callback_query(F.data.startswith("select_game_"), AdminStates.ending_game)
async def end_game_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик завершения игры"""
    try:
        game_id = int(callback.data.split("_")[-1])
        result = await end_game(game_id)
        if result:
            await callback.answer("Игра успешно завершена!")
            # Обновляем сообщение с новым списком игр
            await callback.message.answer(
                "Админ-панель:",
                reply_markup=get_admin_keyboard()
            )
            await state.set_state(AdminStates.managing_games)
        else:
            await callback.answer("Не удалось завершить игру")
    except Exception as e:
        logger.error(f"Ошибка при завершении игры: {e}")
        await callback.answer("Произошла ошибка при завершении игры")

@router.message(F.text == "Список игр")
async def list_games(message: Message, state: FSMContext):
    """Список игр"""
    games = await get_active_games()
    if not games:
        await message.answer("Нет активных игр")
        return
        
    await message.answer(
        "Список игр:",
        reply_markup=await get_games_list_keyboard_for_admin(games)
    )   
    await state.set_state(AdminStates.viewing_game)

@router.callback_query(F.data.startswith("select_game_"), AdminStates.viewing_game)
async def process_select_game(callback: CallbackQuery, state: FSMContext):
    """ Хендлер для выдачи информации об игре """
    await callback.answer()
    # Получаем информацию об игре: id, количество игроков, статус, игроки и их очки, карты, кто ходит
    game_id = int(callback.data.split("_")[-1])
    game = await get_game(game_id)
    players = await get_players_by_game_query(game_id)
    cards = await get_cards_by_game_query(game_id)
    current_player = await get_current_player(game_id)

    await callback.message.answer(
        f"ID: {game.id}\n"
        f"Максимальное количество игроков: {game.max_players}\n"
        f"Статус: {game.status}\n"
        f"Игроки:\n{'\n'.join([f'{player.user.full_name} - {player.score}' for player in players])}\n"
        f"Карты: {', '.join([card.name for card in cards])}\n"
        f"Кто ходит: {current_player.user.full_name if current_player else 'Нет текущего игрока'}"
    )   
    await state.set_state(AdminStates.managing_games)

@router.message(F.text == "Назад")
async def go_back(message: Message, state: FSMContext):
    """Возврат в главное меню"""
    await message.answer(
        "Админ-панель:",
        reply_markup=get_admin_keyboard()
    )
    await state.set_state(AdminStates.managing_games)
