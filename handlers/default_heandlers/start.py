from aiogram import Router, types
from database.db import create_group, create_user, get_group_by_group_id, get_user_by_user_id
from keyboards.reply.handlers_reply import get_game_keyboard
from loader import bot, dp, logger
from config_data.config import ADMIN_IDS, DEFAULT_COMMANDS, ADMIN_COMMANDS
from aiogram.filters import Command

router = Router()

@router.message(Command('start'))
async def bot_start(message: types.Message):
    if message.chat.type == 'private':
        user = await get_user_by_user_id(str(message.from_user.id))
        if user is None:
            await create_user(
                user_id=str(message.from_user.id),
                full_name=message.from_user.full_name,
                username=message.from_user.username,
                is_premium=getattr(message.from_user, 'is_premium', None),
                is_admin=int(message.from_user.id) in ADMIN_IDS
            )
        commands = [f"/{cmd} - {desc}" for cmd, desc in DEFAULT_COMMANDS]
        if int(message.from_user.id) in ADMIN_IDS:
            commands.extend([f"/{cmd} - {desc}" for cmd, desc in ADMIN_COMMANDS])
            await message.answer(
                f"Здравствуйте, {message.from_user.full_name}! Вы в списке администраторов бота. \n"
                f"Вам доступны следующие команды:\n" + "\n".join(commands),
                reply_markup=get_game_keyboard()
            )
        else:
            logger.info(f"Новый пользователь: {message.from_user.full_name} — {message.from_user.username}")
            await message.answer(
                f"Здравствуйте, {message.from_user.full_name}! Я — телеграм-бот. \n"
                f"Вам доступны следующие команды:\n" + "\n".join(commands),
                reply_markup=get_game_keyboard()
            )
    else:
        await message.answer(
            "Здравствуйте! Я — телеграм-бот, модератор каналов и групп. "
            "Чтобы получить больше информации, обратитесь к администратору или напишите мне в личку"
        )
        group = await get_group_by_group_id(str(message.chat.id))
        if group is None:
            await create_group(
                group_id=str(message.chat.id),
                title=message.chat.title,
                description=message.chat.description,
                bio=getattr(message.chat, 'bio', None),
                invite_link=getattr(message.chat, 'invite_link', None),
                location=getattr(message.chat, 'location', None),
                username=message.chat.username
            )
        # Также регистрируем пользователя, если его ещё нет
        user = await get_user_by_user_id(str(message.from_user.id))
        if user is None:
            await create_user(
                user_id=str(message.from_user.id),
                full_name=message.from_user.full_name,
                username=message.from_user.username,
                is_premium=getattr(message.from_user, 'is_premium', None),
                is_admin=int(message.from_user.id) in ADMIN_IDS,
            )
        logger.info(f"Новый пользователь: {message.from_user.full_name} — {message.from_user.username}")
