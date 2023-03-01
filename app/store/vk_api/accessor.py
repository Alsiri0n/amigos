import typing
import json
import random
from typing import Optional

from aiohttp import TCPConnector
from aiohttp.client import ClientSession

from app.base.base_accessor import BaseAccessor
from app.store.vk_api.dataclasses import (Message,
                                          UpdateObject,
                                          MessageEvent,
                                          Update,
                                          UpdateObjectMessageNew,
                                          UpdateObjectMessageEvent,
                                          )
from app.store.vk_api.poller import Poller

if typing.TYPE_CHECKING:
    from app.web.app import Application

API_PATH = "https://api.vk.com/method/"

KEYBOARD = {
    "keyboard_default": {
        "buttons": [
            [
                {
                    "action": {
                        "type": "text",
                        "payload": "",
                        "label": "/поехали"
                    },
                }
            ],
            [
                {
                    "action": {
                        "type": "callback",
                        "payload": "",
                        "label": "/Правила"
                    },
                }
            ]
        ]
    },
    "keyboard_game": {
        "buttons": [
            [
                {
                    "action": {
                        "type": "text",
                        "payload": "",
                        "label": "/приехали"
                    },
                }
            ],
            [
                {
                    "action": {
                        "type": "callback",
                        "payload": "",
                        "label": "/Правила"
                    },
                }
            ]
        ]
    },
}
MESSAGES_TYPE = {
    "text": "message_new",
    "event": "message_event"
}


class VkApiAccessor(BaseAccessor):
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.session: Optional[ClientSession] = None
        self.key: Optional[str] = None
        self.server: Optional[str] = None
        self.poller: Optional[Poller] = None
        self.ts: Optional[int] = None

    async def connect(self, app: "Application") -> None:
        self.session = ClientSession(connector=TCPConnector(verify_ssl=False))
        try:
            await self._get_long_poll_service()
        except Exception as e:
            self.logger.error("Exception", exc_info=e)
        self.poller = Poller(app.store)
        self.logger.info("start polling")
        await self.poller.start()

    async def disconnect(self, app: "Application") -> None:
        if self.session:
            await self.session.close()
        if self.poller:
            await self.poller.stop()

    @staticmethod
    def _build_query(host: str, method: str, params: dict) -> str:
        url = host + method + "?"
        if "v" not in params:
            params["v"] = "5.131"
        url += "&".join([f"{k}={v}" for k, v in params.items()])
        return url

    async def _get_long_poll_service(self) -> None:
        async with self.session.get(
                self._build_query(
                    host=API_PATH,
                    method="groups.getLongPollServer",
                    params={
                        "group_id": self.app.config.bot.group_id,
                        "access_token": self.app.config.bot.token,
                    },
                )
        ) as resp:
            data = (await resp.json())["response"]
            self.logger.info(data)
            self.key = data["key"]
            self.server = data["server"]
            self.ts = data["ts"]
            self.logger.info(self.server)

    async def poll(self) -> None:
        async with self.session.get(
                self._build_query(
                    host=self.server,
                    method="",
                    params={
                        "act": "a_check",
                        "key": self.key,
                        "ts": self.ts,
                        "wait": 25,
                    },
                )
        ) as resp:
            data = await resp.json()
            self.logger.info(data)
            self.ts = data["ts"]
            raw_updates = data.get("updates", [])
            updates = []
            for update in raw_updates:
                if update["type"] == MESSAGES_TYPE["text"]:
                    updates.append(
                        Update(
                            type=MESSAGES_TYPE["text"],
                            object_message_new=UpdateObjectMessageNew(
                                id=update["object"]["message"]["id"],
                                user_id=update["object"]["message"]["from_id"],
                                peer_id=int(update["object"]["message"]["peer_id"]),
                                text=update["object"]["message"]["text"],
                            ),
                            object_message_event=None
                        )
                    )

                elif update["type"] == MESSAGES_TYPE["event"]:
                    updates.append(
                        Update(
                            type=MESSAGES_TYPE["event"],
                            object_message_event=UpdateObjectMessageEvent(
                                id=update["event_id"],
                                user_id=update["object"]["user_id"],
                                peer_id=int(update["object"]["peer_id"]),
                                event_id=update["object"]["event_id"],
                                payload=update["object"]["payload"],
                            ),
                            object_message_new=None
                        )
                    )
                await self.app.store.bots_manager.handle_updates(updates)

    async def send_message(self, message: Message) -> None:
        async with self.session.get(
                self._build_query(
                    host=API_PATH,
                    method=message.method,
                    params={
                        # "user_id": message.user_id,
                        "random_id": random.randint(1,  2 ** 32),
                        "peer_id": message.peer_id,
                        "message": message.text,
                        "access_token": self.app.config.bot.token,
                        "keyboard": json.dumps(KEYBOARD[message.keyboard_type])
                    },
                )
        ) as resp:
            data = await resp.json()
            self.logger.info(data)

    async def send_event(self, message_event: MessageEvent) -> None:
        async with self.session.get(
                self._build_query(
                    host=API_PATH,
                    method=message_event.method,
                    # event_id=message_event.event_id,
                    params={
                        # "user_id": message.user_id,
                        "access_token": self.app.config.bot.token,
                        "event_id": message_event.event_id,
                        "user_id": message_event.user_id,
                        #"random_id": random.randint(1,  2 ** 32),
                        "peer_id": message_event.peer_id,
                        "event_data": json.dumps({
                            "type": "show_snackbar",
                            "text": message_event.message
                        }),

                        #"keyboard": json.dumps(KEYBOARD[message_event.keyboard_type])
                    },
                )
        ) as resp:
            data = await resp.json()
            self.logger.info(data)
