import asyncio
import typing

from asyncio import Task
from logging import getLogger
from typing import Optional
from Levenshtein import distance


from app.store.bot.dataclasses import Update, UpdateObject
from app.store.vk_api.dataclasses import Message, MessageEvent, RawUser
from app.game.models import Question, UserModel, User, Game


if typing.TYPE_CHECKING:
    from app.web.app import Application

KEYBOARD_TYPE = {
    "default": "keyboard_default",
    "start": "keyboard_game",
}
EVENT_TYPE = {
    "text": "message_new",
    "event": "message_event",
    "join": "group_join",
}


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.bot = None
        self.logger = getLogger("handler")
        self.start_command = f"[club{self.app.config.bot.group_id}|@club{self.app.config.bot.group_id}] "
        app.on_startup.append(self.connect)
        # self.current_game
        # 11111 as peer_id: {
        # "game": Game,
        # "current_question": Question,
        # "current_user_answers": set(str) = set(),
        # "current_game_over_users": []
        # }
        self.current_game: dict = {}
        self.game_task: Optional[Task] = None

    # При запуске бота заполняем бд пользователями из сообщества
    async def connect(self, app: "Application"):
        # Получаем количество пользователей в базе
        cnt = await self.app.store.games.get_users_count_in_db()
        # Получаем список пользователей из вк
        raw_users: [RawUser] = await self.app.store.vk_api.get_community_members(cnt)
        # Заносим пользователей в базу
        if raw_users:
            list_user_model = self._cast_raw_user_to_usermodel(raw_users)
            await self.app.store.games.add_users(list_user_model)

    async def handle_updates_rabbit(self, response: dict):
        update: [Update] = await self._create_update_object(response)
        if update:
            if update.type == EVENT_TYPE["event"] and update.object.message == "rules":
                message_text = "Первое правило бойцовского клуба."
                await self._sending_to_callback(
                                                update.object.peer_id,
                                                update.object.user_id,
                                                message_text,
                                                update.object.event_id
                                            )
            elif update.type == EVENT_TYPE["event"] and update.object.message == "1":
                is_exists_game = await self.app.store.games.get_current_game(update.object.peer_id)
                cur_user = await self.app.store.games.get_user_by_vk_id(update.object.user_id)
                if is_exists_game:
                    message_text = f"Игра уже была запущена."
                    await self._sending_to_chat(update.object.peer_id, message_text, KEYBOARD_TYPE["start"])
                    await self._sending_to_callback(update.object.peer_id,
                                                    update.object.user_id,
                                                    message_text,
                                                    update.object.event_id)
                else:
                    game: Game = await self.app.store.games.create_game(update.object.peer_id)
                    self.current_game[update.object.peer_id] = {
                        "game": game,
                        "current_question": None,
                        "current_user_answers": set(),
                        "current_game_over_users": []
                        }
                    message_text = f"Участник {cur_user.first_name} {cur_user.last_name} запустил игру."
                    await self._sending_to_callback(update.object.peer_id,
                                                    update.object.user_id,
                                                    message_text,
                                                    update.object.event_id)
                    await self._sending_to_chat(update.object.peer_id, message_text, KEYBOARD_TYPE["start"])
                    # ЭТО САМАЯ СЛОЖНАЯ СТРОЧКА В МОЕЙ ЖИЗНИ!
                    self.game_task = asyncio.create_task(
                        self.start_game(
                            self.current_game[update.object.peer_id]["game"]))

            elif update.type == EVENT_TYPE["event"] and update.object.message == "0":
                if self.current_game.get(update.object.peer_id):
                    self.game_task.cancel()
                    await self._end_game(self.current_game[update.object.peer_id]["game"],
                                         peer_id=update.object.peer_id,
                                         user_id=update.object.user_id,
                                         event_id=update.object.event_id)
                else:
                    await self._end_game(None,
                                         peer_id=update.object.peer_id,
                                         user_id=update.object.user_id,
                                         event_id=update.object.event_id)

            elif update.type == EVENT_TYPE["join"]:
                exists_user: User = await self.app.store.games.get_user_by_vk_id(update.object.user_id)
                if not exists_user:
                    raw_users: [RawUser] = await self.app.store.vk_api.get_user_data([update.object.user_id])
                    list_user_model = self._cast_raw_user_to_usermodel(raw_users)
                    await self.app.store.games.add_users(list_user_model)
            # Сообщение пользователя во время игры
            elif update.type == EVENT_TYPE["text"] and self.current_game.get(update.object.peer_id):
                # Проверяем что пользователь ещё не проиграл
                if (update.object.user_id not in self.current_game[update.object.peer_id]["current_game_over_users"] and
                    self.current_game[update.object.peer_id].get("current_question")
                ):
                    current_user: User = await self.app.store.games.get_user_by_vk_id(update.object.user_id)
                    for a in self.current_game[update.object.peer_id]["current_question"].answers:
                        if update.object.message.lower() not in self.current_game[update.object.peer_id]["current_user_answers"]:
                            # if a.title.lower() == update.object.message.lower():
                            user_answer = update.object.message.lower()
                            correct_answer = a.title.lower()
                            # Если длина ответа от 3 до 6 символов и расстояние Левенштейна 0-2
                            # Если длина ответа больше 6 символов и расстояние Левенштейна = 3
                            if (len(user_answer) < 7 and distance(user_answer, correct_answer) < 3) or (
                                    len(user_answer) >= 6 and distance(user_answer, correct_answer) < 3
                            ):
                                await self.app.store.games.save_user_answer(game_id=self.current_game[update.object.peer_id]["game"].id,
                                                                            user_id=current_user.id,
                                                                            answer_id=a.id,
                                                                            answer_score=a.score,
                                                                            )
                                self.current_game[update.object.peer_id]["current_user_answers"].add(update.object.message.lower())
                                message = f"Пользователь " \
                                          f"{current_user.first_name} {current_user.last_name}" \
                                          f" заработал {self._case_word(a.score)}."
                                await self._sending_to_chat(update.object.peer_id, message, KEYBOARD_TYPE["start"])
                                break
                    else:
                        # Неверный ответ
                        await self.app.store.games.save_user_answer(game_id=self.current_game[update.object.peer_id]["game"].id,
                                                                    user_id=current_user.id,
                                                                    answer_id=-1,
                                                                    answer_score=0)
                        failures = await self.app.store.games.get_statistics_for_user(
                            self.current_game[update.object.peer_id]["game"].id,
                            current_user.id)
                        if failures == 5:
                            message = f"{current_user.first_name} {current_user.last_name} мы вас услышали."
                        else:
                            message = f"Пользователь " \
                                      f"{current_user.first_name} {current_user.last_name} ответил неправильно." \
                                      f"<br>Это {failures} промах из 5."
                        await self._sending_to_chat(update.object.peer_id, message, KEYBOARD_TYPE["start"])
                        if failures == 5:
                            self.current_game[update.object.peer_id]["current_game_over_users"].append(current_user.vk_id)

                print(f"Пользователь {update.object.user_id} написал {update.object.message}")
                # print(self.current_game)
            elif update.type == EVENT_TYPE["text"] and update.object.user_id == 89191476 and update.object.message == "!startbot42":
                await self._sending_to_chat(update.object.peer_id, "Поехали", KEYBOARD_TYPE["default"])

    async def start_game(self, game: Game):
        for i, cur_round in enumerate(game.road_map):
            if cur_round.status is False:
                message: str = f"==========================================<br>" \
                               f"Вопрос № {i + 1} будет задан через 5 секунд!<br>" \
                               f"==========================================="
                await self._sending_to_chat(game.peer_id
                                            , message, KEYBOARD_TYPE["start"])
                self.current_game[game.peer_id]["current_question"]: Question = await self.app.store.games.get_question_by_id(cur_round.question_id)
                await asyncio.sleep(5)

                message: str = f"{self.current_game[game.peer_id]['current_question'].title.upper()}<br>У вас 20 секунд на ответ!"
                await self._sending_to_chat(game.peer_id, message, KEYBOARD_TYPE["start"])

                await asyncio.sleep(20)
                await self.app.store.games.close_roadmap_step(cur_round)

                message: str = "Время вышло."
                await self._sending_to_chat(game.peer_id, message, KEYBOARD_TYPE["start"])
                # Очищаем ответы пользователей для следующего раунда
                self.current_game[game.peer_id]["current_user_answers"] = set()
        else:
            await self._end_game(game, game.peer_id)

    async def _end_game(self, game: Optional[Game], peer_id: int, user_id: int = None, event_id: str = None):
        game_id: int = await self.app.store.games.end_game(peer_id=peer_id, game=game)
        message: str = "Игра окончена."
        if user_id:
            cur_user = await self.app.store.games.get_user_by_vk_id(user_id)
            message: str = f"Участник {cur_user.first_name} {cur_user.last_name} закончил игру досрочно."
            await self._sending_to_callback(peer_id, user_id, message, event_id)
        await self._sending_to_chat(peer_id, message, KEYBOARD_TYPE["default"])
        statistics = await self.app.store.games.get_statistics(game_id=game_id)
        message: str = "Результаты игры"
        for st in statistics:
            message += f"<br>{st[0]} {st[1]} заработал {self._case_word(st[2])}."
        await self._sending_to_chat(peer_id, message, KEYBOARD_TYPE["default"])
        if game:
            self.current_game.pop(peer_id)

    async def _create_update_object(self, data: dict) -> Optional[Update]:
        # Новое сообщение
        if data["type"] == "message_new":
            update: Update = Update(
                group_id=data["group_id"],
                type=data["type"],
                object=UpdateObject(
                    user_id=data["object"]["message"]["from_id"],
                    peer_id=data["object"]["message"]["peer_id"],
                    event_id=data["object"]["message"]["id"],
                    message=data["object"]["message"]["text"]
                )
            )
        # Новое событие
        elif data["type"] == "message_event":
            update: Update = Update(
                group_id=data["group_id"],
                type=data["type"],
                object=UpdateObject(
                    user_id=data["object"]["user_id"],
                    peer_id=data["object"]["peer_id"],
                    message=data["object"]["payload"]["game"],
                    event_id=data["object"]["event_id"],
                ),
            )
        # Новый пользователь
        elif data["type"] == "group_join":
            update: Update = Update(
                group_id=data["group_id"],
                type=data["type"],
                object=UpdateObject(
                    user_id=data["object"]["user_id"],
                    event_id=data["event_id"],
                ),
            )
        else:
            return None
        return update

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
                # peer_id=update.object.peer_id,
                peer_id=peer_id,
                # user_id=update.object.user_id,
                user_id=user_id,
                message=message,
                event_id=event_id,
            )
        )

    # Преобразуем пользователей из вк в нашу модель пользователя
    def _cast_raw_user_to_usermodel(self, raw_users: [RawUser]) -> [UserModel]:
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
    def _case_word(self, n: int) -> str:
        d = n % 10
        h = n % 100
        if d == 1 and h != 11:
            s = ""
        elif 1 < d < 5 and not 11 < h < 15:
            s = "а"
        else:
            s = "ов"
        return f"{n} балл{s}"
