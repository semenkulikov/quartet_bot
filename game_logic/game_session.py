from typing import List, Optional, Dict

from sqlalchemy import select
from database.models import Game, GamePlayer, GameCard, Card, Faction, GameStatus
from database.db import async_session
from database.db import get_game, get_user, join_game, deal_cards
import logging

logger = logging.getLogger(__name__)

class GameSession:
    def __init__(self, game_id: int):
        self.game_id = game_id
        self.game: Optional[Game] = None
        self.players: List[GamePlayer] = []
        self.cards: List[GameCard] = []
        
    async def load(self):
        """Загрузить данные игры"""
        self.game = await get_game(self.game_id)
        if not self.game:
            raise ValueError(f"Игра {self.game_id} не найдена")
            
        # Загружаем игроков
        async with async_session() as session:
            result = await session.execute(
                select(GamePlayer).where(GamePlayer.game_id == self.game_id)
            )
            self.players = result.scalars().all()
            
            # Загружаем карты
            result = await session.execute(
                select(GameCard).where(GameCard.game_id == self.game_id)
            )
            self.cards = result.scalars().all()
    
    async def start(self):
        """Начать игру"""
        if not self.game or self.game.status != GameStatus.WAITING:
            raise ValueError("Игра не может быть начата")
            
        # Раздаем карты
        if not await deal_cards(self.game_id):
            raise ValueError("Не удалось раздать карты")
            
        await self.load()
        logger.info(f"Игра {self.game_id} начата")
    
    async def get_player_cards(self, player_id: int) -> List[Card]:
        """Получить карты игрока"""
        player_cards = []
        for game_card in self.cards:
            if game_card.player_id == player_id:
                player_cards.append(game_card.card)
        return player_cards
    
    async def get_player_factions(self, player_id: int) -> Dict[Faction, List[Card]]:
        """Получить фракции игрока"""
        factions: Dict[Faction, List[Card]] = {}
        for game_card in self.cards:
            if game_card.player_id == player_id:
                card = game_card.card
                if card.faction not in factions:
                    factions[card.faction] = []
                factions[card.faction].append(card)
        return factions
    
    async def request_card(self, from_player_id: int, to_player_id: int, card_name: str) -> bool:
        """Запросить карту у другого игрока"""
        # Проверяем, что это ход текущего игрока
        if self.game.current_player_id != from_player_id:
            return False
            
        # Находим запрашиваемую карту
        requested_card = None
        for game_card in self.cards:
            if game_card.player_id == to_player_id and game_card.card.name == card_name:
                requested_card = game_card
                break
                
        if not requested_card:
            # Карта не найдена, ход переходит к другому игроку
            self.game.current_player_id = to_player_id
            await self.save_game()
            return False
            
        # Передаем карту
        requested_card.player_id = from_player_id
        await self.save_game()
        return True
    
    async def check_quartet(self, player_id: int) -> Optional[Faction]:
        """Проверить, собрал ли игрок квартет"""
        factions = await self.get_player_factions(player_id)
        for faction, cards in factions.items():
            if len(cards) == 4:  # Квартет собран
                # Удаляем карты из игры
                for game_card in self.cards:
                    if game_card.card in cards:
                        self.cards.remove(game_card)
                # Увеличиваем счет игрока
                for player in self.players:
                    if player.user_id == player_id:
                        player.score += 1
                await self.save_game()
                return faction
        return None
    
    async def save_game(self):
        """Сохранить состояние игры"""
        async with async_session() as session:
            session.add(self.game)
            for player in self.players:
                session.add(player)
            for card in self.cards:
                session.add(card)
            await session.commit()
    
    async def end_game(self):
        """Завершить игру"""
        self.game.status = GameStatus.FINISHED
        await self.save_game()
        logger.info(f"Игра {self.game_id} завершена") 