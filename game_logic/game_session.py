import random
import json
from sqlalchemy.future import select
from database.models_game import GameSession, Faction, Card, PlayerGame, GameStatus
from database.engine import async_session
from loader import app_logger


class GameManager:
    """Класс для управления игровой сессией и логикой игры «Квартет»."""

    async def create_game(self) -> GameSession:
        """
        Создает новую игровую сессию и возвращает её.
        """
        async with async_session() as session:
            game = GameSession(status=GameStatus.waiting)
            session.add(game)
            await session.commit()
            app_logger.info(f"Создана новая игра с ID: {game.id}")
            return game

    async def join_game(self, game_id: int, user_id: str) -> PlayerGame:
        """
        Добавляет игрока к игровой сессии с заданным game_id.
        :param game_id: ID игровой сессии.
        :param user_id: Telegram user_id игрока.
        :return: Объект PlayerGame или None, если присоединение не удалось.
        """
        async with async_session() as session:
            result = await session.execute(select(GameSession).where(GameSession.id == game_id))
            game = result.scalars().first()
            if game and game.status == GameStatus.waiting:
                # Проверка, что игрок ещё не в игре
                result = await session.execute(select(PlayerGame).where(
                    PlayerGame.game_session_id == game_id, PlayerGame.user_id == user_id))
                if result.scalars().first():
                    app_logger.info(f"Игрок {user_id} уже в игре {game_id}.")
                    return None
                player_game = PlayerGame(user_id=user_id, game_session_id=game_id, hand="[]")
                session.add(player_game)
                await session.commit()
                app_logger.info(f"Игрок {user_id} присоединился к игре {game_id}.")
                return player_game
            app_logger.warning(f"Не удалось присоединить игрока {user_id} к игре {game_id}.")
            return None

    async def get_active_games(self) -> list:
        """
        Возвращает список активных игр (ожидающих или в процессе).
        """
        async with async_session() as session:
            result = await session.execute(
                select(GameSession).where(GameSession.status.in_([GameStatus.waiting, GameStatus.in_progress]))
            )
            games = result.scalars().all()
            return games

    async def start_game(self, game_id: int) -> GameSession:
        """
        Запускает игру: раздает карты игрокам, меняет статус и определяет первого игрока.
        """
        async with async_session() as session:
            result = await session.execute(select(GameSession).where(GameSession.id == game_id))
            game = result.scalars().first()
            if game and game.status == GameStatus.waiting:
                # Получаем всех игроков сессии
                result = await session.execute(select(PlayerGame).where(PlayerGame.game_session_id == game_id))
                players = result.scalars().all()
                if not players:
                    app_logger.warning(f"Игра {game_id} не имеет игроков для старта.")
                    return None

                # Формируем колоду из всех карт всех фракций (или можно ограничить только нужными)
                result = await session.execute(select(Card))
                deck = result.scalars().all()
                random.shuffle(deck)

                # Раздаем карты по кругу
                i = 0
                while deck:
                    card = deck.pop()
                    player = players[i % len(players)]
                    hand = json.loads(player.hand)
                    hand.append(card.id)
                    player.hand = json.dumps(hand)
                    # Обновляем владельца карты
                    card.owner_id = player.user_id
                    card.in_deck = False
                    i += 1

                game.status = GameStatus.in_progress
                game.current_turn = players[0].user_id
                await session.commit()
                app_logger.info(f"Игра {game_id} запущена. Первый ход у {players[0].user_id}.")
                return game
            app_logger.warning(f"Не удалось запустить игру {game_id}.")
            return None

    async def make_move(self, game_id: int, requester_id: str, target_id: str, requested_card_id: int) -> bool:
        """
        Обрабатывает ход: запрашивающий игрок (requester_id) запрашивает карту (requested_card_id) у target_id.
        Если у target_id карта, то происходит передача и ход остаётся у requester_id, иначе ход передается target_id.
        :return: True, если ход удачный (карта передана), иначе False.
        """
        async with async_session() as session:
            # Проверка наличия карты у target
            result = await session.execute(select(Card).where(Card.id == requested_card_id))
            card = result.scalars().first()
            if card and card.owner_id == target_id:
                # Передача карты запрашивающему
                card.owner_id = requester_id

                # Обновляем руку у target
                result = await session.execute(select(PlayerGame).where(
                    PlayerGame.game_session_id == game_id, PlayerGame.user_id == target_id))
                target_pg = result.scalars().first()
                hand = json.loads(target_pg.hand)
                if requested_card_id in hand:
                    hand.remove(requested_card_id)
                    target_pg.hand = json.dumps(hand)

                # Обновляем руку у requester
                result = await session.execute(select(PlayerGame).where(
                    PlayerGame.game_session_id == game_id, PlayerGame.user_id == requester_id))
                requester_pg = result.scalars().first()
                hand_req = json.loads(requester_pg.hand)
                hand_req.append(requested_card_id)
                requester_pg.hand = json.dumps(hand_req)

                # Ход остаётся у requester
                await session.commit()
                app_logger.info(f"Игрок {requester_id} получил карту {requested_card_id} от {target_id} в игре {game_id}.")
                return True
            else:
                # Если карта не найдена – смена хода
                result = await session.execute(select(GameSession).where(GameSession.id == game_id))
                game = result.scalars().first()
                # Определяем следующего игрока по порядку (здесь можно добавить более сложную логику)
                result = await session.execute(select(PlayerGame).where(PlayerGame.game_session_id == game_id))
                players = result.scalars().all()
                user_ids = [p.user_id for p in players]
                if requester_id in user_ids:
                    idx = user_ids.index(requester_id)
                    next_idx = (idx + 1) % len(user_ids)
                    game.current_turn = user_ids[next_idx]
                await session.commit()
                app_logger.info(f"Игрок {requester_id} не получил карту {requested_card_id}. Ход передан {game.current_turn}.")
                return False

    async def finish_game(self, game_id: int):
        """
        Завершает игру: подсчитывает собранные фракции, рассылает результаты игрокам и обновляет статус.
        Здесь нужно реализовать логику проверки собранных фракций.
        """
        async with async_session() as session:
            result = await session.execute(select(GameSession).where(GameSession.id == game_id))
            game = result.scalars().first()
            if not game:
                app_logger.error(f"Игра {game_id} не найдена для завершения.")
                return None

            # Здесь реализуйте подсчет очков: например, для каждого игрока проверяем наличие всех 4 карт одной фракции
            # и формируем текстовый отчёт.
            results_text = "Результаты игры:\n"
            # Допустим, добавляем перебор игроков (реализуйте свою логику)
            result = await session.execute(select(PlayerGame).where(PlayerGame.game_session_id == game_id))
            players = result.scalars().all()
            for p in players:
                # Пример: просто выводим список карт (реальную проверку комплектов надо доработать)
                results_text += f"Игрок {p.user_id}: карты {p.hand}\n"
            game.status = GameStatus.finished
            await session.commit()
            app_logger.info(f"Игра {game_id} завершена. Результаты отправлены.")
            return results_text
