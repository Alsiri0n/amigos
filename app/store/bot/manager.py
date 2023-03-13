import asyncio
import typing

from asyncio import Task
from logging import getLogger
from typing import Optional
from Levenshtein import distance

from app.store.bot.dataclasses import Update, UpdateObject, KeyboardType, UpdateType, EventType
from app.store.vk_api.dataclasses import Message, MessageEvent, RawUser
from app.game.models import UserModel, User, Game, GameEntity

if typing.TYPE_CHECKING:
    from app.web.app import Application


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.bot = None
        self.logger = getLogger("handler")
        self.start_command = f"[club{self.app.config.bot.group_id}|@club{self.app.config.bot.group_id}] "
        app.on_startup.append(self.connect)
        self.games: dict[int, GameEntity] = {}
        self.game_task: Optional[Task] = None

    # При запуске бота заполняем бд пользователями из сообщества
    async def connect(self, app: "Application"):
        # Получаем vk_id пользователей уже имеющихся в базе
        users_from_db = await self.app.store.games.get_users_count_in_db()
        # Получаем список пользователей из вк
        users_from_vk: [RawUser] = await self.app.store.vk_api.get_community_members()
        users_id_from_vk = {u.id_ for u in users_from_vk}
        id_need_to_add = users_id_from_vk - users_from_db
        # Добавляем новых пользователей в базу
        if id_need_to_add:
            new_users = [u for u in users_from_vk if u.id_ in id_need_to_add]
            list_user_model = self._cast_raw_user_to_model(new_users)
            await self.app.store.games.add_users(list_user_model)

    async def handle_updates(self, response: dict):
        update: [Update] = await self._create_update_object(response)
        # Если произошло только то, событие которое мы отслеживаем
        if update:
            # Нажали кнопку правила
            if update.type == UpdateType.EVENT and update.object.payload == EventType.RULES:
                await self._send_rules(update.object.peer_id, update.object.user_id, update.object.event_id)
            # Нажали кнопку начало игры
            elif update.type == UpdateType.EVENT and update.object.payload == EventType.START:
                await self.start_button(update.object.peer_id, update.object.user_id, update.object.event_id)
            # Нажали кнопку закончить игру
            elif update.type == UpdateType.EVENT and update.object.payload == EventType.FINISH:
                await self.finish_button(update.object.peer_id, update.object.user_id, update.object.event_id)
            elif update.type == UpdateType.JOIN:
                await self._add_new_user(update.object.user_id)
            # Сообщение пользователя во время игры
            elif update.type == UpdateType.TEXT and self.games.get(update.object.peer_id):
                # Проверяем что пользователь ещё не проиграл и такого ответа ещё не было
                if (update.object.user_id not in self.games.get(update.object.peer_id).game_over_users and
                        update.object.message.lower() not in self.games[update.object.peer_id].past_user_answers):
                    await self._user_answer(update.object.peer_id, update.object.user_id, update.object.message.lower())
            # (ре)Активация бота
            elif update.type == UpdateType.TEXT and \
                    update.object.user_id == self.app.config.admin.vk_id and \
                    update.object.message == "!startbot42":
                await self._sending_to_chat(update.object.peer_id, "Поехали", KeyboardType.DEFAULT.value)

    async def start_button(self, peer_id: int, user_id: int, event_id: str):
        is_exists_game = await self.app.store.games.get_current_game(peer_id)
        cur_user = await self.app.store.games.get_user_by_vk_id(user_id)
        if not cur_user:
            await self._add_new_user(user_id)
            cur_user = await self.app.store.games.get_user_by_vk_id(user_id)
        if is_exists_game:
            message_text = f"Игра уже была запущена."
            await self._sending_to_chat(peer_id, message_text, KeyboardType.START.value)
            await self._sending_to_callback(peer_id, user_id, message_text, event_id)
        else:
            game: Game = await self.app.store.games.create_game(peer_id)
            self.games[peer_id] = GameEntity(
                game=game,
                current_question=None,
                past_user_answers=set(),
                game_over_users=[])
            message_text = f"Участник {cur_user.first_name} {cur_user.last_name} запустил игру."
            await self._sending_to_callback(peer_id, user_id, message_text, event_id)
            await self._sending_to_chat(peer_id, message_text, KeyboardType.START.value)
            self.game_task = asyncio.create_task(self._game_play(self.games[peer_id].game))

    async def _game_play(self, game: Game):
        for i, cur_round in enumerate(game.road_map):
            if cur_round.status is False:
                message: str = f"{'='*43}<br>" \
                               f"Вопрос №{i + 1}/4 будет задан через 5 секунд!<br>" \
                               f"{'='*43}"
                await self._sending_to_chat(game.peer_id, message, KeyboardType.START.value)
                self.games[game.peer_id].current_question = await self.app.store.games.get_question_by_id(cur_round.question_id)
                await asyncio.sleep(5)
                message: str = f"{self.games[game.peer_id].current_question.title.upper()}<br>" \
                               f"У вас 20 секунд на ответ!"
                await self._sending_to_chat(game.peer_id, message, KeyboardType.START.value)

                await asyncio.sleep(20)
                await self.app.store.games.finish_roadmap_step(cur_round)

                message: str = "Время вышло."
                await self._sending_to_chat(game.peer_id, message, KeyboardType.START.value)
                # Очищаем ответы пользователей для следующего раунда
                self.games[game.peer_id].past_user_answers.clear()
        else:
            await self._end_game(game, game.peer_id)

    async def finish_button(self, peer_id: int, user_id: int, event_id: str):
        # Если игра существует
        if self.games.get(peer_id):
            self.game_task.cancel()
            await self._end_game(self.games[peer_id].game, peer_id=peer_id, user_id=user_id, event_id=event_id)
        # Если было зависание и нужно закрыть игру
        else:
            await self._end_game(None, peer_id=peer_id, user_id=user_id, event_id=event_id)

    async def _end_game(self, game: Optional[Game], peer_id: int, user_id: int = None, event_id: str = None):
        game_id: int = await self.app.store.games.end_game(peer_id=peer_id, game=game)
        message: str = "Игра окончена."
        if user_id:
            cur_user = await self.app.store.games.get_user_by_vk_id(user_id)
            message: str = f"Участник {cur_user.first_name} {cur_user.last_name} закончил игру досрочно."
            await self._sending_to_callback(peer_id, user_id, message, event_id)
        await self._sending_to_chat(peer_id, message, KeyboardType.DEFAULT.value)
        statistics = await self.app.store.games.get_statistics(game_id=game_id)
        message: str = "Результаты игры"
        for st in statistics:
            message += f"<br>{st[0]} {st[1]} заработал {self._case_word(st[2])}."
        await self._sending_to_chat(peer_id, message, KeyboardType.DEFAULT.value)
        if game:
            self.games.pop(peer_id)

    async def _add_new_user(self, user_id: int):
        exists_user: User = await self.app.store.games.get_user_by_vk_id(user_id)
        if not exists_user:
            raw_users: [RawUser] = await self.app.store.vk_api.get_user_data([user_id])
            list_user_model = self._cast_raw_user_to_model(raw_users)
            await self.app.store.games.add_users(list_user_model)

    async def _send_rules(self, peer_id: int, user_id: int, event_id: str):
        message_text = "Первое правило бойцовского клуба."
        await self._sending_to_callback(peer_id, user_id, message_text, event_id)

    async def _user_answer(self, peer_id: int, user_id: int, user_answer: str):
        current_user: User = await self.app.store.games.get_user_by_vk_id(user_id)
        for correct_ans in self.games[peer_id].current_question.answers:
            dst = distance(user_answer, correct_ans.title.lower())
            # Если длина ответа от 3 до 6 символов и расстояние Левенштейна < 2
            # Если длина ответа больше 6 символов и расстояние Левенштейна < 4
            if (len(user_answer) > 6 and dst < 4) or (len(user_answer) <= 6 and dst < 2):
                await self.app.store.games.save_user_answer(game_id=self.games[peer_id].game.id,
                                                            user_id=current_user.id,
                                                            answer_id=correct_ans.id,
                                                            answer_score=correct_ans.score,
                                                            )
                self.games[peer_id].past_user_answers.add(user_answer)
                message = f"Пользователь {current_user.first_name} {current_user.last_name}" \
                          f" заработал {self._case_word(correct_ans.score)}."
                await self._sending_to_chat(peer_id, message, KeyboardType.START.value)
                break
        # Если неверный ответ
        else:
            await self.app.store.games.save_user_answer(game_id=self.games[peer_id].game.id,
                                                        user_id=current_user.id,
                                                        answer_id=-1,
                                                        answer_score=0)
            failures = await self.app.store.games.get_user_failures(self.games[peer_id].game.id, current_user.id)
            if failures == 5:
                message = f"{current_user.first_name} {current_user.last_name} мы вас услышали."
                self.games[peer_id].game_over_users.append(current_user.vk_id)
            else:
                message = f"Пользователь {current_user.first_name} {current_user.last_name} ответил неправильно." \
                          f"<br>Это {failures} промах из 5."
            await self._sending_to_chat(peer_id, message, KeyboardType.START.value)
        # DEBUG print(f"Пользователь {update.object.user_id} написал {update.object.message}")

    @staticmethod
    async def _create_update_object(data: dict) -> Optional[Update]:
        if data:
            # Новое сообщение
            if data["type"] == UpdateType.TEXT.value:
                update: Update = Update(
                    group_id=data["group_id"],
                    type=UpdateType.TEXT,
                    object=UpdateObject(
                        user_id=data["object"]["message"]["from_id"],
                        peer_id=data["object"]["message"]["peer_id"],
                        event_id=data["object"]["message"]["id"],
                        message=data["object"]["message"]["text"]
                    )
                )
            # Новое событие
            elif data["type"] == UpdateType.EVENT.value:
                update: Update = Update(
                    group_id=data["group_id"],
                    type=UpdateType.EVENT,
                    object=UpdateObject(
                        user_id=data["object"]["user_id"],
                        peer_id=data["object"]["peer_id"],
                        payload=EventType(data["object"]["payload"]["game"]),
                        event_id=data["object"]["event_id"],
                    ),
                )
            # Новый пользователь
            elif data["type"] == UpdateType.JOIN.value:
                update: Update = Update(
                    group_id=data["group_id"],
                    type=UpdateType.JOIN,
                    object=UpdateObject(
                        user_id=data["object"]["user_id"],
                        event_id=data["event_id"],
                    ),
                )
            return update
        else:
            return None

    async def _sending_to_chat(self, peer_id: int, message: str, keyboard_type: str,):
        await self.app.store.vk_api.send_message(
            Message(
                # user_id=update.object.user_id,
                text=message,
                peer_id=peer_id,
                keyboard_type=keyboard_type,
            )
        )

    async def _sending_to_callback(self, peer_id: int, user_id: int, message: str, event_id: str):
        await self.app.store.vk_api.send_event(
            MessageEvent(
                peer_id=peer_id,
                # user_id=update.object.user_id,
                user_id=user_id,
                message=message,
                event_id=event_id,
            )
        )

    # Преобразуем пользователей из вк в нашу модель пользователя
    @staticmethod
    def _cast_raw_user_to_model(raw_users: list[RawUser]) -> list[UserModel]:
        list_user_model: [UserModel] = []
        for user in raw_users:
            list_user_model.append(
                UserModel(
                    vk_id=user.id_,
                    first_name=user.first_name,
                    last_name=user.last_name
                )
            )
        return list_user_model

    # Правильное множественное число до 1000
    @staticmethod
    def _case_word(n: int) -> str:
        d = n % 10
        h = n % 100
        if d == 1 and h != 11:
            s = ""
        elif 1 < d < 5 and not 11 < h < 15:
            s = "а"
        else:
            s = "ов"
        return f"{n} балл{s}"

