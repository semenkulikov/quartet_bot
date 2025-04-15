from sqlalchemy.ext.asyncio import create_async_engine
from .models import Base
import logging

logger = logging.getLogger(__name__)

async def init_db():
    """Инициализация базы данных"""
    try:
        # Создаем движок
        engine = create_async_engine(
            "sqlite+aiosqlite:///database/database.db"
        )
        
        # Создаем все таблицы
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("База данных успешно инициализирована")
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        raise 