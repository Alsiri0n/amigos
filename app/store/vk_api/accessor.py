import json
import random
from typing import Optional, TYPE_CHECKING

from aiohttp import TCPConnector
from aiohttp.client import ClientSession
from logging import getLogger

from app.base.base_accessor import BaseAccessor
from app.store.vk_api.dataclasses import (Message,
                                          MessageEvent,
                                          Update,
                                          RawUser,
                                          )
from app.store.vk_api.poller import Poller

if TYPE_CHECKING:
    from app.web.app import Application

API_PATH = "https://api.vk.com/method/"

KEYBOARD = {
    "keyboard_default": {
        "buttons": [
            [
                {
                    "action": {
                        "type": "callback",
                        "payload": "{\"game\": \"start\"}",
                        "label": "Поехали"
                    },
                    "color": "positive"
                }
            ],
            [
                {
                    "action": {
                        "type": "callback",
                        "payload": "{\"game\": \"rules\"}",
                        "label": "Правила"
                    },
                    "color": "secondary"
                }
            ]
        ]
    },
    "keyboard_in_game": {
        "buttons": [
            [
                {
                    "action": {
                        "type": "callback",
                        "payload": "{\"game\": \"end\"}",
                        "label": "Закончить игру"
                    },
                    "color": "negative"
                }
            ],
            [
                {
                    "action": {
                        "type": "callback",
                        "payload": "{\"game\": \"rules\"}",
                        "label": "Правила"
                    },
                    "color": "secondary"
                }
            ]
        ]
    },
}
# EVENT_TYPE = {
#     "text": "message_new",
#     "event": "message_event",
#     "join": "group_join",
# }
METHODS = {
    "text": "messages.send",
    "callback": "messages.sendMessageEventAnswer",
    "getMembers": "groups.getMembers",
    "userdata": "users.get"
}


class VkApiAccessor(BaseAccessor):
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.session: Optional[ClientSession] = None
        self.key: Optional[str] = None
        self.server: Optional[str] = None
        self.poller: Optional[Poller] = None
        self.ts: Optional[int] = None
        self.logger = getLogger("VKAPI_accessor")

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
        if self.poller:
            await self.poller.stop()
        if self.session:
            await self.session.close()

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

    async def poll(self):
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
            if raw_updates:
                await self.app.store.rabbit.rabbit_produce(raw_updates)

    # Отвечаем в чат
    async def send_message(self, message: Message) -> None:
        async with self.session.get(
                self._build_query(
                    host=API_PATH,
                    method=METHODS["text"],
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

    # Отвечаем на event
    async def send_event(self, message_event: MessageEvent) -> None:
        async with self.session.get(
                self._build_query(
                    host=API_PATH,
                    method=METHODS["callback"],
                    params={
                        # "user_id": message.user_id,
                        "access_token": self.app.config.bot.token,
                        "event_id": message_event.event_id,
                        "user_id": message_event.user_id,
                        "peer_id": message_event.peer_id,
                        "event_data": json.dumps({
                            "type": "show_snackbar",
                            "text": message_event.message
                        }),
                    },
                )
        ) as resp:
            data = await resp.json()
            self.logger.info(data)

    # Получаем список id участников сообщества
    async def get_community_members(self) -> list[RawUser] | None:
        async with self.session.get(
                self._build_query(
                    host=API_PATH,
                    method=METHODS["getMembers"],
                    params={
                        "access_token": self.app.config.bot.token,
                        "group_id": self.app.config.bot.group_id,
                        "sort": "time_desc",
                        "fields": "lists",
                    },
                )
        ) as resp:
            data = await resp.json()
            self.logger.info(data)
            if data["response"]["items"]:
                raw_users: [RawUser] = []
                for el in data["response"]["items"]:
                    raw_users.append(RawUser(
                        id_=el["id"],
                        first_name=el["first_name"],
                        last_name=el["last_name"]
                    ))
                return raw_users
            return None

    # Получаем имя и фамилию из вк по id
    async def get_user_data(self, list_ids: [int]) -> list[RawUser] | None:
        async with self.session.get(
                self._build_query(
                    host=API_PATH,
                    method=METHODS["userdata"],
                    params={
                        "access_token": self.app.config.bot.token,
                        "user_ids": ",".join(map(str, list_ids)),
                        "fields": "first_name, last_name",
                    },
                )
        ) as resp:
            data = await resp.json()
            self.logger.info(data)
            if data["response"]:
                raw_users: [RawUser] = []
                for el in data["response"]:
                    raw_users.append(RawUser(
                        id_=el["id"],
                        first_name=el["first_name"],
                        last_name=el["last_name"]
                    ))
                return raw_users
            return None
