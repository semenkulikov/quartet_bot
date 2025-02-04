# keyboards/inline/game_menu.py
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.models_game import GameSession
from sqlalchemy.future import select
from database.engine import async_session


async def active_games_markup() -> InlineKeyboardMarkup:
    """
    Формирует клавиатуру с кнопками для каждой активной игры (например, статус waiting или in_progress).
    При нажатии на кнопку будет передаваться callback_data в формате "join_game:<game_id>".
    """
    builder = InlineKeyboardBuilder()

    async with async_session() as session:
        result = await session.execute(
            select(GameSession).where(GameSession.status.in_(["waiting", "in_progress"]))
        )
        games = result.scalars().all()

    if not games:
        # Если игр нет, можно добавить кнопку с уведомлением
        builder.button(text="Нет активных игр", callback_data="none")
    else:
        for game in games:
            # Выводим ID игры и, возможно, количество участников
            button_text = f"Игра #{game.id}"
            builder.button(text=button_text, callback_data=f"join_game:{game.id}")
    builder.adjust(2)
    return builder.as_markup()
