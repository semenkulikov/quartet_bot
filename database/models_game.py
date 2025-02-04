from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from database.models import Base
import enum
import json


class GameStatus(enum.Enum):
    """Статусы игровой сессии."""
    waiting = "waiting"  # Ожидание игроков (игроки ещё могут присоединяться)
    in_progress = "in_progress"  # Игра идет
    finished = "finished"  # Игра завершена


class GameSession(Base):
    """Модель игровой сессии."""
    __tablename__ = 'game_sessions'

    id = Column(Integer, primary_key=True, index=True)
    status = Column(Enum(GameStatus), default=GameStatus.waiting)
    current_turn = Column(String, nullable=True)  # Telegram user_id активного игрока
    creator_id = Column(String, nullable=True)  # ID создателя игры (например, админа)

    # Связь с участниками игры
    players = relationship("PlayerGame", back_populates="game_session", cascade="all, delete-orphan")


class Faction(Base):
    """Модель фракции (набор карт)."""
    __tablename__ = 'factions'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)

    # Связь с картами
    cards = relationship("Card", back_populates="faction", cascade="all, delete-orphan")


class Card(Base):
    """Модель карты, принадлежащей фракции."""
    __tablename__ = 'cards'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    faction_id = Column(Integer, ForeignKey('factions.id'), nullable=False)
    owner_id = Column(String, nullable=True)  # Telegram user_id владельца (если распределена)
    in_deck = Column(Boolean, default=True)  # Карта в колоде или уже у игрока

    faction = relationship("Faction", back_populates="cards")


class PlayerGame(Base):
    """Связующая модель игрока с игровой сессией."""
    __tablename__ = 'player_games'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)  # Telegram user_id игрока
    game_session_id = Column(Integer, ForeignKey('game_sessions.id'), nullable=False)
    hand = Column(String, default="[]")  # JSON-список ID карт, находящихся у игрока

    game_session = relationship("GameSession", back_populates="players")
