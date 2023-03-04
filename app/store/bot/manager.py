import asyncio
import typing
from logging import getLogger
from typing import Optional
from app.store.vk_api.dataclasses import Message, Update, MessageEvent, RawUser
from app.game.models import Question, UserModel, User, Game


if typing.TYPE_CHECKING:
    from app.web.app import Application

KEYBOARD_TYPE = {
    "default": "keyboard_default",
    "start": "keyboard_game",
}


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.bot = None
        self.logger = getLogger("handler")
        self.start_command = f"[club{self.app.config.bot.group_id}|@club{self.app.config.bot.group_id}] "
        app.on_startup.append(self.connect)

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

    async def handle_updates(self, updates: list[Update]):
        message_text = "Hello"
        for update in updates:
            # Handling new message
            if update["type"] == "message_new":
                print(f"написано было {update['object']['message']['text']}")
                # if update.object_message_new.text == self.start_command + "/Правила":
                #     message_text = "Правила игры"
                #     await self._sending_to_chat(update, message_text, KEYBOARD_TYPE["default"])
                # if update.object.text == self.start_command + "/поехали":
                #     message_text = "Игра началась"
                #     await self._sending_to_chat(update, message_text, KEYBOARD_TYPE["start"])
                # if update.object.text == self.start_command + "/приехали":
                #     message_text = "Игра завершилась"
                #     await self._sending_to_chat(update, message_text, KEYBOARD_TYPE["default"])

            # Handling callback buttons
            elif update["type"] == "message_event":
                if update.object.payload == {"game": "rules"}:
                    message_text = "Первое правило бойцовского клуба."
                    await self._sending_to_callback(update.object.peer_id,
                                                    update.object.user_id,
                                                    message_text,
                                                    update.object.event_id)
                elif update.object.payload == {"game": "1"}:
                    cur_user = await self.app.store.games.get_user_by_vk_id(update.object.user_id)
                    game: Game = await self.app.store.games.create_game()
                    message_text = f"Участник {cur_user.first_name} {cur_user.last_name} запустил игру."
                    await self._sending_to_callback(update.object.peer_id,
                                                    update.object.user_id,
                                                    message_text,
                                                    update.object.event_id)
                    await self._sending_to_chat(update.object.peer_id, message_text, KEYBOARD_TYPE["start"])
                    # await self.start_game(game, update.object.peer_id)
                    # await
                elif update.object.payload == {"game": "0"}:
                    cur_user = await self.app.store.games.get_user_by_vk_id(update.object.user_id)
                    await self.app.store.games.end_game()
                    message_text = f"Участник {cur_user.first_name} {cur_user.last_name} закончил игру."
                    await self._sending_to_callback(update.object.peer_id,
                                                    update.object.user_id,
                                                    message_text,
                                                    update.object.event_id)
                    await self._sending_to_chat(update.object.peer_id, message_text, KEYBOARD_TYPE["default"])
            # Handling new user to group
            elif update["type"] == "group_join":
                exists_user: User = await self.app.store.games.get_user_by_vk_id(update.object.user_id)
                if not exists_user:
                    raw_users: [RawUser] = await self.app.store.vk_api.get_user_data([update.object.user_id])
                    list_user_model = self._cast_raw_user_to_usermodel(raw_users)
                    await self.app.store.games.add_users(list_user_model)

            # Handling another events
            else:
                await self._sending_to_chat(update.object.peer_id, "", KEYBOARD_TYPE["default"])


    async def handle_updates_rabbit(self, updates: list[Update]):
        print(updates)

    async def start_game(self, game: Game, peer_id: int):
        # print(game)
        for cur_round in game.road_map:
        # cur_round = game.road_map[0]
            if cur_round.status is False:
                message: str = "================================<br>Следующий вопрос через 5 секунд!<br>================================"
                await self._sending_to_chat(peer_id, message, KEYBOARD_TYPE["start"])
                await asyncio.sleep(5)
                question: Question = await self.app.store.games.get_question_by_id(cur_round.question_id)
                await self._sending_to_chat(peer_id, question.title, KEYBOARD_TYPE["start"])
                message: str = "У вас 20 секунд на ответ!"
                await self._sending_to_chat(peer_id, message, KEYBOARD_TYPE["start"])
                await self.app.store.vk_api.round_begin(10)
                await self.app.store.games.close_roadmap_step(cur_round)
                message: str = "Время вышло."
                await self._sending_to_chat(peer_id, message, KEYBOARD_TYPE["start"])
        else:
            await self.app.store.games.end_game(game)
            message: str = "Игра окончена."
            await self._sending_to_chat(peer_id, message, KEYBOARD_TYPE["default"])

    async def _sending_to_chat(self,
                               # update: Update,
                               peer_id: int,
                               message: str,
                               keyboard_type: str,
                               ):
        await self.app.store.vk_api.send_message(
            Message(
                # user_id=update.object.user_id,
                text=message,
                # peer_id=update.object.peer_id,
                peer_id=peer_id,
                keyboard_type=keyboard_type,
            )
        )

    async def _sending_to_callback(self,
                                   # update: Update,
                                   peer_id: int,
                                   user_id: int,
                                   message: str,
                                   event_id: str
                                   ):
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
