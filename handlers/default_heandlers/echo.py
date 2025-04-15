from aiogram import Router, types
from loader import dp

router = Router()

@router.message()
async def bot_echo(message: types.Message):
    await message.reply(
        "Введите любую команду из меню, чтобы я начал работать\n"
        "Либо выберите одну из кнопок, которые я вам прислал"
    )
