from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_game_keyboard() -> ReplyKeyboardMarkup:
    """Основная клавиатура игры"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Создать игру"),
                KeyboardButton(text="Присоединиться к игре")
            ],
            [
                KeyboardButton(text="Мои карты"),
                KeyboardButton(text="Правила игры")
            ]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_admin_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура админ-панели"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Управление фракциями"),
                KeyboardButton(text="Управление играми")
            ],
            [
                KeyboardButton(text="Назад")
            ]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_faction_management_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура управления фракциями"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Создать фракцию"),
                KeyboardButton(text="Удалить фракцию")
            ],
            [
                KeyboardButton(text="Список фракций"),
                KeyboardButton(text="Назад")
            ]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_game_management_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура управления играми"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Список игр"),
                KeyboardButton(text="Завершить игру")
            ],
            [
                KeyboardButton(text="Назад")
            ]
        ],
        resize_keyboard=True
    )
    return keyboard 