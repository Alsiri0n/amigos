import asyncio
import json
from typing import TYPE_CHECKING, Optional

import aio_pika
#import aiormq
#from aiormq.abc import DeliveredMessage

from app.rabbit.rabbit_accessor import RabbitAccessor
from app.store.bot.dataclasses import Update
from app.store.bot.poller import Poller

if TYPE_CHECKING:
    from app.web.app import Application


class QueueAccessor(RabbitAccessor):
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.rabbit_queue: Optional[aio_pika.Queue] = None
        self.poller: Poller = None
        self.consumer_tag: str = None

    async def connect(self, app: "Application") -> None:
        self.poller = Poller(app.store)
        self.logger.info("Start rabbitMQ")
        self.connection = self.app.rabbit.connection_consumer
        self.channel: aio_pika.abc.AbstractChannel = await self.connection.channel()
        self.rabbit_queue: aio_pika.abc.AbstractQueue = await self.channel.declare_queue(self.app.config.rabbit.queue)
        self.consumer_tag = await self.rabbit_queue.consume(self.on_message, no_ack=True)

        # await self.poller.start()

    async def disconnect(self, app: "Application") -> None:
        print("app_store_bot_accessor(RABBIT_CONSUMER)_disconnect_started")
        if self.poller:
            await self.poller.stop()
        print("app_store_bot_accessor(RABBIT_CONSUMER)_disconnect_poller_stopped")
        await self.rabbit_queue.cancel(self.consumer_tag)
        await self.channel.close()
        await self.connection.close()

    # Если использовать коллбэк
    async def on_message(self, message):
        if message:
            await self.app.store.bots_manager.handle_updates_rabbit(json.loads(message.body.decode())[0])

    #TODO попробовать сделать поллер через basic_get а не basic_consume. Мне кажется через callback быстрее
    async def poll(self) -> Optional[aio_pika.IncomingMessage]:
        pass
            # raw_updates = await self.channel.basic_get(self.rabbit_queue.queue)
        #
        # if raw_updates.body:
        #     await self.channel.basic_ack(raw_updates.delivery_tag)
        #     return raw_updates
