import json
from aiogram import types
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from loader import dp, app_logger
from game_logic.game_session import GameManager
from keyboards.inline.game_menu import active_games_markup, game_actions_markup, hand_markup

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
async def start_game_handler(message: types.Message):
    """
    Запускает игру, если игрок является создателем или администратором.
    """
    try:
        # Ожидаем формат команды: /start_game <game_id>
        game_id = int(message.get_args())
    except (ValueError, TypeError):
        await message.answer("Укажите корректный ID игры. Пример: /start_game 1")
        return

    game = await game_manager.start_game(game_id)
    if game:
        await message.answer(f"Игра #{game_id} началась!\nХод первого игрока: {game.current_turn}")
        app_logger.info(f"Пользователь {message.from_user.full_name} запустил игру #{game_id}")
    else:
        await message.answer("Не удалось запустить игру. Проверьте ID или статус игры.")


@dp.message(Command('my_hand'))
async def my_hand_handler(message: types.Message):
    """
    Показывает игроку его карты с возможностью выбора фракции для запроса.
    Использует inline-клавиатуру, сформированную по данным руки.
    """
    async with dp.storage.session() as session:
        # Получаем объект PlayerGame игрока из БД
        # Здесь можно реализовать запрос через GameManager или напрямую к базе данных
        # Для примера делаем упрощенно:
        from sqlalchemy.future import select
        from database.models_game import PlayerGame
        result = await session.execute(select(PlayerGame).where(PlayerGame.user_id == str(message.from_user.id)))
        player = result.scalars().first()
        if not player:
            await message.answer("Вы не участвуете ни в одной игре.")
            return
        # Формируем клавиатуру на основе содержимого руки (например, разбиваем по фракциям)
        markup = await hand_markup(player)
        await message.answer("Ваши карты:", reply_markup=markup)
