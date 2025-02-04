import random
import json
from database.models_game import GameSession, Faction, Card, PlayerGame
from database.engine import async_session
from sqlalchemy.future import select

class GameManager:
    """Менеджер для управления игровым сеансом"""

    async def create_game(self):
        async with async_session() as session:
            game = GameSession(status="waiting")
            session.add(game)
            await session.commit()
            return game

    async def join_game(self, game_id: int, user_id: str):
        async with async_session() as session:
            # Проверяем, существует ли игра и её статус
            result = await session.execute(select(GameSession).where(GameSession.id == game_id))
            game = result.scalars().first()
            if game and game.status == "waiting":
                # Создаем связь игрока с игрой
                player_game = PlayerGame(user_id=user_id, game_session_id=game_id, hand="[]")
                session.add(player_game)
                await session.commit()
                return player_game
            return None

    async def start_game(self, game_id: int):
        """При старте игры: раздаем карты игрокам, обновляем статус игры."""
        async with async_session() as session:
            result = await session.execute(select(GameSession).where(GameSession.id == game_id))
            game = result.scalars().first()
            if game and game.status == "waiting":
                # Получаем всех игроков в игре
                result = await session.execute(select(PlayerGame).where(PlayerGame.game_session_id == game_id))
                players = result.scalars().all()
                # Подготавливаем колоду: выбираем все карты из всех фракций
                result = await session.execute(select(Card))
                deck = result.scalars().all()
                random.shuffle(deck)
                # Раздаем карты по кругу
                i = 0
                while deck:
                    card = deck.pop()
                    players[i % len(players)].hand = json.dumps(
                        json.loads(players[i % len(players)].hand) + [card.id]
                    )
                    # Обновляем владельца карты
                    card.owner_id = players[i % len(players)].user_id
                    card.in_deck = False
                    i += 1
                game.status = "in_progress"
                # Устанавливаем первого игрока (например, первого из списка)
                game.current_turn = players[0].user_id
                await session.commit()
                return game
            return None

    async def make_move(self, game_id: int, requester_id: str, target_id: str, requested_card_id: int):
        """
        Обработка запроса карты:
         - Если у target_id запрошенная карта, передаем карту requester_id и возвращаем True (ход продолжается).
         - Если нет, меняем активного игрока и возвращаем False.
        """
        async with async_session() as session:
            # Получаем карту
            result = await session.execute(select(Card).where(Card.id == requested_card_id))
            card = result.scalars().first()
            if card and card.owner_id == target_id:
                # Передаем карту requester-у:
                card.owner_id = requester_id
                # Обновляем руку игрока-источника
                result = await session.execute(select(PlayerGame).where(
                    PlayerGame.game_session_id == game_id, PlayerGame.user_id == target_id))
                target_pg = result.scalars().first()
                hand = json.loads(target_pg.hand)
                if requested_card_id in hand:
                    hand.remove(requested_card_id)
                    target_pg.hand = json.dumps(hand)
                # Обновляем руку запрашивающего игрока
                result = await session.execute(select(PlayerGame).where(
                    PlayerGame.game_session_id == game_id, PlayerGame.user_id == requester_id))
                requester_pg = result.scalars().first()
                hand_req = json.loads(requester_pg.hand)
                hand_req.append(requested_card_id)
                requester_pg.hand = json.dumps(hand_req)
                await session.commit()
                return True
            else:
                # Если карта не найдена или не у target_id, то сменить ход:
                result = await session.execute(select(GameSession).where(GameSession.id == game_id))
                game = result.scalars().first()
                # Здесь можно реализовать логику определения следующего игрока
                # Например, получить список игроков и найти следующего после requester_id
                # Для простоты пока оставим заглушку:
                game.current_turn = target_id
                await session.commit()
                return False
