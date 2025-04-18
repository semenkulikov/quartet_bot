from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()

class GameStatus(enum.Enum):
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"

    def __str__(self):
        return self.value

class User(Base):
    """ Модель для пользователя """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, nullable=False)  # Telegram ID
    full_name = Column(String, nullable=False)
    username = Column(String, nullable=False)
    is_premium = Column(Boolean, nullable=True)
    is_admin = Column(Boolean, default=False)
    
    # Связи
    games = relationship("GamePlayer", back_populates="user")

class Faction(Base):
    __tablename__ = 'factions'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Связи
    cards = relationship("Card", back_populates="faction")

class Card(Base):
    __tablename__ = 'cards'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    faction_id = Column(Integer, ForeignKey('factions.id'))
    
    # Связи
    faction = relationship("Faction", back_populates="cards")
    game_cards = relationship("GameCard", back_populates="card")

class Game(Base):
    __tablename__ = 'games'
    
    id = Column(Integer, primary_key=True, index=True)
    status = Column(Enum(GameStatus), default=GameStatus.WAITING)
    max_players = Column(Integer, default=4)
    current_player_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Связи
    players = relationship("GamePlayer", back_populates="game")
    cards = relationship("GameCard", back_populates="game")

class GamePlayer(Base):
    __tablename__ = 'game_players'
    
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey('games.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    score = Column(Integer, default=0)
    
    # Связи
    game = relationship("Game", back_populates="players")
    user = relationship("User", back_populates="games")
    cards = relationship("GameCard", back_populates="player")

class GameCard(Base):
    __tablename__ = 'game_cards'
    
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey('games.id'))
    card_id = Column(Integer, ForeignKey('cards.id'))
    player_id = Column(Integer, ForeignKey('game_players.id'), nullable=True)
    
    # Связи
    game = relationship("Game", back_populates="cards")
    card = relationship("Card", back_populates="game_cards")
    player = relationship("GamePlayer", back_populates="cards")

class Group(Base):
    __tablename__ = 'groups'

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    bio = Column(Text, nullable=True)
    invite_link = Column(String, nullable=True)
    location = Column(String, nullable=True)
    username = Column(String, nullable=True)
