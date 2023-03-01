import typing
from logging import getLogger
from typing import Optional
from app.store.vk_api.dataclasses import Message, Update, MessageEvent, RawUser
from app.game.models import Question, UserModel, User


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

    #При запуске бота заполняем бд пользователями из сообщества
    async def connect(self, app: "Application"):
        # Получаем количество пользователей в базе
        cnt = await self.app.store.games.get_users_count_in_db()
        # Получаем список пользователей из вк
        raw_users: [RawUser] = await self.app.store.vk_api.get_community_members(cnt)
        # Заносим пользователей в базу
        if raw_users:
            await self.app.store.games.add_users(raw_users)

    async def handle_updates(self, updates: list[Update]):
        message_text = "Hello"
        for update in updates:
            # Handling new message
            if update.type == "message_new":
                pass
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
            elif update.type == "message_event":
                if update.object.payload == {"game": "rules"}:
                    message_text = "Первое правило бойцовского клуба."
                    await self._sending_to_callback(update, message_text)
                elif update.object.payload == {"game": "1"}:
                    cur_user = await self.app.store.games.get_user_by_vk_id(update.object.user_id)
                    await self.app.store.games.create_game()
                    message_text = f"Участник {cur_user.first_name} {cur_user.last_name} запустил игру."
                    await self._sending_to_callback(update, message_text)
                    await self._sending_to_chat(update, message_text, KEYBOARD_TYPE["start"])
                elif update.object.payload == {"game": "0"}:
                    cur_user = await self.app.store.games.get_user_by_vk_id(update.object.user_id)
                    await self.app.store.games.end_game()
                    message_text = f"Участник {cur_user.first_name} {cur_user.last_name} закончил игру."
                    await self._sending_to_callback(update, message_text)
                    await self._sending_to_chat(update, message_text, KEYBOARD_TYPE["default"])
            # Handling new user to group
            elif update.type == "group_join":
                exists_user: User = await self.app.store.games.get_user_by_vk_id(update.object.user_id)
                if not exists_user:
                    raw_users: [RawUser] = await self.app.store.vk_api.get_user_data([update.object.user_id])
                    list_user_model: [UserModel] = []
                    for user in raw_users:
                        list_user_model.append(
                            UserModel(
                                vk_id=user.id_,
                                first_name=user.first_name,
                                last_name=user.last_name
                            )
                        )
                    await self.app.store.games.add_users(list_user_model)

            # Handling another events
            else:
                await self._sending_to_chat(update, "", KEYBOARD_TYPE["default"])
            # elif 3 < cur_status.id < 8 and update.object.text == "Ответить":
            #     message_text = "Напишите ваш ответ"
            #     await self._sending(update, None, message_text, KEYBOARD["keyboard_in_game"])
            # elif update.object.text == "Завершить игру" and 0 < cur_status.id < 8:
            #     game_result: [GameResult] = await self.app.store.games.end_game(game_id=cur_status.game_result.game_id)
            #     message_text = "Игра окончена. Ваш счёт: "
            #     await self._sending(update, game_result, message_text, KEYBOARD["keyboard_default"], add_message="game.result")
            # elif 3 < cur_status.id < 8:
            #     message_text = "Ваш ответ принят"
            #     await self._sending(update, None, message_text, KEYBOARD["keyboard_in_game"])
            # elif update.object.text == "Начать игру":
            #     await self.app.store.games.set_status(cur_status.game_result.game_id, 4)
            #     question: Question = await self.app.store.games.get_question(cur_status.game_result.game_id)
            #     message_text = 'Если вы знаете лучший вариант ответа.<br>Нажимайте кнопку "Ответить"<br><br><br>' + \
            #         f"ВОПРОС!<br> {question.title}"
            #     game_result: [GameResult] = await self.app.store.games.end_game(game_id=cur_status.game_result.game_id)
            #     await self._sending(update, game_result, message_text, KEYBOARD["keyboard_create"])
            # elif update.object.text == "Создать игру":
            #     await self.app.store.games.create_game(update.object.user_id)
            #     message_text = f"Вы создали игру.<br>Список участников: {update.object.user_id}"
            #     await self._sending(update, None, message_text, KEYBOARD["keyboard_create"])
            # elif update.object.text == "Присоединиться":
            #     message_text = """Вы присоединились к игре"""
            #     await self._sending(update, None, message_text, KEYBOARD["keyboard_waiting"])
            # elif cur_status is None:
            #     message_text = "Попробуйте создать игру"
            #     await self._sending(update, None, message_text, KEYBOARD["keyboard_default"])
            # elif cur_status.id == 3:
            #     message_text = "Вы ожидаете других игроков"
            #     await self._sending(update, None, message_text, KEYBOARD["keyboard_create"])

    async def _sending_to_chat(self,
                               update: Update,
                               message: str,
                               keyboard_type: str,
                               ):
        await self.app.store.vk_api.send_message(
            Message(
                # user_id=update.object.user_id,
                text=message,
                peer_id=update.object.peer_id,
                keyboard_type=keyboard_type,
            )
        )

    async def _sending_to_callback(self,
                                   update: Update,
                                   message: str,
                                   ):
        await self.app.store.vk_api.send_event(
            MessageEvent(
                peer_id=update.object.peer_id,
                user_id=update.object.user_id,
                message=message,
                event_id=update.object.event_id,
            )
        )
