import json
import typing
from logging import getLogger
from typing import Optional
from app.store.vk_api.dataclasses import Message, Update, MessageEvent
from app.game.models import Question

if typing.TYPE_CHECKING:
    from app.web.app import Application

KEYBOARD_TYPE = {
    "default": "keyboard_default",
    "start": "keyboard_game",
}
METHODS = {
    "text": "messages.send",
    "callback": "messages.sendMessageEventAnswer",
}


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.bot = None
        self.logger = getLogger("handler")
        self.start_command = f"[club{self.app.config.bot.group_id}|@club{self.app.config.bot.group_id}] "

    async def handle_updates(self, updates: list[Update]):
        message_text = "Hello"
        for update in updates:
            # Text new_message
            # Логику перенести в коллбэки нельзя, потому что коллбэк отвечает только одному пользователю
            # Но есть идея, администратор может запустить игру и дублировать сообщение в общий чат
            # TODO перенести логику в коллбэки, здесь обрабатывать только входящие сообщения от пользователя
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
            # Если коллбэк
            elif update.type == "message_event":
                if update.object.payload == {"game": "rules"}:
                    message_text = "Первое правило бойцовского клуба."
                    await self._sending_to_chat_event(update, message_text)
                elif update.object.payload == {"game": "1"}:
                    message_text = "Вы запустили игру"
                    await self._sending_to_chat_event(update, message_text)
                    await self._sending_to_chat(update, message_text, KEYBOARD_TYPE["start"])
                elif update.object.payload == {"game": "0"}:
                    message_text = "Игра окончена"
                    await self._sending_to_chat_event(update, message_text)
                    await self._sending_to_chat(update, message_text, KEYBOARD_TYPE["default"])
            # Пользователь добавился в группу
            # TODO добавить пользователя в базу
            elif update.type == "group_join":
                pass
            # Другие события в сообществе
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
                method="messages.send",
            )
        )

    async def _sending_to_chat_event(self,
                                     update: Update,
                                     message: str,
                                     ):
        await self.app.store.vk_api.send_event(
            MessageEvent(
                peer_id=update.object.peer_id,
                user_id=update.object.user_id,
                message=message,
                event_id=update.object.event_id,
                method=METHODS["callback"]
            )
        )
