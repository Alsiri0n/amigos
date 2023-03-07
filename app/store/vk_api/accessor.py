import json
import random
from typing import Optional, TYPE_CHECKING

import aio_pika
import aiormq
from aiohttp import TCPConnector
from aiohttp.client import ClientSession

from app.base.base_accessor import BaseAccessor
from app.rabbit.rabbit_accessor import RabbitAccessor
from app.store.vk_api.dataclasses import (Message,
                                          MessageEvent,
                                          Update,
                                          UpdateObjectMessageNew,
                                          UpdateObjectMessageEvent,
                                          UpdateObject,
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
                        "payload": "{\"game\": \"1\"}",
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
    "keyboard_game": {
        "buttons": [
            [
                {
                    "action": {
                        "type": "callback",
                        "payload": "{\"game\": \"0\"}",
                        "label": "Приехали"
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


class VkApiAccessor(RabbitAccessor):
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.session: Optional[ClientSession] = None
        self.key: Optional[str] = None
        self.server: Optional[str] = None
        self.poller: Optional[Poller] = None
        self.ts: Optional[int] = None
        self.rabbit_connection: Optional[aio_pika.Connection] = None
        self.rabbit_channel: Optional[aio_pika.Channel] = None
        # self.rabbit_queue: Optional[aiormq.spec.Queue] = None

    async def connect(self, app: "Application") -> None:
        self.session = ClientSession(connector=TCPConnector(verify_ssl=False))
        try:
            await self._get_long_poll_service()
        except Exception as e:
            self.logger.error("Exception", exc_info=e)
        self.poller = Poller(app.store)
        self.logger.info("start polling")
        await self.poller.start()
        self.rabbit_connection = self.app.rabbit.connection_producer
        self.rabbit_channel = await self.rabbit_connection.channel()
        # self.rabbit_queue = await self.rabbit_channel.queue_declare("amigos")

    async def disconnect(self, app: "Application") -> None:
        print("vk_api_accessor_disconnect_started")
        if self.poller:
            await self.poller.stop()
        if self.session:
            await self.session.close()

        await self.rabbit_channel.close()
        await self.rabbit_connection.close()
        print("vk_api_accessor_disconnect_ended")

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

    async def poll(self) -> Optional[Update]:
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
            # updates = []
            # for update in raw_updates:
            #     if update["type"] == EVENT_TYPE["text"]:
            #         updates.append(
            #             Update(
            #                 type=EVENT_TYPE["text"],
            #                 object=UpdateObjectMessageNew(
            #                     id_=update["object"]["message"]["id"],
            #                     user_id=update["object"]["message"]["from_id"],
            #                     peer_id=update["object"]["message"]["peer_id"],
            #                     text=update["object"]["message"]["text"]
            #                 )
            #             )
            #         )
            #     elif update["type"] == EVENT_TYPE["event"]:
            #         updates.append(
            #             Update(
            #                 type=EVENT_TYPE["event"],
            #                 object=UpdateObjectMessageEvent(
            #                     id_=update["event_id"],
            #                     user_id=update["object"]["user_id"],
            #                     peer_id=update["object"]["peer_id"],
            #                     event_id=update["object"]["event_id"],
            #                     payload=update["object"]["payload"]
            #                 )
            #             )
            #         )
            #     elif update["type"] == EVENT_TYPE["join"]:
            #         updates.append(
            #             Update(
            #                 type=EVENT_TYPE["join"],
            #                 object=UpdateObject(
            #                     id_=update["event_id"],
            #                     user_id=update["object"]["user_id"],
            #                     peer_id=None,
            #                 )
            #             )
            #         )
            return raw_updates
                # await self.app.store.bots_manager.handle_updates(updates)

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

    async def get_community_members(self, offset: int) -> list[RawUser] | None:
        async with self.session.get(
                self._build_query(
                    host=API_PATH,
                    method=METHODS["getMembers"],
                    params={
                        "access_token": self.app.config.bot.token,
                        "group_id": self.app.config.bot.group_id,
                        "sort": "time_desc",
                        "offset": offset,
                        "fields": list,
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

    async def send_to_rabbit(self, message: Update):
        # async with self.rabbit_connection:

        await self.rabbit_channel.default_exchange.publish(
            aio_pika.Message(body=bytes(json.dumps(message), "utf-8")), routing_key=self.app.config.rabbit.queue
            )
