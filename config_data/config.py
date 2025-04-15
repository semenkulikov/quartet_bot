import os
from dotenv import find_dotenv, load_dotenv

if not find_dotenv():
    exit('Переменные окружения не загружены, так как отсутствует файл .env')
else:
    load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ID администраторов
ADMIN_IDS = [
    int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id
]

DEFAULT_COMMANDS = [
    ("start", "Начать игру"),
    ("help", "Помощь"),
]

ADMIN_COMMANDS = [
    ("admin_panel", "Админ-панель"),
]

# Настройки базы данных
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///database.db")

# Настройки логирования
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = "logs/bot.log"
LOG_MAX_BYTES = 1024 * 1024  # 1 MB
LOG_BACKUP_COUNT = 5
