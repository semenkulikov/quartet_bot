from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, selectinload
from .models import Base, Group, User, Game, GamePlayer, Faction, Card, GameCard, GameStatus
from sqlalchemy import select, update, delete
from typing import List, Optional
from loader import bot
import logging

logger = logging.getLogger(__name__)

# Создаем асинхронный движок для SQLite
engine = create_async_engine(
    "sqlite+aiosqlite:///database/database.db"
)

# Создаем фабрику сессий
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Функции для работы с пользователями
async def get_user(user_id: str) -> Optional[User]:
    """Получить пользователя по TelegramID"""
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        return result.scalar_one_or_none()

async def get_user_by_id(user_id: int) -> Optional[User]:
    """Получить пользователя по ID"""
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

async def create_user(user_id: str, full_name: str, username: str) -> User:
    """Создать нового пользователя"""
    async with async_session() as session:
        user = User(user_id=user_id, full_name=full_name, username=username)
        session.add(user)
        await session.commit()
        return user

# Функции для работы с играми
async def create_game(max_players: int = 4) -> Game:
    """Создать новую игру"""
    async with async_session() as session:
        game = Game(max_players=max_players)
        session.add(game)
        await session.commit()
        return game
    
async def end_game(game_id: int) -> bool:
    """Завершить игру"""
    async with async_session() as session:
        game = await get_game(game_id)
        if not game:
            return False
        game.status = GameStatus.FINISHED
        session.add(game)
        await session.commit()
        return True


async def get_current_player(game_id: int) -> Optional[User]:
    """Получить текущего игрока (поле current_player_id) """
    async with async_session() as session:
        game = await get_game(game_id)
        if not game:
            return None
        result = await session.execute(
            select(User).where(User.id == game.current_player_id)
        )
        return result.scalar_one_or_none()

async def get_game_by_user_id(user_id: int) -> Optional[Game]:
    """Получить игру по ID игрока """
    async with async_session() as session:
        # Получаем объекты player игрока, затем их игры
        player = await session.execute(
            select(GamePlayer).where(GamePlayer.user_id == user_id)
        )
        player = player.scalar_one_or_none()
        if not player:
            return None
        return player.game

async def get_game(game_id: int) -> Optional[Game]:
    """Получить игру по ID"""
    async with async_session() as session:
        result = await session.execute(
            select(Game).where(Game.id == game_id)
        )
        return result.scalar_one_or_none()

async def get_active_games() -> List[Game]:
    """Получить список активных игр"""
    async with async_session() as session:
        result = await session.execute(
            select(Game).where(Game.status == GameStatus.IN_PROGRESS)
        )
        return result.scalars().all()
    
async def get_waiting_games() -> List[Game]:
    """ Получить список игр,в ожидании игроков """
    async with async_session() as session:
        result = await session.execute(
            select(Game).where(Game.status == GameStatus.WAITING)
        )
        return result.scalars().all()

async def get_cards_by_game_query(game_id: int) -> List[Card]:
    """Получение списка карт игры"""
    async with async_session() as session:
        result = await session.execute(
            select(Game)
            .options(selectinload(Game.cards))
            .where(Game.id == game_id)
        )
        game = result.unique().scalar_one_or_none()
        return game.cards if game else []

async def get_players_by_game_query(game_id: int) -> List[GamePlayer]:
    """Получить список игроков по игре"""
    async with async_session() as session:
        result = await session.execute(
            select(GamePlayer)
            .options(selectinload(GamePlayer.user))
            .where(GamePlayer.game_id == game_id)
        )
        return result.scalars().all()

async def join_game(game_id: int, user_id: int) -> bool:
    """Присоединиться к игре"""
    async with async_session() as session:
        game = await get_game(game_id)
        if not game or game.status != GameStatus.WAITING:
            return False
        
        # Проверяем, не присоединился ли уже пользователь
        existing_player = await get_game_by_user_id(user_id)
        if existing_player:
            return False
        
        # Проверяем количество игроков
        players_count = await get_players_by_game_query(game_id)
        
        if len(players_count) < game.max_players:
            # Добавляем игрока
            player = GamePlayer(game_id=game_id, user_id=user_id)
            session.add(player)
            await session.commit()

            if len(players_count) + 1 == game.max_players:
            # Оповещаем всех игроков о том, что игра началась
                players = await get_players_by_game_query(game_id)
                for player in players:
                    user_obj = await get_user_by_id(player.user_id)
                    await bot.send_message(
                        user_obj.user_id,
                        text=f"Игра #{game_id} началась! Начинаем раздачу карт..."
                    )   
                await deal_cards(game_id)
            return True
        return False
        
        
        

