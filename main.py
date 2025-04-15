import asyncio
from aiogram import Dispatcher
from loader import dp, bot, logger
from handlers.custom_heandlers import game_handlers, admin_handlers, game_process_handlers
from handlers.default_heandlers import start, help, echo
from database.init_db import init_db
import logging
from config_data.config import ADMIN_IDS

async def main():
    """Запуск бота"""
    try:
        # Инициализация базы данных
        await init_db()
        logger.info("База данных инициализирована")
        
        # Регистрация роутеров
        dp.include_router(start.router)
        dp.include_router(help.router)
        
        dp.include_router(game_handlers.router)
        dp.include_router(admin_handlers.router)
        dp.include_router(game_process_handlers.router)

        dp.include_router(echo.router)
        # Запуск бота
        
        me = await bot.get_me()
        logger.info(f"Бот @{me.username} запущен")
        for admin_id in ADMIN_IDS:
            await bot.send_message(admin_id, f"Бот @{me.username} запущен.")
            logger.info(f"Администратору {admin_id} отправлено сообщение о запуске бота")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
