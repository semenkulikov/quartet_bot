from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config_data.config import ADMIN_IDS
from database.db import get_all_users

async def users_markup() -> InlineKeyboardMarkup:
    """ Клавиатура для отображения юзеров в админ панели """
    builder = InlineKeyboardBuilder()
    users = await get_all_users()
    for user in users:
        # Добавляем кнопку только если пользователь не является администратором
        if int(user.user_id) not in ADMIN_IDS:
            builder.button(text=user.username, callback_data=str(user.id))
    # Добавляем кнопку "Выйти"
    builder.button(text="Выйти", callback_data="Выход")
    # Располагаем кнопки в 2 колонки
    builder.adjust(2)
    return builder.as_markup()