# Функции для работы с фракциями
async def create_faction(name: str, description: str = None) -> Faction:
    """Создать новую фракцию"""
    async with async_session() as session:
        faction = Faction(name=name, description=description)
        session.add(faction)
        await session.commit()
        return faction

async def add_card_to_faction(faction_id: int, card_name: str) -> Card:
    """Добавить карту в фракцию"""
    async with async_session() as session:
        card = Card(name=card_name, faction_id=faction_id)
        session.add(card)
        await session.commit()
        return card

async def get_faction(faction_id: int) -> Optional[Faction]:
    """Получить фракцию по ID"""
    async with async_session() as session:
        result = await session.execute(
            select(Faction).where(Faction.id == faction_id)
        )
        return result.scalar_one_or_none()

async def get_factions() -> List[Faction]:
    """Получить все фракции"""
    async with async_session() as session:
        result = await session.execute(select(Faction))
        return result.scalars().all()

async def get_cards_by_faction(faction_id: int) -> List[Card]:
    """Получить все карты фракции"""
    async with async_session() as session:
        result = await session.execute(
            select(Card).where(Card.faction_id == faction_id)
        )
        return result.scalars().all()

async def delete_faction(faction_id: int) -> bool:
    """Удалить фракцию"""
    async with async_session() as session:
        result = await session.execute(
            delete(Faction).where(Faction.id == faction_id)
        )
        await session.commit()
        return result.rowcount > 0

# Функции для работы с картами в игре
async def deal_cards(game_id: int) -> bool:
    """Раздать карты в игре"""
    async with async_session() as session:
        game = await get_game(game_id)
        if not game or game.status != GameStatus.WAITING:
            return False
        
        # Получаем все карты
        cards = await session.execute(select(Card))
        cards = cards.scalars().all()
        
        # Получаем всех игроков
        players = await session.execute(
            select(GamePlayer).where(GamePlayer.game_id == game_id)
        )
        players = players.scalars().all()
        
        # Раздаем карты
        for i, card in enumerate(cards):
            player = players[i % len(players)]
            game_card = GameCard(
                game_id=game_id,
                card_id=card.id,
                player_id=player.id
            )
            session.add(game_card)
        
        # Обновляем статус игры
        game.status = GameStatus.IN_PROGRESS
        game.current_player_id = players[0].user_id
        session.add(game)

        await session.commit()
        return True 


async def get_user_by_user_id(user_id: str):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        return result.scalars().first()

async def create_user(user_id: str, full_name: str, username: str, is_premium: bool = None, is_admin: bool = False):
    async with async_session() as session:
        user = User(user_id=user_id, full_name=full_name, username=username, is_premium=is_premium, is_admin=is_admin)
        session.add(user)
        await session.commit()
        return user

async def get_group_by_group_id(group_id: str):
    async with async_session() as session:
        result = await session.execute(select(Group).where(Group.group_id == group_id))
        return result.scalars().first()

async def create_group(group_id: str, title: str, description: str = None, bio: str = None,
                       invite_link: str = None, location: str = None, username: str = None):
    async with async_session() as session:
        group = Group(
            group_id=group_id,
            title=title,
            description=description,
            bio=bio,
            invite_link=invite_link,
            location=location,
            username=username
        )
        session.add(group)
        await session.commit()
        return group

async def get_all_users():
    async with async_session() as session:
        result = await session.execute(select(User))
        return result.scalars().all()

async def update_user_invoice(user_id: str, invoice_path: str):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        user = result.scalars().first()
        if user:
            user.path_to_invoice = invoice_path
            await session.commit()
        return user
