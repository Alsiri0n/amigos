import asyncio
import typing
import json
from asyncio import Task
from logging import getLogger
from typing import Optional

from aiormq.abc import DeliveredMessage

from app.store.bot.schemes import UpdateSchema, UpdateObjectMessageNew
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
        self.game: Game = None
        self.current_question: Question = None
        self.current_user_answers: [str] = []
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

    # async def handle_updates(self, updates: list[Update]):
    #     message_text = "Hello"
    #     for update in updates:
    #         # Handling new message
    #         if update["type"] == "message_new":
    #             print(f"написано было {update['object']['message']['text']}")
    #             # if update.object_message_new.text == self.start_command + "/Правила":
    #             #     message_text = "Правила игры"
    #             #     await self._sending_to_chat(update, message_text, KEYBOARD_TYPE["default"])
    #             # if update.object.text == self.start_command + "/поехали":
    #             #     message_text = "Игра началась"
    #             #     await self._sending_to_chat(update, message_text, KEYBOARD_TYPE["start"])
    #             # if update.object.text == self.start_command + "/приехали":
    #             #     message_text = "Игра завершилась"
    #             #     await self._sending_to_chat(update, message_text, KEYBOARD_TYPE["default"])
    #
    #         # Handling callback buttons
    #         elif update["type"] == "message_event":
    #             if update.object.payload == {"game": "rules"}:
    #                 message_text = "Первое правило бойцовского клуба."
    #                 await self._sending_to_callback(update.object.peer_id,
    #                                                 update.object.user_id,
    #                                                 message_text,
    #                                                 update.object.event_id)
    #             elif update.object.payload == {"game": "1"}:
    #                 cur_user = await self.app.store.games.get_user_by_vk_id(update.object.user_id)
    #                 game: Game = await self.app.store.games.create_game()
    #                 message_text = f"Участник {cur_user.first_name} {cur_user.last_name} запустил игру."
    #                 await self._sending_to_callback(update.object.peer_id,
    #                                                 update.object.user_id,
    #                                                 message_text,
    #                                                 update.object.event_id)
    #                 await self._sending_to_chat(update.object.peer_id, message_text, KEYBOARD_TYPE["start"])
    #                 # await self.start_game(game, update.object.peer_id)
    #                 # await
    #             elif update.object.payload == {"game": "0"}:
    #                 cur_user = await self.app.store.games.get_user_by_vk_id(update.object.user_id)
    #                 await self.app.store.games.end_game()
    #                 message_text = f"Участник {cur_user.first_name} {cur_user.last_name} закончил игру."
    #                 await self._sending_to_callback(update.object.peer_id,
    #                                                 update.object.user_id,
    #                                                 message_text,
    #                                                 update.object.event_id)
    #                 await self._sending_to_chat(update.object.peer_id, message_text, KEYBOARD_TYPE["default"])
    #         # Handling new user to group
    #         elif update["type"] == "group_join":
    #             exists_user: User = await self.app.store.games.get_user_by_vk_id(update.object.user_id)
    #             if not exists_user:
    #                 raw_users: [RawUser] = await self.app.store.vk_api.get_user_data([update.object.user_id])
    #                 list_user_model = self._cast_raw_user_to_usermodel(raw_users)
    #                 await self.app.store.games.add_users(list_user_model)
    #
    #         # Handling another events
    #         else:
    #             await self._sending_to_chat(update.object.peer_id, "", KEYBOARD_TYPE["default"])

    async def handle_updates_rabbit(self, response: DeliveredMessage):
        update: [Update] = await self._create_update_object(json.loads(response.body.decode())[0])
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
                cur_user = await self.app.store.games.get_user_by_vk_id(update.object.user_id)
                self.game: Game = await self.app.store.games.create_game()
                message_text = f"Участник {cur_user.first_name} {cur_user.last_name} запустил игру."
                await self._sending_to_callback(update.object.peer_id,
                                                update.object.user_id,
                                                message_text,
                                                update.object.event_id)
                await self._sending_to_chat(update.object.peer_id, message_text, KEYBOARD_TYPE["start"])
                # ЭТО САМАЯ СЛОЖНАЯ СТРОЧКА В МОЕЙ ЖИЗНИ!
                self.game_task = asyncio.create_task(self.start_game(self.game, update.object.peer_id))
                # await self.start_game(game, update.object.peer_id)
            elif update.type == EVENT_TYPE["event"] and update.object.message == "0":
                if self.game:
                    self.game_task.cancel()
                await self._end_game(self.game,
                                     update.object.peer_id,
                                     user_id=update.object.user_id,
                                     event_id=update.object.event_id)

            elif update.type == EVENT_TYPE["join"]:
                exists_user: User = await self.app.store.games.get_user_by_vk_id(update.object.user_id)
                if not exists_user:
                    raw_users: [RawUser] = await self.app.store.vk_api.get_user_data([update.object.user_id])
                    list_user_model = self._cast_raw_user_to_usermodel(raw_users)
                    await self.app.store.games.add_users(list_user_model)
            elif update.type == EVENT_TYPE["text"] and self.game:
                current_user: User = await self.app.store.games.get_user_by_vk_id(update.object.user_id)
                for a in self.current_question.answers:
                    if update.object.message.lower() not in self.current_user_answers:
                        if a.title.lower() == update.object.message.lower():
                            await self.app.store.games.save_user_answer(game_id=self.game.id,
                                                                        user_id=current_user.id,
                                                                        answer_id=a.id,
                                                                        answer_score=a.score,
                                                                        )
                            self.current_user_answers.append(update.object.message.lower())
                            message = f"Пользователь " \
                                      f"{current_user.first_name} {current_user.last_name} заработал {a.score} очков"
                            await self._sending_to_chat(update.object.peer_id, message, KEYBOARD_TYPE["start"])
                            break
                    else:
                        self.app.store.games.save_user_answer(game_id=self.game.id,
                                                              user_id=current_user.id,
                                                              answer_id=-1,
                                                              answer_score=0)
                        message = f"Пользователь " \
                                  f"{current_user.first_name} {current_user.last_name} ответил неправильно"
                        await self._sending_to_chat(update.object.peer_id, message, KEYBOARD_TYPE["start"])

                # await self.app.store.games.save_user_answer(cur_game=self.game,
                #                                             user_id=update.object.user_id,
                #                                             user_answer=update.object.message)
                print(f"Было написано {update.object.message}")

    async def start_game(self, game: Game, peer_id: int):
        for cur_round in game.road_map:
            if cur_round.status is False:
                message: str = "================================<br>Следующий вопрос через 5 секунд!<br>================================"
                await self._sending_to_chat(peer_id, message, KEYBOARD_TYPE["start"])
                await asyncio.sleep(5)
                self.current_question: Question = await self.app.store.games.get_question_by_id(cur_round.question_id)
                await self._sending_to_chat(peer_id, self.current_question.title, KEYBOARD_TYPE["start"])
                message: str = "У вас 20 секунд на ответ!"
                await self._sending_to_chat(peer_id, message, KEYBOARD_TYPE["start"])
                await asyncio.sleep(20)
                # await self.app.store.vk_api.round_begin(10)
                await self.app.store.games.close_roadmap_step(cur_round)
                message: str = "Время вышло."
                await self._sending_to_chat(peer_id, message, KEYBOARD_TYPE["start"])
                self.current_user_answers = []
        else:
            await self._end_game(game, peer_id)

    async def _end_game(self, game: Game, peer_id: int, user_id: int = None, event_id: str = None):
        await self.app.store.games.end_game(game)
        message: str = "Игра окончена."
        if user_id:
            cur_user = await self.app.store.games.get_user_by_vk_id(user_id)
            message: str = f"Участник {cur_user.first_name} {cur_user.last_name} закончил игру досрочно."
            await self._sending_to_callback(peer_id, user_id, message, event_id)
        await self._sending_to_chat(peer_id, message, KEYBOARD_TYPE["default"])
        statistics = await self.app.store.games.get_statistics(game_id=game.id)
        message: str = "Результаты игры"
        for st in statistics:
            message += f"<br>{st[0]} {st[1]} заработал {st[2]} баллов"
        await self._sending_to_chat(peer_id, message, KEYBOARD_TYPE["default"])
        self.game = None
        self.current_question = None
        self.current_user_answers = []

    async def _create_update_object(self, data: dict) -> Update:
        # Новое сообщение

        if data["type"] == "message_new":
            # print(data)
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
                # peer_id=update.object.peer_id,
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
                # event_id=update.object.event_id,
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

