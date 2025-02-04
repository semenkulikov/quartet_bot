from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.future import select
from loader import dp, app_logger
from states.faction_states import FactionStates
from database.models_game import Faction, Card
from database.engine import async_session
from aiogram.types import CallbackQuery
from keyboards.inline.faction_menu import factions_markup
from aiogram.filters import Command


@dp.message(Command('add_faction'))
async def add_faction_start(message: types.Message, state: FSMContext):
    """
    Начало процесса создания новой фракции.
    Админ вводит название фракции.
    """
    from config_data.config import ADMIN_ID
    if str(message.from_user.id) != ADMIN_ID:
        await message.answer("У вас недостаточно прав.")
        return
    await message.answer("Введите название новой фракции:")
    await state.set_state(FactionStates.waiting_for_faction_name)


@dp.message(FactionStates.waiting_for_faction_name)
async def process_faction_name(message: types.Message, state: FSMContext):
    """
    Сохраняем название фракции и просим ввести название первой карты.
    """
    faction_name = message.text.strip()
    await state.update_data(faction_name=faction_name)
    await message.answer("Введите название карты №1:")
    await state.set_state(FactionStates.waiting_for_card_1)


@dp.message(FactionStates.waiting_for_card_1)
async def process_card_1(message: types.Message, state: FSMContext):
    """
    Сохраняем первую карту и просим ввести вторую.
    """
    card1 = message.text.strip()
    await state.update_data(card1=card1)
    await message.answer("Введите название карты №2:")
    await state.set_state(FactionStates.waiting_for_card_2)


@dp.message(FactionStates.waiting_for_card_2)
async def process_card_2(message: types.Message, state: FSMContext):
    """
    Сохраняем вторую карту и просим ввести третью.
    """
    card2 = message.text.strip()
    await state.update_data(card2=card2)
    await message.answer("Введите название карты №3:")
    await state.set_state(FactionStates.waiting_for_card_3)


@dp.message(FactionStates.waiting_for_card_3)
async def process_card_3(message: types.Message, state: FSMContext):
    """
    Сохраняем третью карту и просим ввести четвёртую.
    """
    card3 = message.text.strip()
    await state.update_data(card3=card3)
    await message.answer("Введите название карты №4:")
    await state.set_state(FactionStates.waiting_for_card_4)


@dp.message(FactionStates.waiting_for_card_4)
async def process_card_4(message: types.Message, state: FSMContext):
    """
    Сохраняем четвёртую карту и создаём фракцию со всеми четырьмя картами.
    """
    card4 = message.text.strip()
    data = await state.get_data()
    faction_name = data.get("faction_name")
    card1 = data.get("card1")
    card2 = data.get("card2")
    card3 = data.get("card3")

    async with async_session() as session:
        # Создаем фракцию
        faction = Faction(name=faction_name)
        session.add(faction)
        await session.commit()  # чтобы получить faction.id
        # Создаем 4 карты для фракции
        cards = [
            Card(name=card1, faction_id=faction.id),
            Card(name=card2, faction_id=faction.id),
            Card(name=card3, faction_id=faction.id),
            Card(name=card4, faction_id=faction.id)
        ]
        session.add_all(cards)
        await session.commit()
    app_logger.info(f"Добавлена фракция '{faction_name}' с картами: {card1}, {card2}, {card3}, {card4}")
    await message.answer(f"Фракция '{faction_name}' успешно создана!")
    await state.clear()


@dp.message(Command('manage_factions'))
async def manage_factions_handler(message: types.Message):
    """
    Отправляет администратору список фракций для управления.
    """
    from config_data.config import ADMIN_ID
    if str(message.from_user.id) != ADMIN_ID:
        await message.answer("У вас недостаточно прав.")
        return
    markup = await factions_markup()
    await message.answer("Выберите фракцию для редактирования/удаления:", reply_markup=markup)

@dp.callback_query(lambda c: c.data and c.data.startswith("faction:"))
async def faction_choice_callback(call: CallbackQuery):
    """
    Обрабатывает выбор фракции и выводит действия для неё.
    Callback_data: "faction:<faction_id>"
    """
    faction_id = call.data.split(":")[1]
    builder = InlineKeyboardBuilder()
    builder.button(text="Редактировать", callback_data=f"edit_faction:{faction_id}")
    builder.button(text="Удалить", callback_data=f"delete_faction:{faction_id}")
    builder.adjust(2)
    await call.message.edit_text("Выберите действие для фракции:", reply_markup=builder.as_markup())
    await call.answer()

@dp.callback_query(lambda c: c.data and c.data.startswith("delete_faction:"))
async def delete_faction_callback(call: CallbackQuery):
    """
    Обрабатывает удаление фракции.
    """
    faction_id = call.data.split(":")[1]
    async with async_session() as session:
        result = await session.execute(select(Faction).where(Faction.id == faction_id))
        faction = result.scalars().first()
        if faction:
            await session.delete(faction)
            await session.commit()
            app_logger.info(f"Фракция {faction.name} (ID: {faction_id}) удалена.")
            await call.message.edit_text(f"Фракция {faction.name} удалена.")
        else:
            await call.message.edit_text("Фракция не найдена.")
    await call.answer()