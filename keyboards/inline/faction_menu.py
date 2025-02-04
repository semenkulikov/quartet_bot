# keyboards/inline/faction_menu.py
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.future import select
from database.models_game import Faction
from database.engine import async_session

async def factions_markup() -> InlineKeyboardMarkup:
    """
    Формирует клавиатуру с кнопками для всех фракций.
    Callback_data: "faction:<faction_id>"
    """
    builder = InlineKeyboardBuilder()
    async with async_session() as session:
        result = await session.execute(select(Faction))
        factions = result.scalars().all()
    if not factions:
        builder.button(text="Нет фракций", callback_data="none")
    else:
        for faction in factions:
            builder.button(text=faction.name, callback_data=f"faction:{faction.id}")
    builder.adjust(2)
    return builder.as_markup()
