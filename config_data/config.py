import os
from dotenv import load_dotenv, find_dotenv

if not find_dotenv():
    exit('Переменные окружения не загружены, так как отсутствует файл .env')
else:
    load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
DEFAULT_COMMANDS = (
    ('start', "Запустить бота"),
    ('help', "Вывести справку"),
    ('new_game', "Создать игру"),
    ("join_game", "Присоединиться к игре"),
    ("start_game", "Запустить игру"),
    ("my_hand", "Мои карты"),
)
ADMIN_COMMANDS = (
    ("admin_panel", "Админка"),
    ("admin_games", "Изменить игры"),
    ("add_faction", "Создать фракцию"),
    ("manage_factions", "Управление фракциями")
)
ADMIN_ID = os.getenv('ADMIN_ID')
ALLOWED_USERS = [int(ADMIN_ID)]
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATABASE_PATH = os.path.join(BASE_DIR, "database", "database.db")
DATABASE_URL = f"sqlite+aiosqlite:///{DATABASE_PATH}"
