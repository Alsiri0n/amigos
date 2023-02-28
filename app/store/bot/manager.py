import json
import typing
from logging import getLogger
from typing import Optional
from app.store.vk_api.dataclasses import Message, Update
from app.game.models import Question

if typing.TYPE_CHECKING:
    from app.web.app import Application

KEYBOARD = {
    "keyboard_default": {
        "buttons": [
            [
                {
                    "action": {
                        "type": "text",
                        "payload": "",
                        "label": "Создать игру"
                    },
                }
            ],
            [
                {
                    "action": {
                        "type": "text",
                        "payload": "",
                        "label": "Присоединиться"
                    },
                }
            ],
            [
                {
                    "action": {
                        "type": "text",
                        "payload": "",
                        "label": "Правила"
                    },
                }
            ]
        ]
    },
    "keyboard_create": {
        "buttons": [
            [
                {
                    "action": {
                        "type": "text",
                        "payload": "",
                        "label": "Начать игру"
                    },
                }
            ],
            [
                {
                    "action": {
                        "type": "text",
                        "payload": "",
                        "label": "Список участников"
                    },
                }
            ],
            [
                {
                    "action": {
                        "type": "text",
                        "payload": "",
                        "label": "Завершить игру"
                    },
                }
            ]
        ]
    },
    "keyboard_waiting": {
        "buttons": [
            [
                {
                    "action": {
                        "type": "text",
                        "payload": "",
                        "label": "Выбрать комнату"
                    },
                }
            ],
            [
                {
                    "action": {
                        "type": "text",
                        "payload": "",
                        "label": "Назад"
                    },
                }
            ],
            [
                {
                    "action": {
                        "type": "text",
                        "payload": "",
                        "label": "Правила"
                    },
                }
            ]
        ]
    },
    "keyboard_in_game": {
        "buttons": [
            [
                {
                    "action": {
                        "type": "text",
                        "payload": "",
                        "label": "Ответить"
                    },
                }
            ],
            [
                {
                    "action": {
                        "type": "text",
                        "payload": "",
                        "label": "Завершить игру"
                    },
                }
            ],
            [
                {
                    "action": {
                        "type": "text",
                        "payload": "",
                        "label": "Правила"
                    },
                }
            ]
        ]
    },
}


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.bot = None
        self.logger = getLogger("handler")

    async def handle_updates(self, updates: list[Update]):
        message_text = "Hello"

        kbd = KEYBOARD["keyboard_default"]
        for update in updates:
            cur_status: Optional[GameStatus] = await self.app.store.games.get_last_status(update.object.user_id)
            if update.object.text == "Правила":
                message_text = "Правила игры"
                await self._sending(update, None, message_text, KEYBOARD["keyboard_default"])
            elif 3 < cur_status.id < 8 and update.object.text == "Ответить":
                message_text = "Напишите ваш ответ"
                await self._sending(update, None, message_text, KEYBOARD["keyboard_in_game"])
            elif update.object.text == "Завершить игру" and 0 < cur_status.id < 8:
                game_result: [GameResult] = await self.app.store.games.end_game(game_id=cur_status.game_result.game_id)
                message_text = "Игра окончена. Ваш счёт: "
                await self._sending(update, game_result, message_text, KEYBOARD["keyboard_default"], add_message="game.result")
            elif 3 < cur_status.id < 8:
                message_text = "Ваш ответ принят"
                await self._sending(update, None, message_text, KEYBOARD["keyboard_in_game"])
            elif update.object.text == "Начать игру":
                await self.app.store.games.set_status(cur_status.game_result.game_id, 4)
                question: Question = await self.app.store.games.get_question(cur_status.game_result.game_id)
                message_text = 'Если вы знаете лучший вариант ответа.<br>Нажимайте кнопку "Ответить"<br><br><br>' + \
                    f"ВОПРОС!<br> {question.title}"
                game_result: [GameResult] = await self.app.store.games.end_game(game_id=cur_status.game_result.game_id)
                await self._sending(update, game_result, message_text, KEYBOARD["keyboard_create"])
            elif update.object.text == "Создать игру":
                await self.app.store.games.create_game(update.object.user_id)
                message_text = f"Вы создали игру.<br>Список участников: {update.object.user_id}"
                await self._sending(update, None, message_text, KEYBOARD["keyboard_create"])
            elif update.object.text == "Присоединиться":
                message_text = """Вы присоединились к игре"""
                await self._sending(update, None, message_text, KEYBOARD["keyboard_waiting"])
            elif cur_status is None:
                message_text = "Попробуйте создать игру"
                await self._sending(update, None, message_text, KEYBOARD["keyboard_default"])
            elif cur_status.id == 3:
                message_text = "Вы ожидаете других игроков"
                await self._sending(update, None, message_text, KEYBOARD["keyboard_create"])

    async def _sending(self,
                       update: Update,
                       # game_result: [GameResult],
                       message: str,
                       kbd: KEYBOARD,
                       add_message=None):
        # if game_result:
        #     full_message = message
        #     for game in game_result:
        #         if add_message == "game.result":
        #             full_message = message + f"{game.result}"
        #         await self.app.store.vk_api.send_message(
        #             Message(
        #                 user_id=game.user_id,
        #                 text=full_message,
        #                 keyboard=json.dumps(kbd),
        #                 # chat_id=update.object.chat_id
        #             )
        #         )
        # else:
        await self.app.store.vk_api.send_message(
            Message(
                # user_id=update.object.user_id,
                text=message,
                keyboard=json.dumps(kbd),
                peer_id=update.object.peer_id
                # chat_id=update.object.chat_id
            )
        )