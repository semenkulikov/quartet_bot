from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import json

async def active_games_markup() -> InlineKeyboardMarkup:
    """
    Формирует клавиатуру с кнопками для активных игр.
    Callback_data: "join_game:<game_id>"
    """
    from sqlalchemy.future import select
    from database.models_game import GameSession, GameStatus
    from database.engine import async_session

    builder = InlineKeyboardBuilder()
    async with async_session() as session:
        result = await session.execute(
            select(GameSession).where(GameSession.status.in_([GameStatus.waiting, GameStatus.in_progress]))
        )
        games = result.scalars().all()
    if not games:
        builder.button(text="Нет активных игр", callback_data="none")
    else:
        for game in games:
            builder.button(text=f"Игра #{game.id}", callback_data=f"join_game:{game.id}")
    builder.adjust(2)
    return builder.as_markup()

async def game_actions_markup(game_id: int) -> InlineKeyboardMarkup:
    """
    Формирует клавиатуру для админ-действий над игрой:
    Например, старт игры, отмена, вывод результатов.
    Callback_data: "action:<game_id>:<action>"
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="Запустить игру", callback_data=f"action:{game_id}:start")
    builder.button(text="Отменить игру", callback_data=f"action:{game_id}:cancel")
    builder.button(text="Результаты", callback_data=f"action:{game_id}:results")
    builder.adjust(1)
    return builder.as_markup()

async def hand_markup(player) -> InlineKeyboardMarkup:
    """
    Формирует клавиатуру с кнопками для карт игрока, сгруппированных по фракциям.
    Callback_data: "select_card:<card_id>"
    """
    builder = InlineKeyboardBuilder()
    hand = json.loads(player.hand)
    # Здесь можно запросить подробную информацию о картах, используя card_id
    # Допустим, для примера просто выводим card_id
    for card_id in hand:
        builder.button(text=f"Карта {card_id}", callback_data=f"select_card:{card_id}")
    builder.adjust(3)
    return builder.as_markup()
