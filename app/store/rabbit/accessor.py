import asyncio

import aio_pika
import json

from logging import getLogger
from typing import TYPE_CHECKING, Optional
from yarl import URL

from app.base.base_accessor import BaseAccessor
from app.store.vk_api.dataclasses import Update

if TYPE_CHECKING:
    from app.web.app import Application


class RabbitAccessor(BaseAccessor):
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.logger = getLogger("rabbit_accessor")
        self.rabbit_connection: Optional[aio_pika.Connection] = None
        self.rabbit_channel: Optional[aio_pika.Channel] = None
        self.rabbit_queue: Optional[aio_pika.Queue] = None

    async def connect(self, app: "Application"):
        rabbit_url = URL.build(
            scheme="amqp",
            user=self.app.config.rabbit.user,
            password=self.app.config.rabbit.password,
            host=self.app.config.rabbit.host,
            port=self.app.config.rabbit.port,
            path=self.app.config.rabbit.vhost,
        )
        self.rabbit_connection = await aio_pika.connect_robust(rabbit_url)
        self.rabbit_channel = await self.rabbit_connection.channel()
        self.rabbit_queue: aio_pika.abc.AbstractQueue = await self.rabbit_channel.declare_queue(self.app.config.rabbit.queue)
        await self.rabbit_queue.consume(self.on_message, no_ack=True)

    async def on_message(self, message):
        if message:
            await self.app.store.bots_manager.handle_updates(json.loads(message.body.decode())[0])

    async def disconnect(self, app: "Application"):
        await self.rabbit_channel.close()
        await self.rabbit_connection.close()

    async def rabbit_produce(self, updates: list[Update]):
        await self.rabbit_channel.default_exchange.publish(
            aio_pika.Message(body=bytes(json.dumps(updates), "utf-8")), routing_key=self.app.config.rabbit.queue
        )
