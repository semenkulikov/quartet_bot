from aiogram import types
from aiogram.filters import Command
from aiogram.types import CallbackQuery

from keyboards.inline.game_menu import active_games_markup
from loader import dp, bot, app_logger
from game_logic.game_session import GameManager

game_manager = GameManager()

@dp.message(Command('new_game'))
async def new_game(message: types.Message):
    game = await game_manager.create_game()
    app_logger.info(f"Новая игра создана. ID: {game.id}, создатель: {message.from_user.full_name}")
    await message.answer(f"Создана новая игра с ID: {game.id}. Чтобы присоединиться, введите команду /join_game {game.id}")


@dp.message(Command('join_game'))
async def join_game(message: types.Message):
    """
    Отправляет пользователю inline-клавиатуру со списком активных игр.
    """
    markup = await active_games_markup()
    await message.answer("Выберите игру, к которой хотите присоединиться:", reply_markup=markup)


@dp.callback_query(lambda c: c.data and c.data.startswith("join_game"))
async def join_game_callback(call: CallbackQuery):
    """
    Обрабатывает выбор игры из inline-клавиатуры.
    Формат callback_data: "join_game:<game_id>"
    """
    game_id_str = call.data.split(":")[1]
    try:
        game_id = int(game_id_str)
    except ValueError:
        await call.answer("Некорректный ID игры.")
        return

    # Присоединение к игре через GameManager
    player = await game_manager.join_game(game_id, str(call.from_user.id))
    if player:
        await call.message.edit_text(f"Вы успешно присоединились к игре #{game_id}!")
        app_logger.info(f"Пользователь @{call.from_user.username} присоединился к игре #{game_id}")
    else:
        await call.answer("Не удалось присоединиться к игре. Возможно, игра уже началась.", show_alert=True)
        app_logger.info(f"Попытка присоединения пользователя @{call.from_user.username} к игре #{game_id} не удалась")

