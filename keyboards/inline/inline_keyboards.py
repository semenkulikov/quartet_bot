from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.db import get_players_by_game_query
from database.models import Card, Game, Faction, GamePlayer, GameStatus
from typing import List


async def get_games_list_keyboard(games: list[Game]) -> InlineKeyboardMarkup:
    """Клавиатура со списком игр"""
    keyboard = []
    for game in games:
        # Получаем количество игроков в игре
        players_count = len(await get_players_by_game_query(game.id))
        if game.status == GameStatus.WAITING:
            keyboard.append([
                InlineKeyboardButton(
                    text=f"Игра #{game.id} ({players_count}/{game.max_players})",
                    callback_data=f"join_game_{game.id}"
                )   
            ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def get_games_list_keyboard_for_admin(games: List[Game]) -> InlineKeyboardMarkup:
    """Создание клавиатуры со списком игр для админа"""
    keyboard = []
    for game in games:
        if game.status == GameStatus.WAITING:
            # Получаем количество игроков в игре
            players_count = len(await get_players_by_game_query(game.id))
            keyboard.append([
                InlineKeyboardButton(
                    text=f"Игра #{game.id} ({players_count}/{game.max_players})",
                    callback_data=f"select_game_{game.id}"
                )
            ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_factions_list_keyboard(factions: list[Faction]) -> InlineKeyboardMarkup:
    """Клавиатура со списком фракций"""
    keyboard = []
    for faction in factions:
        keyboard.append([
            InlineKeyboardButton(
                text=faction.name,
                callback_data=f"select_faction_{faction.id}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def get_cards_list_keyboard(cards: list) -> InlineKeyboardMarkup:
    """Клавиатура со списком карт"""
    keyboard = []
    for card in cards:
        keyboard.append([
            InlineKeyboardButton(
                text=card.name,
                callback_data=f"select_card_{card.id}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def get_players_list_keyboard(players: list) -> InlineKeyboardMarkup:
    """Клавиатура со списком игроков"""
    keyboard = []
    for player in players:
        keyboard.append([
            InlineKeyboardButton(
                text=player.user.full_name,
                callback_data=f"select_player_{player.user_id}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


