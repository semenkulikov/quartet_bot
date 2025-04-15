from aiogram import Router, types
from aiogram.filters import Command

from loader import dp
from config_data.config import DEFAULT_COMMANDS, ADMIN_COMMANDS, ADMIN_IDS

router = Router()

@router.message(Command('help'))
async def bot_help(message: types.Message):
    commands = [f"/{cmd} - {desc}" for cmd, desc in DEFAULT_COMMANDS]
    if int(message.from_user.id) in ADMIN_IDS:
        commands.extend([f"/{cmd} - {desc}" for cmd, desc in ADMIN_COMMANDS])
    await message.reply("Доступные команды:\n" + "\n".join(commands))
