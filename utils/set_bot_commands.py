from aiogram.types import BotCommand
from config_data.config import DEFAULT_COMMANDS
from loader import bot

async def set_default_commands():
    """ Функция для установки команд по умолчанию в бота """
    commands = [BotCommand(command=cmd, description=desc) for cmd, desc in DEFAULT_COMMANDS]
    await bot.set_my_commands(commands)
