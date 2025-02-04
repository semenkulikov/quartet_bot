import json
from aiogram import types
from aiogram.filters import Command
from aiogram.types import CallbackQuery

from config_data.config import ADMIN_ID
from loader import dp, app_logger
from game_logic.game_session import GameManager
from keyboards.inline.game_menu import active_games_markup, game_actions_markup, hand_markup, \
    admin_games_for_start_markup, admin_games_for_stop_markup
from sqlalchemy.future import select
from database.models_game import PlayerGame

game_manager = GameManager()


@dp.message(Command('new_game'))
async def new_game_handler(message: types.Message):
    """
    Создает новую игру и сообщает игроку ID.
    """
    game = await game_manager.create_game()
    await message.answer(f"Создана новая игра с ID: {game.id}. Расскажи друзьям, пусть присоединяются!")
    app_logger.info(f"Пользователь {message.from_user.full_name} создал новую игру с ID: {game.id}.")



@dp.message(Command('join_game'))
async def join_game_handler(message: types.Message):
    """
    Отправляет игроку inline-клавиатуру с активными играми для присоединения.
    """
    markup = await active_games_markup()
    await message.answer("Выберите игру для присоединения:", reply_markup=markup)


@dp.callback_query(lambda c: c.data and c.data.startswith("join_game"))
async def join_game_callback(call: CallbackQuery):
    """
    Обрабатывает нажатие на кнопку выбора игры.
    Формат callback_data: "join_game:<game_id>"
    """
    game_id_str = call.data.split(":")[1]
    try:
        game_id = int(game_id_str)
    except ValueError:
        await call.answer("Некорректный ID игры.", show_alert=True)
        return
    player = await game_manager.join_game(game_id, str(call.from_user.id))
    if player:
        await call.message.edit_text(f"Вы успешно присоединились к игре #{game_id}!")
        app_logger.info(f"Пользователь {call.from_user.full_name} присоединился к игре #{game_id}")
    else:
        await call.answer("Не удалось присоединиться. Возможно, вы уже в игре или игра началась.", show_alert=True)
        app_logger.warning(f"Пользователю {call.from_user.full_name} не удалось присоединиться к игре #{game_id}")


@dp.message(Command('start_game'))
async def admin_start_game_handler(message: types.Message):
    """
    Админская команда для запуска игры.
    Выводит список игр, созданных администратором, которые ждут старта.
    """

    if str(message.from_user.id) != ADMIN_ID:
        await message.answer("У вас недостаточно прав для запуска игр.")
        return
    markup = await admin_games_for_start_markup()
    await message.answer("Выберите игру для старта:", reply_markup=markup)

@dp.callback_query(lambda c: c.data and c.data.startswith("start_game"))
async def start_game_callback(call: CallbackQuery):
    """
    Обрабатывает выбор игры администратором для запуска.
    Callback_data: "start_game:<game_id>"
    """
    game_id_str = call.data.split(":")[1]
    try:
        game_id = int(game_id_str)
    except ValueError:
        await call.answer("Некорректный ID игры.", show_alert=True)
        return
    game = await game_manager.start_game(game_id)
    if game:
        await call.message.edit_text(f"Игра #{game_id} запущена!\nПервый ход у {game.current_turn}.")
        app_logger.info(f"Пользователь {call.from_user.full_name} запустил игру #{game_id}")
    else:
        await call.message.edit_text("Не удалось запустить игру. Проверьте статус игры.")
    await call.answer()


@dp.message(Command('my_hand'))
async def my_hand_handler(message: types.Message):
    """
    Показывает игроку его карты с возможностью выбора фракции для запроса.
    Использует inline-клавиатуру, сформированную по данным руки.
    """
    app_logger.info(f"Пользователь {message.from_user.full_name} вызвал команду /my_hand")
    async with dp.storage.session() as session:
        # Получаем объект PlayerGame игрока из БД
        # Здесь можно реализовать запрос через GameManager или напрямую к базе данных
        # Для примера делаем упрощенно:
        result = await session.execute(select(PlayerGame).where(PlayerGame.user_id == str(message.from_user.id)))
        player = result.scalars().first()
        if not player:
            await message.answer("Вы не участвуете ни в одной игре.")
            return
        # Формируем клавиатуру на основе содержимого руки (например, разбиваем по фракциям)
        markup = await hand_markup(player)
        await message.answer("Ваши карты:", reply_markup=markup)


@dp.message(Command('stop_game'))
async def admin_stop_game_handler(message: types.Message):
    """
    Админская команда для остановки игры.
    Выводит список активных игр для выбора.
    """
    if str(message.from_user.id) != ADMIN_ID:
        await message.answer("У вас недостаточно прав для остановки игр.")
        return
    markup = await admin_games_for_stop_markup()
    await message.answer("Выберите игру для остановки:", reply_markup=markup)


@dp.callback_query(lambda c: c.data and c.data.startswith("stop_game"))
async def stop_game_callback(call: CallbackQuery):
    """
    Обрабатывает выбор игры для остановки.
    Callback_data: "stop_game:<game_id>"
    """
    game_id_str = call.data.split(":")[1]
    try:
        game_id = int(game_id_str)
    except ValueError:
        await call.answer("Некорректный ID игры.", show_alert=True)
        return
    results = await game_manager.finish_game(game_id)
    if results:
        await call.message.edit_text(f"Игра #{game_id} остановлена.\nРезультаты:\n{results}")
    else:
        await call.message.edit_text("Ошибка при остановке игры.")
    await call.answer()
