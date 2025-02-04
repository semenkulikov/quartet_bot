from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from database.models import Base
import enum
import json


# Для статуса игры можно использовать Enum
class GameStatus(enum.Enum):
    waiting = "waiting"  # Ожидание игроков
    in_progress = "in_progress"  # Идет игра
    finished = "finished"  # Игра завершена


class GameSession(Base):
    __tablename__ = 'game_sessions'

    id = Column(Integer, primary_key=True, index=True)
    status = Column(Enum(GameStatus), default=GameStatus.waiting)
    current_turn = Column(String, nullable=True)  # Можно хранить Telegram user_id активного игрока
    # Добавьте дополнительные поля (например, время старта игры)

    # Связь с участниками
    players = relationship("PlayerGame", back_populates="game_session")


class Faction(Base):
    __tablename__ = 'factions'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    # Дополнительные данные при необходимости (например, описание)

    # Связь с картами
    cards = relationship("Card", back_populates="faction")


class Card(Base):
    __tablename__ = 'cards'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    faction_id = Column(Integer, ForeignKey('factions.id'), nullable=False)

    # Если карта находится в колоде или у игрока, можно хранить owner_id (Telegram user_id) или game_session_id
    owner_id = Column(String, nullable=True)  # если карта у игрока
    in_deck = Column(Boolean, default=True)  # True, если ещё в колоде

    faction = relationship("Faction", back_populates="cards")


class PlayerGame(Base):
    __tablename__ = 'player_games'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)  # Ссылка на Telegram ID (User.user_id)
    game_session_id = Column(Integer, ForeignKey('game_sessions.id'), nullable=False)

    # Для хранения набора карт можно использовать JSON строку
    hand = Column(String, default="[]")  # JSON-список ID карт

    game_session = relationship("GameSession", back_populates="players")
