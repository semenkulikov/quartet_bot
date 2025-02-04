from config_data.config import ALLOWED_USERS, ADMIN_ID
from keyboards.inline.accounts import users_markup
from states.states import AdminPanel
from database.engine import async_session
from sqlalchemy.future import select
from database.models import User

from aiogram import types
from aiogram.filters import Command, StateFilter
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from loader import dp, app_logger
from keyboards.inline.game_menu import active_games_markup, game_actions_markup
from game_logic.game_session import GameManager

game_manager = GameManager()


@dp.message(Command('admin_panel'))
async def admin_panel(message: types.Message, state: FSMContext):
    if int(message.from_user.id) in ALLOWED_USERS:
        app_logger.info(f"Администратор @{message.from_user.username} вошел в админ панель.")
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
        app_logger.info(f"Администратор @{call.from_user.username} вышел из админ панели.")
    else:
        async with async_session() as session:
            result = await session.execute(select(User).where(User.id == int(call.data)))
            user_obj = result.scalars().first()
        if user_obj:
            text = f"Имя: {user_obj.full_name}\nТелеграм: @{user_obj.username}\n"
            await call.message.answer(text)
        else:
            await call.message.answer("Пользователь не найден")

@dp.message(Command('admin_games'))
async def admin_games_handler(message: types.Message, state: FSMContext):
    """
    Отправляет администратору список активных игр с inline-клавиатурой.
    """
    # Проверка прав (используйте ADMIN_ID из конфига)
    from config_data.config import ADMIN_ID
    if int(message.from_user.id) != int(ADMIN_ID):
        await message.answer("У вас недостаточно прав для доступа к админке.")
        return
    markup = await active_games_markup()
    await message.answer("Активные игры:", reply_markup=markup)
    await state.set_state("admin:games")

@dp.callback_query(lambda c: c.data and c.data.startswith("join_game"), StateFilter("admin:games"))
async def admin_join_game_callback(call: CallbackQuery, state: FSMContext):
    """
    Позволяет администратору выбрать игру для управления.
    """
    game_id_str = call.data.split(":")[1]
    try:
        game_id = int(game_id_str)
    except ValueError:
        await call.answer("Некорректный ID игры.", show_alert=True)
        return
    markup = await game_actions_markup(game_id)
    await call.message.edit_text(f"Выбрана игра #{game_id}. Доступные действия:", reply_markup=markup)
    await state.update_data(selected_game=game_id)
    await call.answer()

@dp.callback_query(lambda c: c.data and c.data.startswith("action"), StateFilter("admin:games"))
async def admin_game_action_callback(call: CallbackQuery, state: FSMContext):
    """
    Обрабатывает действия администратора над выбранной игрой.
    Формат callback_data: "action:<game_id>:<action>"
    """
    data_parts = call.data.split(":")
    game_id = int(data_parts[1])
    action = data_parts[2]
    if action == "start":
        game = await game_manager.start_game(game_id)
        if game:
            text = f"Игра #{game_id} запущена. Первый ход у {game.current_turn}."
        else:
            text = f"Не удалось запустить игру #{game_id}."
    elif action == "cancel":
        # Реализуйте логику отмены игры (например, обновите статус и уведомите игроков)
        text = f"Игра #{game_id} отменена."
    elif action == "results":
        results = await game_manager.finish_game(game_id)
        text = f"Результаты игры #{game_id}:\n{results}"
    else:
        text = "Неизвестное действие."
    await call.message.edit_text(text)
    await call.answer()